from __future__ import annotations

from abc import ABC, abstractmethod
from numbers import Number
from typing import List, Literal, Tuple, Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.tsa.stattools as stattools
from matplotlib.figure import Figure
from statsmodels.tools.validation import bool_like
from statsmodels.tsa.stattools import acf, pacf

from ..exceptions.custom_exceptions import IllegalNbLagsException, IllegalValueException, ModelNotSimulatedException
from ..utils.general_utils import check_condition

PERCENTILES = [50, 75, 95, 99, 99.9]


class TimeSeries(ABC):
    def __init__(self, time_series: List[Number]) -> None:
        self._time_series = time_series
        self._order = None
        self._simulation = None  # Will be set during simulate()

    def check_time_series_stationarity(self, nb_lags: int) -> None:
        check_condition(
            self.is_time_series_stationary(max_lag=nb_lags),
            Exception("The time series must be stationary in order to simulate signs.")
        )

    def is_time_series_stationary(
        self,
        significance_level: float = 0.05,
        max_lag: int | None = None,
        regression: Literal["c", "ct", "ctt", "n"] = "c",
        autolag: Literal["AIC", "BIC", "t-stat"] | None = None,
        verbose: bool = False
    ) -> bool:
        df_test = stattools.adfuller(self._time_series, maxlag=max_lag, regression=regression, autolag=autolag)
        p_value = df_test[1]

        if verbose:
            print(f"Test Statistic: {df_test[0]}")
            print(f"p-value: {p_value}")
            print(f"# Lags Used: {df_test[2]}")
            print(f"Number of Observations Used: {df_test[3]}")

            for key, value in df_test[4].items():
                print(f"Critical Value ({key}): {value}")

        return p_value <= significance_level

    @abstractmethod
    def fit(self, method: str) -> TimeSeries:
        pass

    @abstractmethod
    def simulate(self, size: int) -> List[Number]:
        pass

    def calculate_acf(self, nb_lags: int, time_series: List[Number] = None) -> np.ndarray:
        if time_series is None:
            time_series = self._time_series

        check_condition(condition=nb_lags is not None and 1 <= nb_lags < len(time_series),
                        exception=IllegalNbLagsException(f"Can only calculate the autocorrelation function with a number of lags positive and lower than the time series length (requested number of lags {nb_lags} should be < {len(time_series)})."))
        return acf(x=time_series, nlags=nb_lags, qstat=False, fft=True, alpha=None, bartlett_confint=True, missing="raise")

    def calculate_pacf(self, nb_lags: int, alpha: float | None = 0.05, time_series: List[Number] = None) -> np.ndarray | Tuple[np.ndarray, np.ndarray]:
        if time_series is None:
            time_series = self._time_series

        check_condition(condition=1 <= nb_lags < len(time_series) // 2,
                        exception=IllegalNbLagsException(f"Can only calculate the partial autocorrelation function with a number of lags positive and lower than 50% of the time series length (requested number of lags {nb_lags} should be < {len(time_series) // 2})."))
        check_condition(condition=alpha is None or 0 < alpha <= 1,
                        exception=IllegalValueException(f"Alpha {alpha} is invalid, it must be in the interval [0, 1]"))
        return pacf(x=time_series, nlags=nb_lags, method="burg", alpha=alpha)

    def simulation_summary(self, plot: bool = True, log_scale: bool = True) -> pd.DataFrame:
        plot = bool_like(value=plot, name="plot", optional=False, strict=True)
        log_scale = bool_like(value=log_scale, name="log_scale", optional=False, strict=True)
        check_condition(self._simulation is not None, ModelNotSimulatedException("The model has not yet been simulated. Simulate the model first by calling 'simulate()'."))

        statistics_training = self._compute_signs_statistics(signs=self._time_series, column_name="Training")
        statistics_simulation = self._compute_signs_statistics(signs=self._simulation, column_name="Simulation")
        statistics = pd.concat([statistics_training, statistics_simulation], axis=1).round(decimals=2)

        if plot:
            self._plot_corr_training_vs_simulation(log_scale=log_scale)

        return statistics

    @classmethod
    def _compute_signs_statistics(cls, signs: List[Number] | None, column_name: str) -> pd.DataFrame:
        series_nb_consecutive_values = cls._compute_series_nb_consecutive_values(signs=signs)
        names, values = [], []
        names.append("size"), values.append(len(signs))
        names.append("pct_buy (%)"), values.append(cls._percentage_buy(signs=signs))
        names.append("mean_nb_consecutive_values",), values.append(np.mean(series_nb_consecutive_values))
        names.append("std_nb_consecutive_values"), values.append(np.std(series_nb_consecutive_values))
        names.extend([f"Q{percentile}_nb_consecutive_values" for percentile in PERCENTILES])
        values.extend(np.percentile(series_nb_consecutive_values, PERCENTILES))

        return pd.DataFrame(data=values, columns=[column_name], index=names)

    @staticmethod
    def _compute_series_nb_consecutive_values(signs: list[Number]) -> List[int]:
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
        return series_nb_consecutive_signs

    @staticmethod
    def _percentage_buy(signs: List[Number]) -> float:
        return round(100 * sum([1 for sign in signs if sign == 1]) / len(signs), 2)

    def _plot_corr_training_vs_simulation(self, log_scale: bool = True) -> Figure:
        nb_lags = min(2 * self._order, len(self._time_series) // 2 - 1)
        acf_training = self.calculate_acf(nb_lags=nb_lags)
        acf_simulation = self.calculate_acf(nb_lags=nb_lags, time_series=self._simulation)
        pacf_training = self.calculate_pacf(nb_lags=nb_lags, alpha=None)
        pacf_simulation = self.calculate_pacf(nb_lags=nb_lags, alpha=None, time_series=self._simulation)

        fig, axe = plt.subplots(1, 2, figsize=(16, 4))

        acf_title = f"ACF plot for training and simulated time series"
        self._plot_training_vs_simulation(axe=axe[0], training=acf_training, simulation=acf_simulation, title=acf_title,
                                          order=self._order, log_scale=log_scale)

        pacf_title = f"PACF plot for training and simulated time series"
        self._plot_training_vs_simulation(axe=axe[1], training=pacf_training, simulation=pacf_simulation, title=pacf_title,
                                          order=self._order, log_scale=log_scale)

        plt.show()
        return fig

    @staticmethod
    def _plot_training_vs_simulation(axe: Any, training: np.ndarray, simulation: np.ndarray, order: int, title: str, log_scale: bool) -> None:
        all_values = np.concatenate((training, simulation))
        y_scale = f"{'log' if log_scale else 'linear'}"

        axe.plot(training, "green", linestyle="dashed", label=f"Training")
        axe.plot(simulation, "purple", label=f"Simulation")
        axe.set_yscale(y_scale)
        axe.set_title(f"{title} ({y_scale} scale)")
        axe.set_xlabel("Lag")
        axe.set_xlim(-1, len(training) - 1)
        y_min = max(0.0001, np.min(all_values)) if y_scale == "log" else np.min(all_values)
        axe.set_ylim(y_min, np.max(all_values) + 0.1)
        axe.axvline(x=order, color='blue', label="Order of the model", linestyle='--')
        axe.grid()
        axe.legend()
