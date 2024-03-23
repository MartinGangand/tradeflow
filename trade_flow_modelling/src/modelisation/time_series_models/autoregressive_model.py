from numbers import Number
from typing import List, Tuple, Literal
from statsmodels.tsa.ar_model import AutoReg, ar_select_order
import numpy as np
from statsmodels.tsa.tsatools import lagmat
import statsmodels.api as sm
import pandas as pd
from joblib import Parallel, delayed
import mystic as my

from .time_series_model import TimeSeriesModel
from ..regression import linear_models

class AutoregressiveModel(TimeSeriesModel):
    def __init__(self, time_series: List[Number], nb_lags: int | None = None) -> None:
        super().__init__(time_series)
        self._nb_lags = nb_lags

    def simulate(self, size: int) -> Tuple[List[Number], int]:
        self.select_model_nb_lags()
        self.check_time_series_stationarity(self._nb_lags)
        model_parameters = self.estimate_model_parameters()
        simulated_signs = self.simulate_time_series_from_model_parameters(model_parameters, size)

        return simulated_signs, self._nb_lags

    def select_model_nb_lags(self, version: Literal["statsmodels", "opti", "multi_processes", "mystic_opti"], ic: Literal["aic", "bic", "hqic"]= "aic", nb_processes = 4, init_pct=1):
        if (self._nb_lags is None):
            match version:
                case "statsmodels":
                    maxlag = int(np.ceil(12.0 * np.power(len(self._time_series) / 100.0, 1 / 4.0)))
                    mod = ar_select_order(self._time_series, maxlag=maxlag, ic=ic, trend="c")
                    return len(mod.ar_lags)
                
                case "opti":
                    selected_lags = ar_select_order_opti(self._time_series, max_lag=None, ic=ic)
                    return len(selected_lags) if selected_lags != (0,) else 0
                
                case "multi_processes":
                    selected_lags, ics = ar_select_order_multi_processes(self._time_series, max_lag=None, ic=ic, nb_processes=nb_processes)
                    return len(selected_lags) if selected_lags != (0,) else 0
                
                case "mystic_opti":
                    nb_lags = ar_select_order_mystic_opti(self._time_series, ic=ic, init_pct=init_pct)
                    return nb_lags
                
       
    def estimate_model_parameters(self) -> List[Number]:
        ar_model = AutoReg(self._time_series, lags=self._nb_lags, trend="c").fit()
        return ar_model.params
    
    def simulate_time_series_from_model_parameters(self, model_params: List[Number], size: int) -> List[Number]:
        nb_params = len(model_params) - 1

        previous_signs = self._time_series[-nb_params:]
        assert(len(previous_signs) == nb_params)
        for _ in range(size):
            expected_value = self.compute_next_sign_expected_value(model_params, previous_signs)
            proba_to_buy = self.expected_value_to_proba_to_buy(expected_value)      
            next_sign = self._simulate_next_sign(proba_to_buy)
            previous_signs.append(next_sign)

        simulated_signs = previous_signs[nb_params:]
        assert(len(simulated_signs) == size)
        return simulated_signs

    def compute_next_sign_expected_value(self, model_params, previous_signs):
        assert(len(previous_signs) >= len(model_params) - 1)
        expected_value = model_params[0]
        for i in range(1, len(model_params)):
            expected_value += (model_params[i] * previous_signs[-i])
        return expected_value

    def expected_value_to_proba_to_buy(self, expected_value):
        proba_to_buy = self._capped_proba((1 + expected_value) / 2)
        assert(self._is_proba_valid(proba_to_buy))
        return proba_to_buy

    def _capped_proba(self, proba):
        capped_proba = None
        if (proba > 1):
            capped_proba = 1
        elif (proba < 0):
            capped_proba = 0
        else:
            capped_proba = proba

        return capped_proba

    def _is_proba_valid(self, proba):
        return proba >= 0 and proba <= 1

    def _simulate_next_sign(self, proba_to_buy):
        return 1 if np.random.uniform() <= proba_to_buy else -1
    
def simulate_signs(time_series: List[Number], nb_lags: int | None, size: int) -> Tuple[List[Number], int]:
    autoregressive_model = AutoregressiveModel(time_series, nb_lags)
    simulated_signs, nb_lags = autoregressive_model.simulate(size)
    return simulated_signs, nb_lags

def ar_select_order_opti(y: List[Number], max_lag: int | None = None, ic: Literal["aic", "bic", "hqic"] = "aic") -> Tuple[int]:
    if (max_lag is None):
        # Schwert (1989)
        max_lag = int(np.ceil(12.0 * np.power(len(y) / 100.0, 1 / 4.0)))

    x, y = lagmat(y, max_lag, original="sep")
    x = sm.add_constant(x)
    y = y[max_lag:]
    x = x[max_lag:]
    x_pd = pd.DataFrame(x)

    ics = []
    for i in range(max_lag + 1):
        x_selection = x_pd.values[:, slice(i + 1)]

        ols_model = linear_models.OLS(y, x_selection)
        ols_model.df_model = x_selection.shape[1] - 1
        ols_model.k_constant = 1

        res = ols_model.fit()
        
        lags = tuple(j for j in range(1, i + 1))
        lags = 0 if not lags else lags
        ics.append((lags, res.info_criteria(ic)))
    
    selected_tuple = min(ics, key=lambda x: x[1])
    selected_lags = selected_tuple[0]
    return selected_lags

def ar_select_order_multi_processes(y: List[Number], max_lag: int | None, ic: Literal["aic", "bic", "hqic"], nb_processes: int):
    if (max_lag is None):
        # Schwert (1989)
        max_lag = int(np.ceil(12.0 * np.power(len(y) / 100.0, 1 / 4.0)))

    x, y = lagmat(y, max_lag, original="sep")
    x = sm.add_constant(x)
    y = y[max_lag:]
    x = x[max_lag:]
    x_pd = pd.DataFrame(x)

    slice_indexes_per_process = dispatch_indexes(max_lag, nb_processes)

    results_all_processes = Parallel(n_jobs=nb_processes)(
        delayed(compute_ic)(x_pd, y, slice_indexes, ic) for slice_indexes in slice_indexes_per_process
        )

    ics = [current_ic for results_current_process in results_all_processes for current_ic in results_current_process]
    assert(len(ics) == max_lag + 1)

    selected_tuple = min(ics, key=lambda x: x[1])
    selected_lags = selected_tuple[0]
    return selected_lags, ics

def compute_ic(x_pd, y, slice_indexes, ic):
    results_current_process = []
    for slice_indexe in slice_indexes:
        x_selection = x_pd.values[:, slice(slice_indexe)]

        ols_model = linear_models.OLS(y, x_selection)
        ols_model.df_model = x_selection.shape[1] - 1
        ols_model.k_constant = 1

        res = ols_model.fit()
        
        lags = tuple(j for j in range(1, slice_indexe))
        lags = (0,) if not lags else lags
        results_current_process.append((lags, res.info_criteria(ic)))
    return results_current_process

def dispatch_indexes(max_lag, nb_processes):
    slice_indexes_per_process = [[] for _ in range(nb_processes)]
    direction = True
    for i in range(max_lag + 1):
        args_idx = i % nb_processes
        new_args_idx = args_idx if direction else nb_processes - 1 - args_idx
        direction = direction if args_idx != nb_processes - 1 else not(direction)
        slice_indexes_per_process[new_args_idx].append(i + 1)

    assert(sum([len(l) for l in slice_indexes_per_process]) == max_lag + 1)
    return slice_indexes_per_process


def ar_select_order_mystic_opti(signs: List[Number], ic: Literal['aic', 'bic', 'hqic'], init_pct=1):
    max_lag = int(np.ceil(12.0 * np.power(len(signs) / 100.0, 1 / 4.0)))

    x, y = lagmat(signs, max_lag, original="sep")
    x = sm.add_constant(x)
    y = y[max_lag:]
    x = x[max_lag:]
    x_pd = pd.DataFrame(x)

    nb_lags_to_ic = {}
    def objective_function(nb_lags):
        nb_lags = nb_lags[0]
        if (nb_lags in nb_lags_to_ic):
            return nb_lags_to_ic[nb_lags]
        
        x_selection = x_pd.values[:, slice(nb_lags)]

        ols_model = linear_models.OLS(y, x_selection)
        ols_model.df_model = x_selection.shape[1] - 1
        ols_model.k_constant = 1

        res = ols_model.fit()
        info_criteria = res.info_criteria(ic)
        
        nb_lags_to_ic[nb_lags] = info_criteria
        return info_criteria
     
    integer_constraint = my.constraints.integers()(lambda x:x)
    initial_value = 0
    result = my.solvers.fmin(objective_function, [initial_value], bounds=[(1, max_lag + 1)], xtol=0.5, maxiter=max_lag + 1, constraints=integer_constraint, disp=False)
    
    return round(result[0]) - 1
