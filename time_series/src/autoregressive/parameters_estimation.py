from typing import List, Literal
from numbers import Number
import numpy as np
from statsmodels.tsa.ar_model import AutoReg

from ....statistics.autocorrelation.src.autocorrelation import calculate_autocorrelation, calculate_autocorrelation_matrix

def ar_estimate_model_parameters_statsmodels_ols(time_series: List[Number], order: int, trend: Literal["n", "c"]) -> List[Number]:
    ar_model = AutoReg(endog=time_series, lags=order, trend=trend).fit()

    parameters = ar_model.params
    assert(len(parameters) == order if trend == "n" else order + 1)
    return ar_model.params

def ar_estimate_model_parameters_yule_walker(time_series: List[Number], order: int) -> List[Number]:
    # Remove the lag 0 autocorrelation (= 1)
    autocorrelation = calculate_autocorrelation(time_series=time_series, nb_lags=order)[1:]
    assert(len(autocorrelation) == order)

    autocorrelation_matrix = calculate_autocorrelation_matrix(autocorrelation=autocorrelation)

    parameters = np.linalg.solve(autocorrelation_matrix, autocorrelation)
    assert(len(parameters) == order)
    return parameters
