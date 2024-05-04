from scipy import signal
from typing import List
from numbers import Number

from ....utils.src.general_utils import check_condition

def calculate_autocorrelation(time_series: List[Number], nb_lags: int | None = None) -> List[Number]:
    nb_lags = len(time_series) - 1 if nb_lags is None else nb_lags
    check_condition(nb_lags < len(time_series),
                                    Exception(f"The number of lags {nb_lags} is invalid, it must be < {len(time_series)}."))

    acf = signal.correlate(time_series, time_series, mode="full", method="auto")
    acf_normalized =  acf[len(acf) // 2:][:nb_lags + 1] / float(acf.max())
    assert(len(acf_normalized) == nb_lags + 1)
    return acf_normalized

def calculate_autocorrelation_matrix(autocorrelation: List[Number]) -> List[List[Number]]:
    nb_lags = len(autocorrelation)
    
    autocorrelation_matrix = []   
    row_zeros = [0 for _ in range(nb_lags)]
    for i in range(nb_lags):
        current_row = row_zeros.copy()
        for j in range(nb_lags):
            idx = abs(i - j)
            current_row[j] = autocorrelation[idx - 1] if idx != 0 else 1

        autocorrelation_matrix.append(current_row)

    return autocorrelation_matrix
