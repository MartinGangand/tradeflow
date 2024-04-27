from scipy import signal
from typing import List
from numbers import Number

from ...utils.src import general_utils

class AutocorrelationCalculator:
    def __init__(self, time_series: List[Number], nb_lags: int | None = None) -> None:
        self._time_series = time_series
        self._init_nb_lags(nb_lags)

    def _init_nb_lags(self, nb_lags) -> int:
        if (nb_lags is not None):
            self._nb_lags = nb_lags
        else:
            self._nb_lags = len(self._time_series) - 1
        self._check_nb_lags_validity()

    def _check_nb_lags_validity(self) -> None:
        general_utils.check_condition(self._is_nb_lags_valid(),
                                      Exception(f"The number of lags {self._nb_lags} is invalid, it must be < {len(self._time_series)}"))

    def _is_nb_lags_valid(self) -> bool:
        return self._nb_lags < len(self._time_series)
    
    def calculate(self) -> List[Number]:
        acf = signal.correlate(self._time_series, self._time_series, mode="full", method="auto")
        acf_normalized =  acf[len(acf) // 2:][:self._nb_lags + 1] / float(acf.max())
        assert(len(acf_normalized) == self._nb_lags + 1)
        return acf_normalized
    
def calculate_autocorrelation(time_series: List[Number], nb_lags: int | None = None) -> List[Number]:
    autocorrelation_calculator = AutocorrelationCalculator(time_series, nb_lags)
    return autocorrelation_calculator.calculate()    
