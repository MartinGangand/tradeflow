from numbers import Number
from typing import List, Literal
from statsmodels.tsa.tsatools import lagmat
from statsmodels.tsa.stattools import pacf
import pandas as pd
from joblib import Parallel, delayed
from statsmodels.tsa.ar_model import ar_select_order
import mystic as my

from ....regression.src.linear_models.OLS import OLS
from ....constants.src.constants import OLSMethod
from ....utils.src.general_utils import isValueWithinIntervalExclusive

# Information criterion (statsmodels)
def ar_select_order_ic_statsmodels(time_series: List[Number], max_order: int, criterion: Literal["aic", "bic", "hqic"], trend: Literal["n", "c"]) -> int:
    model = ar_select_order(endog=time_series, maxlag=max_order, ic=criterion, trend=trend)
    return len(model.ar_lags)


# Information criterion (custom OLS)
def ar_select_order_ic_custom_ols(time_series: List[Number], max_order: int, criterion: Literal["aic", "bic", "hqic"]) -> int:
    x, y = lagmat(time_series, max_order, original="sep")
    y = y[max_order:]
    x = x[max_order:]
    x_pd = pd.DataFrame(x)

    ics = []
    for current_nb_lags in range(1, max_order + 1):
        x_selection = x_pd.values[:, slice(current_nb_lags)]
        assert(x_selection.shape[1] == current_nb_lags)

        ols_model = OLS(y=y, x=x_selection)
        ols_model.df_model = x_selection.shape[1]
        ols_model.k_constant = 0

        res = ols_model.fit(method=OLSMethod.PINV.value)
        
        lags = tuple(j for j in range(1, current_nb_lags + 1))
        ics.append((lags, res.info_criterion(criterion=criterion)))
    
    selected_tuple = min(ics, key=lambda x: x[1])
    selected_lags = selected_tuple[0]
    return len(selected_lags)


# Information criterion (multi processes)
def ar_select_order_ic_multi_processes(time_series: List[Number], max_order: int, criterion: Literal["aic", "bic", "hqic"], nb_processes: int) -> int:
    x, y = lagmat(time_series, max_order, original="sep")
    y = y[max_order:]
    x = x[max_order:]
    x_pd = pd.DataFrame(x)

    slice_indexes_per_process = dispatch_indexes(max_order=max_order, nb_processes=nb_processes)

    result_all_processes = Parallel(n_jobs=nb_processes)(
        delayed(compute_ic)(x_pd=x_pd, y=y, slice_indexes=slice_indexes, criterion=criterion) for slice_indexes in slice_indexes_per_process
        )

    ics = [current_ic for results_current_process in result_all_processes for current_ic in results_current_process]
    assert(len(ics) == max_order)

    selected_tuple = min(ics, key=lambda x: x[1])
    selected_lags = selected_tuple[0]
    return len(selected_lags)

def compute_ic(x_pd: pd.DataFrame, y: List[Number], slice_indexes: List[int], criterion: Literal['aic', 'bic', 'hqic']):
    result_current_process = []
    for current_nb_lags in slice_indexes:
        x_selection = x_pd.values[:, slice(current_nb_lags)]
        assert(x_selection.shape[1] == current_nb_lags)

        ols_model = OLS(y=y, x=x_selection)
        ols_model.df_model = x_selection.shape[1]
        ols_model.k_constant = 0

        res = ols_model.fit(method=OLSMethod.PINV.value)
        
        lags = tuple(j for j in range(1, current_nb_lags + 1))
        result_current_process.append((lags, res.info_criterion(criterion=criterion)))
    return result_current_process

def dispatch_indexes(max_order: int, nb_processes: int) -> List[List[int]]:
    slice_indexes_per_process = [[] for _ in range(nb_processes)]
    direction = True
    for i in range(max_order):
        args_idx = i % nb_processes
        new_args_idx = args_idx if direction else nb_processes - 1 - args_idx
        direction = not(direction) if args_idx == nb_processes - 1 else direction
        slice_indexes_per_process[new_args_idx].append(i + 1)

    assert(sum([len(l) for l in slice_indexes_per_process]) == max_order)
    return slice_indexes_per_process


# Information criterion (optimization with mystic)
def ar_select_order_mystic_optimization(time_series: List[Number], max_order: int, criterion: Literal['aic', 'bic', 'hqic']) -> int:
    x, y = lagmat(time_series, max_order, original="sep")
    y = y[max_order:]
    x = x[max_order:]
    x_pd = pd.DataFrame(x)

    nb_lags_to_ic = {}
    def objective_function(nb_lags):
        nb_lags = nb_lags[0]
        if (nb_lags in nb_lags_to_ic):
            return nb_lags_to_ic[nb_lags]
        
        x_selection = x_pd.values[:, slice(nb_lags)]
        assert(x_selection.shape[1] == nb_lags)

        ols_model = OLS(y=y, x=x_selection)
        ols_model.df_model = x_selection.shape[1]
        ols_model.k_constant = 0

        res = ols_model.fit(method=OLSMethod.PINV.value)
        info_criterion = res.info_criterion(criterion=criterion)
        
        nb_lags_to_ic[nb_lags] = info_criterion
        return info_criterion
     
    integer_constraint = my.constraints.integers()(lambda x: x)
    result = my.solvers.fmin(cost=objective_function, x0=[1], bounds=[(1, max_order + 1)], xtol=0.5, maxiter=max_order + 1, constraints=integer_constraint, disp=False)
    
    return int(result[0])


# Partial autocorrelation function
def ar_select_order_pacf(time_series: List[Number], max_order: int, alpha: float) -> int:
    acf_coeffs, confidence_interval = pacf(x=time_series, nlags=max_order, method="burg", alpha=alpha)

    acf_coeffs = acf_coeffs[1:]
    confidence_interval = confidence_interval[1:]

    lower_band = confidence_interval[:, 0] - acf_coeffs
    upper_band = confidence_interval[:, 1] - acf_coeffs

    ar_model_order = 0
    for acf_coeff, value_lower_band, value_upper_band in zip(acf_coeffs, lower_band, upper_band):
        if (isValueWithinIntervalExclusive(lower_bound=value_lower_band, upper_bound=value_upper_band, value=acf_coeff)):
            return ar_model_order
        ar_model_order += 1

    # If no lags within [1, max_order] are in the band, set max_order to 2 * max_order and compute again the number of lags
    return ar_select_order_pacf(time_series=time_series, max_order=max_order*2, alpha=alpha)
