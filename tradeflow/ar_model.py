from __future__ import annotations

from typing import Literal, Optional

import numpy as np
from statsmodels.regression import yule_walker
from statsmodels.regression.linear_model import burg
from statsmodels.tools.typing import ArrayLike1D
from statsmodels.tsa.ar_model import AutoReg
from statsmodels.tsa.tsatools import lagmat

from tradeflow.common import logger_utils
from tradeflow.common.ctypes_utils import CArray, CArrayEmpty
from tradeflow.common.general_utils import check_condition, check_enum_value_is_valid, get_enum_values, \
    is_value_within_interval_exclusive
from tradeflow.common.shared_libraries_registry import SharedLibrariesRegistry
from tradeflow.config import LIB_TRADEFLOW
from tradeflow.constants import OrderSelectionMethodAR, FitMethodAR
from tradeflow.exceptions import IllegalValueException, ModelNotFittedException, IllegalNbLagsException, \
    NonStationaryTimeSeriesException, AutocorrelatedResidualsException
from tradeflow.time_series import TimeSeries

logger = logger_utils.get_logger(__name__)


class AR(TimeSeries):
    """
    Autoregressive model for trade/order signs.

    Parameters
    ----------
    signs : array_like
        An array of signs where each element is either 1 (representing a buy) or -1 (representing a sell).
    max_order : int, default None
        The maximum order of the autoregressive model.
        If None, the maximum order is set to 12*(nobs/100)^{1/4} as outlined in Schwert (1989).
    order_selection_method : {'pacf'}, default None
        The method for selecting the order of the model. If None, the order of the model will be `max_order`.

        * 'pacf' - Choose the model using the number of significant lags in the partial autocorrelation function of the time series of signs.
    """

    def __init__(self, signs: ArrayLike1D, max_order: Optional[int] = None,
                 order_selection_method: Optional[Literal["pacf"]] = None) -> None:
        super().__init__(signs=signs)
        self._max_order = self._init_max_order(max_order=max_order)
        self._order_selection_method = check_enum_value_is_valid(enum_obj=OrderSelectionMethodAR,
                                                                 value=order_selection_method,
                                                                 parameter_name="order_selection_method",
                                                                 is_none_valid=True)

        # Will be set during fit()
        self._constant_parameter = 0.0
        self._parameters = None

    def resid(self, seed: Optional[int] = None) -> np.ndarray:
        """
        Estimate and return the residuals of the model.

        Residuals are calculated as the difference between the observed values and the
        values predicted by the model using the fitted parameters.

        Parameters
        ----------
        seed : int, default None
            Seed used to initialize the pseudo-random number generator.
            If `seed` is `None`, then a random seed between 0 and 2^32 - 1 is used.

        Returns
        -------
        np.ndarray
            The residuals of the AR model.

        Raises
        ------
        ModelNotFittedException
            If the model's parameters are not set. This occurs if the model
            has not been fitted by calling `fit()`.

        """
        check_condition(condition=self._parameters is not None, exception=ModelNotFittedException("The model does not have its parameters set. Fit the model first by calling 'fit()'."))

        if seed is None:
            seed = np.random.randint(0, np.iinfo(np.int32).max)
        np.random.seed(seed)

        def predict_sign_from_expected_value(expected_value: float, uniform: float) -> int:
            buy_proba = 0.5 * (1 + expected_value)
            next_sign = 1 if uniform <= buy_proba else -1
            return next_sign

        x, y = lagmat(x=self._signs, maxlag=len(self._parameters), trim="both", original="sep", use_pandas=False)
        x_with_cst = np.c_[np.ones(shape=x.shape[0]), x]

        expected_values_pred = x_with_cst @ np.append(self._constant_parameter, self._parameters)
        uniforms = np.random.uniform(low=0, high=1, size=len(expected_values_pred))
        signs_pred = np.vectorize(predict_sign_from_expected_value)(expected_values_pred, uniforms)

        resid = y.squeeze() - signs_pred
        return resid

    def _init_max_order(self, max_order: Optional[int]) -> int:
        if max_order is None:
            # Schwert (1989)
            max_order = int(np.ceil(12.0 * np.power(len(self._signs) / 100.0, 1 / 4.0)))

        check_condition(condition=1 <= max_order < len(self._signs) // 2,
                        exception=IllegalNbLagsException(f"{max_order} is not valid for 'max_order', it must be positive and lower than 50% of the time series length (< {len(self._signs) // 2})."))
        logger.info(f"The maximum order has been set to {max_order}.")
        return max_order

    def fit(self, method: Literal["yule_walker", "burg", "ols_with_cst"], significance_level: float = 0.05, check_residuals: bool = True) -> AR:
        """
        Estimate the model parameters.

        Parameters
        ----------
        method : {'yule_walker', 'ols_with_cst'}
            The method to use for estimating parameters.

            * 'yule_walker' - Use the Yule Walker equations to estimate model parameters.
              There will be no constant term, thus the percentage of buy signs
              in the time series generated with these parameters will be close to 50%.

            * 'burg' - Use Burg's method to estimate model parameters.
              There will be no constant term, thus the percentage of buy signs
              in the time series generated with these parameters will be close to 50%.

            * 'ols_with_cst' - Use OLS to estimate model parameters.
              There will be a constant term, thus the percentage of buy signs in the time series
              generated with these parameters will be close to the one from the training time series.
        significance_level : float, default 0.05
            The significance level for stationarity and residual autocorrelation (if `check_residuals` is `True`) tests.
        check_residuals : bool, default True
            If `True`, performs a residual autocorrelation check using the Breusch-Godfrey test.
            Raises an exception if residuals are autocorrelated.

        Returns
        -------
        AR
            The AR instance.
        """
        method = check_enum_value_is_valid(enum_obj=FitMethodAR, value=method, parameter_name="method", is_none_valid=False)
        self._select_order()
        check_condition(condition=self._is_time_series_stationary(significance_level=significance_level, regression="n"), exception=NonStationaryTimeSeriesException("The time series must be stationary in order to be fitted."))

        if method == FitMethodAR.YULE_WALKER:
            self._parameters = yule_walker(x=self._signs, order=self._order, method="mle", df=None, inv=False, demean=True)[0]
        elif method == FitMethodAR.BURG:
            self._parameters, _ = burg(endog=self._signs, order=self._order, demean=True)
        elif method == FitMethodAR.OLS_WITH_CST:
            ar_model = AutoReg(endog=self._signs, lags=self._order, trend="c").fit()
            self._constant_parameter, self._parameters = ar_model.params[0], ar_model.params[1:]
        else:
            raise IllegalValueException(
                f"The method '{method}' for the parameters estimation is not valid, it must be among {get_enum_values(enum_obj=FitMethodAR)}.")

        if check_residuals:
            _, p_value = self.breusch_godfrey_test(resid=self.resid(seed=1))
            # If the p value is below the significance level, we can reject the null hypothesis of no autocorrelation
            logger.info(f"Breusch-Godfrey test: p value for the null hypothesis of no autocorrelation is {round(p_value, 4)}")
            check_condition(condition=p_value > significance_level,
                            exception=AutocorrelatedResidualsException(f"The residuals of the model seems to be autocorrelated (p value of the null hypothesis of no autocorrelation is {round(p_value, 4)}), you may try to increase the number of lags, or you can set 'check_residuals' to False to disable this check."))

        logger.info(f"The AR({self._order}) model has been fitted with method '{method}'.")
        return self

    def _select_order(self) -> None:
        if self._order_selection_method is None:
            self._order = self._max_order
        elif self._order_selection_method == OrderSelectionMethodAR.PACF:
            pacf_coeffs, confidence_interval = self.calculate_pacf(nb_lags=self._max_order, alpha=0.05)

            pacf_coeffs = pacf_coeffs[1:]
            confidence_interval = confidence_interval[1:]

            lower_band = confidence_interval[:, 0] - pacf_coeffs
            upper_band = confidence_interval[:, 1] - pacf_coeffs

            order = 0
            for acf_coeff, value_lower_band, value_upper_band in zip(pacf_coeffs, lower_band, upper_band):
                if is_value_within_interval_exclusive(value=acf_coeff, lower_bound=value_lower_band, upper_bound=value_upper_band):
                    break
                order += 1
            self._order = order
        else:
            raise IllegalValueException(
                f"The method '{self._order_selection_method}' for the order selection is not valid, it must be among {get_enum_values(enum_obj=OrderSelectionMethodAR)}")

        logger.info(f"AR order selection: {self._order} lags (method: {self._order_selection_method}, time series length: {len(self._signs)}).")

    def simulate(self, size: int, seed: Optional[int] = None) -> np.ndarray:
        """
        Simulate a time series of signs after the model has been fitted.

        Parameters
        ----------
        size : int
            The number of signs to simulate.
        seed : int, default None
            Seed used to initialize the pseudo-random number generator.
            If `seed` is `None`, then a random seed between 0 and 2^32 - 1 is used.

        Returns
        -------
        np.ndarray
            The simulated signs (+1 for buy, -1 for sell).
        """
        check_condition(condition=size > 0, exception=IllegalValueException(f"The size '{size}' for the time series to be simulated is not valid, it must be greater than 0."))
        check_condition(condition=self._parameters is not None, exception=ModelNotFittedException("The model has not yet been fitted. Fit the model first by calling 'fit()'."))

        if seed is None:
            seed = np.random.randint(0, np.iinfo(np.int32).max)

        inverted_parameters = CArray.of(c_type_str="double", arr=self._parameters[::-1])
        last_signs = CArray.of(c_type_str="int", arr=np.asarray(self._signs[-self._order:]).astype(int))
        self._simulation = CArrayEmpty.of(c_type_str="int", size=size)

        cpp_lib = SharedLibrariesRegistry().find_shared_library(name=LIB_TRADEFLOW).load()
        cpp_lib.simulate(size, inverted_parameters, self._constant_parameter, len(inverted_parameters), last_signs, seed, self._simulation)
        return self._simulation[:]
