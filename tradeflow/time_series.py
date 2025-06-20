from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Literal, Tuple, Any, Optional, List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.tsa.stattools as stattools
from matplotlib.figure import Figure
from scipy import stats
from statsmodels.regression.linear_model import OLS
from statsmodels.tools.typing import ArrayLike1D
from statsmodels.tools.validation import bool_like
from statsmodels.tsa.stattools import acf, pacf
from statsmodels.tsa.tsatools import lagmat

from tradeflow.common import logger_utils
from tradeflow.common.general_utils import check_condition
from tradeflow.exceptions import IllegalNbLagsException, IllegalValueException, \
    ModelNotSimulatedException

logger = logger_utils.get_logger(__name__)


class TimeSeries(ABC):
    """
    Time series model for trade/order signs. Intended to be subclassed.

    Parameters
    ----------
    signs : array_like
        A 1-d endogenous response variable. The dependent variable.
    """

    def __init__(self, signs: ArrayLike1D) -> None:
        self._signs = signs
        self._nb_signs = len(signs)

        # Will be set in fit()
        self._order = None
        
        self._x = None
        self._y = None
        self._first_order_signs = None
        self._start_idx_parameters = None

        # Will be set in simulate()
        self._simulation = None

    @abstractmethod
    def resid(self) -> np.ndarray:
        """
        Estimate and return the residuals of the model.
        """
        pass

    @abstractmethod
    def fit(self, method: str) -> TimeSeries:
        """
        Estimate the model parameters.
        """
        pass

    @abstractmethod
    def simulate(self, size: int) -> np.ndarray:
        """
        Simulate a time series of signs after the model has been fitted.
        """
        pass

    def calculate_acf(self, nb_lags: int, time_series: Optional[ArrayLike1D] = None) -> np.ndarray:
        """
        Calculate the autocorrelation function of a time series of signs.

        Parameters
        ----------
        nb_lags : int
            Number of lags to return autocorrelation for.
        time_series : array_like, default None
            The time series for which to compute the acf. If None, the original time series of the model is used.

        Returns
        -------
        np.ndarray
            The autocorrelation for lags 0, 1, ..., nlags.
            It includes the lag 0 autocorrelation (i.e., 1), thus the size is (nlags + 1,).
        """
        if time_series is None:
            time_series = self._signs

        check_condition(condition=nb_lags is not None and 1 <= nb_lags < len(time_series),
                        exception=IllegalNbLagsException(f"Can only calculate the autocorrelation function with a number of lags positive and lower than the time series length (requested number of lags {nb_lags} should be < {len(time_series)})."))
        return acf(x=time_series, nlags=nb_lags, qstat=False, fft=True, alpha=None, bartlett_confint=True, missing="raise")

    def calculate_pacf(self, nb_lags: int, alpha: Optional[float] = None, time_series: Optional[ArrayLike1D] = None) -> np.ndarray | Tuple[np.ndarray, np.ndarray]:
        """
        Calculate the partial autocorrelation function of a time series of signs.

        Parameters
        ----------
        nb_lags : int
            Number of lags to return autocorrelation for.
        alpha : float, optional
            If a number is given, the confidence intervals for the given level are returned.
            For example, if alpha=0.05, 95 % confidence intervals are returned.
        time_series : array_like, default None
            The time series for which to compute the pacf. If None, the original time series of the model is used.

        Returns
        -------
        pacf : np.ndarray
            The partial autocorrelation for lags 0, 1, ..., nb_lags.
            It includes the lag 0 autocorrelation (i.e., 1), thus the size is (nlags + 1,).
        confint : ndarray, optional
            Confidence intervals for the pacf at lags 0, 1, ..., nb_lags.
            The shape is (nlags + 1, 2). It is Returned if alpha is not None.
        """
        if time_series is None:
            time_series = self._signs

        check_condition(condition=1 <= nb_lags < len(time_series) // 2,
                        exception=IllegalNbLagsException(f"Can only calculate the partial autocorrelation function with a number of lags positive and lower than 50% of the time series length (requested number of lags {nb_lags} should be < {len(time_series) // 2})."))
        check_condition(condition=alpha is None or 0 < alpha <= 1,
                        exception=IllegalValueException(f"Alpha {alpha} is invalid, it must be in the interval [0, 1]"))
        return pacf(x=time_series, nlags=nb_lags, method="burg", alpha=alpha)

    def simulation_summary(self, plot: bool = True, log_scale: bool = True, percentiles: Tuple[float, ...] = (50.0, 75.0, 95.0, 99.0, 99.9)) -> pd.DataFrame:
        """
        Return a statistical summary comparing the original signs and the simulated ones.

        The statistics are computed over the series counting the number of consecutive signs in a row.

        The function is to be called after a model has been fitted and simulated.

        Parameters
        ----------
        plot : bool
            If True, plots two graphs. One comparing the autocorrelation function
            of the original and simulated time series, and another comparing the partial autocorrelation.
        log_scale : bool, default true
            If True, use a log scale for plotting graphs, otherwise use a linear scale.
            It has no effect if `plot` is False.
        percentiles : tuple of float
            The percentiles to use.

        Returns
        -------
        pd.DataFrame
            A DataFrame containing the statistics for the original and simulated time series.
        """
        plot = bool_like(value=plot, name="plot", optional=False, strict=True)
        log_scale = bool_like(value=log_scale, name="log_scale", optional=False, strict=True)
        check_condition(self._simulation is not None, ModelNotSimulatedException("The model has not yet been simulated. Simulate the model first by calling 'simulate()'."))

        statistics_training = self._compute_signs_statistics(signs=self._signs, column_name="Training", percentiles=percentiles)
        statistics_simulation = self._compute_signs_statistics(signs=self._simulation, column_name="Simulation", percentiles=percentiles)
        statistics = pd.concat([statistics_training, statistics_simulation], axis=1).round(decimals=2)

        if plot:
            self._build_fig_corr_training_vs_simulation(log_scale=log_scale)

        return statistics

    @staticmethod
    def is_time_series_stationary(time_series: ArrayLike1D, nb_lags: Optional[int] = None, significance_level: float = 0.05, regression: Literal["c", "ct", "ctt", "n"] = "c") -> bool:
        """
        Test whether a time series is stationary at a given significance level using the Augmented Dickey-Fuller test.

        Parameters
        ----------
        time_series : array_like
            The time series to test for stationarity.
        nb_lags : int, default None
            The number of lags to include in the test. If None, the default used by the test is applied.
        significance_level : float, default 0.05
            The significance level for the test. If the p-value is less than or equal to this value, the time series is considered stationary.
        regression: {'c', 'ct', 'ctt', 'n'}, default 'c'
            Constant and trend order to include in regression.

            * "c" : constant only (default).
            * "ct" : constant and trend.
            * "ctt" : constant, and linear and quadratic trend.
            * "n" : no constant, no trend.

        Returns
        -------
        bool
            True if the time series is stationary at the given significance level, False otherwise.
        """
        df_test = stattools.adfuller(x=time_series, maxlag=nb_lags, regression=regression, autolag=None)
        p_value = df_test[1]

        is_stationary = p_value <= significance_level
        logger.info(f"The time series of signs is {'non-' if not is_stationary else ''}stationary at the significance level {significance_level} (p-value: {np.round(p_value, decimals=6)}, number of lags used: {df_test[2]}).")
        return is_stationary

    @staticmethod
    def breusch_godfrey_test(resid: np.ndarray, nb_lags: Optional[int] = None) -> Tuple[float, float]:
        """
        Perform the Breusch-Godfrey test for residual autocorrelation.

        Parameters
        ----------
        resid : np.ndarray
            The residuals from a regression model. Must be a 1-dimensional array.
        nb_lags : int, default None
            The number of lags to include in the test. If None, defaults to min(10, len(resid) // 5).

        Returns
        -------
        lagrange_multiplier : float
            The value of the Lagrange Multiplier test statistic.
        p_value : float
            The p-value for the test statistic.
        """
        resid = np.asarray(resid)
        if resid.ndim != 1:
            raise ValueError("Residuals must be a 1d array.")

        nb_resid = resid.shape[0]
        if nb_lags is None:
            nb_lags = min(10, resid.shape[0] // 5)

        x = lagmat(x=resid, maxlag=nb_lags, trim="forward", original="ex")
        x_with_cst = np.c_[np.ones(shape=nb_resid), x]

        res = OLS(resid, x_with_cst).fit()

        lagrange_multiplier = nb_resid * res.rsquared
        p_value = stats.chi2.sf(lagrange_multiplier, nb_lags)

        return lagrange_multiplier, p_value

    @classmethod
    def _compute_signs_statistics(cls, signs: ArrayLike1D, column_name: str, percentiles: Tuple[float, ...]) -> pd.DataFrame:
        series_nb_consecutive_signs = cls._compute_series_nb_consecutive_signs(signs=signs)
        names, values = [], []
        names.append("size"), values.append(len(signs))
        names.append("pct_buy (%)"), values.append(cls.percentage_buy(signs=signs))
        names.append("mean_nb_consecutive_values",), values.append(np.mean(series_nb_consecutive_signs))
        names.append("std_nb_consecutive_values"), values.append(np.std(series_nb_consecutive_signs))
        names.extend([f"Q{percentile}_nb_consecutive_values" for percentile in percentiles])
        values.extend(np.percentile(series_nb_consecutive_signs, percentiles))

        return pd.DataFrame(data=values, columns=[column_name], index=names)

    @staticmethod
    def _compute_series_nb_consecutive_signs(signs: ArrayLike1D) -> np.ndarray:
        series_nb_consecutive_signs = []
        current_nb = 1
        for i in range(1, len(signs)):
            if signs[i] == signs[i - 1]:
                current_nb += 1
            else:
                series_nb_consecutive_signs.append(current_nb)
                current_nb = 1

        series_nb_consecutive_signs.append(current_nb)
        assert np.sum(series_nb_consecutive_signs) == len(signs)
        return np.array(series_nb_consecutive_signs)

    @staticmethod
    def percentage_buy(signs: ArrayLike1D) -> float:
        return round(100 * sum([1 for sign in signs if sign == 1]) / len(signs), 2)

    def _build_fig_corr_training_vs_simulation(self, log_scale: bool = True) -> Figure:
        nb_lags = min(2 * self._order, len(self._signs) // 2 - 1)
        acf_training = self.calculate_acf(nb_lags=nb_lags)
        acf_simulation = self.calculate_acf(nb_lags=nb_lags, time_series=self._simulation)
        pacf_training = self.calculate_pacf(nb_lags=nb_lags, alpha=None)
        pacf_simulation = self.calculate_pacf(nb_lags=nb_lags, alpha=None, time_series=self._simulation)

        fig, axe = plt.subplots(1, 2, figsize=(16, 4))

        acf_title = f"ACF function for training and simulated time series"
        self._fill_axe(axe=axe[0], functions=[acf_training, acf_simulation], colors=["green", "purple"], linestyles=["dashed", "solid"], labels=["Training", "Simulation"], title=acf_title, xlabel="Lag", log_scale=log_scale, order=self._order)

        pacf_title = f"PACF function for training and simulated time series"
        self._fill_axe(axe=axe[1], functions=[pacf_training, pacf_simulation], colors=["green", "purple"], linestyles=["dashed", "solid"], labels=["Training", "Simulation"], title=pacf_title, xlabel="Lag", log_scale=log_scale, order=self._order)

        return fig

    @staticmethod
    def _fill_axe(axe: Any, functions: List[np.ndarray], colors: List[str], linestyles: List[str], labels: List[str], title: str, xlabel: str, log_scale: bool, order: Optional[int] = None) -> None:
        all_values = np.concatenate(functions)
        y_scale = f"{'log' if log_scale else 'linear'}"

        for function, color, linestyle, label in zip(functions, colors, linestyles, labels):
            axe.plot(function, color=color, linestyle=linestyle, label=label)

        axe.set_title(f"{title} ({y_scale} scale)")
        axe.set_yscale(y_scale)

        axe.set_xlabel(xlabel)
        axe.set_xlim(-1, max(len(function) for function in functions) - 1)

        y_min = max(0.0001, np.min(all_values)) if log_scale else np.min(all_values)
        axe.set_ylim(y_min, np.max(all_values) + 0.1)

        if order is not None:
            axe.axvline(x=order, color="blue", label="Order of the model", linestyle="--")

        axe.grid()
        axe.legend()

    def plot_acf_and_pacf(self, nb_lags: int, log_scale: bool = True, time_series: Optional[ArrayLike1D] = None) -> Figure:
        if time_series is None:
            time_series = self._signs

        acf_function = self.calculate_acf(nb_lags=nb_lags, time_series=time_series)
        pacf_function = self.calculate_pacf(nb_lags=nb_lags, alpha=None, time_series=time_series)

        fig, axe = plt.subplots(1, 2, figsize=(16, 4))
        self._fill_axe(axe=axe[0], functions=[acf_function], colors=["green"], linestyles=["solid"], labels=[f"Time series of size {len(time_series)}"], title="ACF function", xlabel="Lag", log_scale=log_scale, order=None)
        self._fill_axe(axe=axe[1], functions=[pacf_function], colors=["orange"], linestyles=["solid"], labels=[f"Time series of size {len(time_series)}"], title="PACF function", xlabel="Lag", log_scale=log_scale, order=None)

        return fig
