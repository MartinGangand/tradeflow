from numbers import Number
from typing import List, Literal
from statsmodels.tsa.tsatools import lagmat
from statsmodels.tsa.stattools import pacf
import statsmodels.api as sm
import pandas as pd
from joblib import Parallel, delayed
from statsmodels.tsa.ar_model import ar_select_order
import mystic as my

from ....regression.src.linear_models.OLS import OLS
from ....constants.src.constants import OLSMethod
from ....utils.src import general_utils

# Information criterion (statsmodels)
def ar_select_order_ic_statsmodels(time_series: List[Number], max_nb_lags: int, criteria: Literal["aic", "bic", "hqic"]) -> int:
    model = ar_select_order(endog=time_series, maxlag=max_nb_lags, ic=criteria, trend="c")
    return len(model.ar_lags)


# Information criterion (custom OLS)
def ar_select_order_ic_custom_ols(time_series: List[Number], max_nb_lags: int, criteria: Literal["aic", "bic", "hqic"]) -> int:
    x, y = lagmat(time_series, max_nb_lags, original="sep")
    x = sm.add_constant(x)
    y = y[max_nb_lags:]
    x = x[max_nb_lags:]
    x_pd = pd.DataFrame(x)

    ics = []
    for i in range(max_nb_lags + 1):
        x_selection = x_pd.values[:, slice(i + 1)]

        ols_model = OLS(y=y, x=x_selection)
        ols_model.df_model = x_selection.shape[1] - 1
        ols_model.k_constant = 1

        res = ols_model.fit(method=OLSMethod.PINV.value)
        
        lags = tuple(j for j in range(1, i + 1)) if i != 0 else ()
        ics.append((lags, res.info_criteria(criteria=criteria)))
    
    selected_tuple = min(ics, key=lambda x: x[1])
    selected_lags = selected_tuple[0]
    return len(selected_lags)


# Information criterion (multi processes)
def ar_select_order_ic_multi_processes(time_series: List[Number], max_nb_lags: int, criteria: Literal["aic", "bic", "hqic"], nb_processes: int) -> int:
    x, y = lagmat(time_series, max_nb_lags, original="sep")
    x = sm.add_constant(x)
    y = y[max_nb_lags:]
    x = x[max_nb_lags:]
    x_pd = pd.DataFrame(x)

    slice_indexes_per_process = dispatch_indexes(max_nb_lags=max_nb_lags, nb_processes=nb_processes)

    result_all_processes = Parallel(n_jobs=nb_processes)(
        delayed(compute_ic)(x_pd=x_pd, y=y, slice_indexes=slice_indexes, criteria=criteria) for slice_indexes in slice_indexes_per_process
        )

    ics = [current_ic for results_current_process in result_all_processes for current_ic in results_current_process]
    assert(len(ics) == max_nb_lags + 1)

    selected_tuple = min(ics, key=lambda x: x[1])
    selected_lags = selected_tuple[0]
    return len(selected_lags) if selected_lags != (0,) else 0

def compute_ic(x_pd, y, slice_indexes, criteria):
    result_current_process = []
    for slice_indexe in slice_indexes:
        x_selection = x_pd.values[:, slice(slice_indexe)]

        ols_model = OLS(y=y, x=x_selection)
        ols_model.df_model = x_selection.shape[1] - 1
        ols_model.k_constant = 1

        res = ols_model.fit(method=OLSMethod.PINV.value)
        
        lags = tuple(j for j in range(1, slice_indexe))
        lags = () if not lags else lags
        result_current_process.append((lags, res.info_criteria(criteria=criteria)))
    return result_current_process

def dispatch_indexes(max_nb_lags, nb_processes) -> List[List[int]]:
    slice_indexes_per_process = [[] for _ in range(nb_processes)]
    direction = True
    for i in range(max_nb_lags + 1):
        args_idx = i % nb_processes
        new_args_idx = args_idx if direction else nb_processes - 1 - args_idx
        direction = not(direction) if args_idx == nb_processes - 1 else direction
        slice_indexes_per_process[new_args_idx].append(i + 1)

    assert(sum([len(l) for l in slice_indexes_per_process]) == max_nb_lags + 1)
    return slice_indexes_per_process


# Information criterion (optimization with mystic)
def ar_select_order_mystic_optimization(time_series: List[Number], max_nb_lags: int, criteria: Literal['aic', 'bic', 'hqic']) -> int:
    x, y = lagmat(time_series, max_nb_lags, original="sep")
    x = sm.add_constant(x)
    y = y[max_nb_lags:]
    x = x[max_nb_lags:]
    x_pd = pd.DataFrame(x)

    nb_lags_to_ic = {}
    def objective_function(nb_lags):
        nb_lags = nb_lags[0]
        if (nb_lags in nb_lags_to_ic):
            return nb_lags_to_ic[nb_lags]
        
        x_selection = x_pd.values[:, slice(nb_lags)]

        ols_model = OLS(y=y, x=x_selection)
        ols_model.df_model = x_selection.shape[1] - 1
        ols_model.k_constant = 1

        res = ols_model.fit(method=OLSMethod.PINV.value)
        info_criteria = res.info_criteria(criteria=criteria)
        
        nb_lags_to_ic[nb_lags] = info_criteria
        return info_criteria
     
    integer_constraint = my.constraints.integers()(lambda x: x)
    result = my.solvers.fmin(cost=objective_function, x0=[0], bounds=[(1, max_nb_lags + 1)], xtol=0.5, maxiter=max_nb_lags + 1, constraints=integer_constraint, disp=False)
    
    return int(result[0]) - 1


# Partial autocorrelation function
def ar_select_order_pacf(time_series: List[Number], max_nb_lags: int, alpha: float) -> int:
    acf_coeffs, confidence_interval = pacf(x=time_series, nlags=max_nb_lags, method="burg", alpha=alpha)

    acf_coeffs = acf_coeffs[1:]
    confidence_interval = confidence_interval[1:]

    lower_band = confidence_interval[:, 0] - acf_coeffs
    upper_band = confidence_interval[:, 1] - acf_coeffs

    ar_model_order = 0
    for acf_coeff, value_lower_band, value_upper_band in zip(acf_coeffs, lower_band, upper_band):
        if (general_utils.isValueWithinIntervalExclusive(lower_bound=value_lower_band, upper_bound=value_upper_band, value=acf_coeff)):
            return ar_model_order
        ar_model_order += 1

    # If no lags within [1, max_nb_lags] are in the band, set max_nb_lags 2 * max_nb_lags and compute again the number of lags
    return ar_select_order_pacf(time_series=time_series, max_nb_lags=max_nb_lags*2, alpha=alpha)
