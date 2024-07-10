from __future__ import annotations

from typing import List, Literal, Optional

import numpy as np
from statsmodels.regression import yule_walker
from statsmodels.tsa.ar_model import ar_select_order, AutoReg

from tradeflow import logger_utils
from tradeflow.constants import OrderSelectionMethodAR, FitMethodAR, InformationCriterion
from tradeflow.exceptions import IllegalValueException, ModelNotFittedException, IllegalNbLagsException, \
    NonStationaryTimeSeriesException
from tradeflow.general_utils import check_condition, check_enum_value_is_valid, get_enum_values, \
    is_value_within_interval_exclusive
from tradeflow.time_series import TimeSeries

logger = logger_utils.get_logger(__name__)


class AR(TimeSeries):
    """
    Autoregressive model for trade/order signs.

    Parameters
    ----------
    signs : list of {1, -1}
        A list of signs where each element is either 1 (representing a buy) or -1 (representing a sell).
    max_order : int, default None
        The maximum order of the autoregressive model.
        If None, the maximum order is set to 12*(nobs/100)^{1/4} as outlined in Schwert (1989).
    order_selection_method : {'information_criterion', 'pacf'}, default None
        The method for selecting the order of the model. If None, the order of the model will be `max_order`.

        * 'information_criterion' - Choose the model that minimizes a given information criterion.
        * 'pacf' - Choose the model using the number of significant lags in the partial autocorrelation function of the time series of signs.

    information_criterion : {'aic', 'bic', 'hqic'}, optional
        The information criterion to use in the order selection.
        It has no effect if `order_selection_method` is not 'information_criterion'.
        * 'aic' - Akaike information criterion.
        * 'bic' - Bayesian information criterion.
        * 'hqic' - Hannan–Quinn information criterion.
    """

    def __init__(self, signs: List[{1, -1}], max_order: Optional[int] = None,
                 order_selection_method: Optional[Literal["information_criterion", "pacf"]] = None,
                 information_criterion: Optional[Literal["aic", "bic", "hqic"]] = None) -> None:
        super().__init__(signs=signs)
        self._max_order = self._init_max_order(max_order=max_order)
        self._order_selection_method = check_enum_value_is_valid(enum_obj=OrderSelectionMethodAR,
                                                                 value=order_selection_method,
                                                                 parameter_name="order_selection_method",
                                                                 is_none_valid=True)
        self._information_criterion = check_enum_value_is_valid(enum_obj=InformationCriterion,
                                                                value=information_criterion,
                                                                parameter_name="information_criterion",
                                                                is_none_valid=self._order_selection_method is None or self._order_selection_method == OrderSelectionMethodAR.PACF)
        if self._information_criterion is not None and (
                self._order_selection_method is None or self._order_selection_method == OrderSelectionMethodAR.PACF):
            logger.warning(
                f"The information criterion '{self._information_criterion}' will have no effect as the order selection method '{self._order_selection_method}' doesn't use it.")

        # Will be set during fit()
        self._constant_parameter = 0
        self._parameters = None

    def _init_max_order(self, max_order: Optional[int]) -> int:
        if max_order is None:
            # Schwert (1989)
            max_order = int(np.ceil(12.0 * np.power(len(self._signs) / 100.0, 1 / 4.0)))

        check_condition(condition=1 <= max_order < len(self._signs) // 2,
                        exception=IllegalNbLagsException(
                            f"{max_order} is not valid for 'max_order', it must be positive and lower than 50% of the time series length (< {len(self._signs) // 2})."))
        logger.info(f"The maximum order has been set to {max_order}.")
        return max_order

    def fit(self, method: Literal["yule_walker", "ols_with_cst"]) -> AR:
        """
        Estimate the model parameters.

        Parameters
        ----------
        method : {'yule_walker', 'ols_with_cst'}
            The method to use for estimating parameters.

            * 'yule_walker' - Use the Yule Walker equations to estimate model parameters.
              There will be no constant term, thus the percentage of buy signs
              in the time series generated with these parameters will be close to 50%.

            * 'ols_with_cst' - Use OLS to estimate model parameters.
              There will be a constant term, thus the percentage of buy signs in the time series
              generated with these parameters will be close to the one from the training time series.

        Returns
        -------
        AR
            The AR instance.
        """
        method = check_enum_value_is_valid(enum_obj=FitMethodAR, value=method, parameter_name="method",
                                           is_none_valid=False)
        self._select_order()

        match method:
            case FitMethodAR.YULE_WALKER:
                check_condition(self._is_time_series_stationary(regression="n"), NonStationaryTimeSeriesException("The time series must be stationary to be fitted."))
                self._parameters = yule_walker(x=self._signs, order=self._order, method="mle", df=None, inv=False, demean=True)[0]
            case FitMethodAR.OLS_WITH_CST:
                check_condition(self._is_time_series_stationary(regression="c"), NonStationaryTimeSeriesException("The time series must be stationary to be fitted."))
                ar_model = AutoReg(endog=self._signs, lags=self._order, trend="c").fit()
                self._constant_parameter, self._parameters = ar_model.params[0], ar_model.params[1:]
            case _:
                raise IllegalValueException(
                    f"The method '{method}' for the parameters estimation is not valid, it must be among {get_enum_values(enum_obj=FitMethodAR)}.")

        logger.info(f"The AR({self._order}) model has been fitted with method '{method}'.")
        return self

    def _select_order(self) -> None:
        if self._order_selection_method is None:
            self._order = self._max_order

        else:
            match self._order_selection_method:
                case OrderSelectionMethodAR.INFORMATION_CRITERION:
                    model = ar_select_order(endog=self._signs, maxlag=self._max_order,
                                            ic=self._information_criterion.value, trend="n")
                    self._order = len(model.ar_lags)
                case OrderSelectionMethodAR.PACF:
                    pacf_coeffs, confidence_interval = self.calculate_pacf(nb_lags=self._max_order, alpha=0.05)

                    pacf_coeffs = pacf_coeffs[1:]
                    confidence_interval = confidence_interval[1:]

                    lower_band = confidence_interval[:, 0] - pacf_coeffs
                    upper_band = confidence_interval[:, 1] - pacf_coeffs

                    order = 0
                    for acf_coeff, value_lower_band, value_upper_band in zip(pacf_coeffs, lower_band, upper_band):
                        if is_value_within_interval_exclusive(value=acf_coeff, lower_bound=value_lower_band,
                                                              upper_bound=value_upper_band):
                            break
                        order += 1
                    self._order = order
                case _:
                    raise IllegalValueException(
                        f"The method '{self._order_selection_method}' for the order selection is not valid, it must be among {get_enum_values(enum_obj=OrderSelectionMethodAR)}")

        logger.info(
            f"AR order selection: {self._order} lags (method: {self._order_selection_method}, information criterion: {self._information_criterion}, time series length: {len(self._signs)}).")

    def simulate(self, size: int, seed: Optional[int] = None) -> List[int]:
        """
        Simulate a time series of signs after the model has been fitted.

        Parameters
        ----------
        size : int
            The number of signs to simulate.
        seed : int, default None
            Seed used to initialize the pseudo-random number generator.
            If `seed` is ``None``, then a random seed is used.

        Returns
        -------
        list of int
            The simulated signs.
        """
        check_condition(size > 0, IllegalValueException(
            f"The size '{size}' for the time series to be simulated is not valid, it must be greater than 0."))
        check_condition(self._parameters is not None, ModelNotFittedException(
            "The model has not yet been fitted. Fit the model first by calling 'fit()'."))

        np.random.seed(seed=seed)

        previous_signs = self._signs[-self._order:]
        for _ in range(size):
            next_sign_expected_value = self._constant_parameter + np.dot(a=self._parameters,
                                                                         b=previous_signs[-self._order:][::-1])
            next_sign_buy_proba = 0.5 * (1 + next_sign_expected_value)
            next_sign = 1 if np.random.uniform() <= next_sign_buy_proba else -1
            previous_signs = np.append(arr=previous_signs, values=next_sign)

        self._simulation = previous_signs[self._order:]
        return self._simulation
