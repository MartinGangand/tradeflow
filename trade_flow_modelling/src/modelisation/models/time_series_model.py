from abc import ABC, abstractmethod
from typing import List, Literal, Tuple
from numbers import Number
import statsmodels.tsa.stattools as stattools

from ..utils import general_utils

class TimeSeriesModel(ABC):
    def __init__(self, time_series: List[Number]) -> None:
        self._time_series = time_series

    def check_time_series_stationarity(self, nb_lags: int) -> None:
        general_utils.check_condition(
            self.is_time_series_stationary(max_lag=nb_lags),
            Exception("The time series must be stationary in order to simulate signs")
        )

    def is_time_series_stationary(
        self,
        significance_level : float = 0.05,
        max_lag: int | None = None,
        regression: Literal["c", "ct", "ctt", "n"] = "c",
        autolag: Literal["AIC", "BIC", "t-stat"] | None = None,
        verbose: bool = False
    ):
        df_test = stattools.adfuller(self._time_series, maxlag=max_lag, regression=regression, autolag=autolag)
        p_value = df_test[1]

        if (verbose):
            print(f"Test Statistic: {df_test[0]}")
            print(f"p-value: {df_test[1]}")
            print(f"#Lags Used: {df_test[2]}")
            print(f"Number of Observations Used: {df_test[3]}")

            for key, value in df_test[4].items():
                print(f"Critical Value ({key}): {value}")

        return p_value <= significance_level
    
    @abstractmethod
    def simulate(self, size: int) -> Tuple[List[Number], int]:
        pass
