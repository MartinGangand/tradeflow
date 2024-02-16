from numbers import Number
from typing import List, Tuple, Literal
from statsmodels.tsa.ar_model import AutoReg, ar_select_order
import numpy as np
from statsmodels.tsa.tsatools import lagmat
import statsmodels.api as sm
import time
from trade_flow_modelling.src import bis
import pandas as pd
from IPython.display import display

from .time_series_model import TimeSeriesModel
from ..regression import linear_models

class AutoregressiveModel(TimeSeriesModel):
    def __init__(self, time_series: List[Number], nb_lags: int | None) -> None:
        super().__init__(time_series)
        self._nb_lags = nb_lags

    def simulate(self, size: int) -> Tuple[List[Number], int]:
        self.select_model_nb_lags()
        self.check_time_series_stationarity(self._nb_lags)
        model_parameters = self.estimate_model_parameters()
        simulated_signs = self.simulate_time_series_from_model_parameters(model_parameters, size)

        return simulated_signs, self._nb_lags

    def select_model_nb_lags(self, version: Literal["statsmodels", "opti"]):
        if (self._nb_lags is None):
            match version:
                case "statsmodels":
                    maxlag = int(np.ceil(12.0 * np.power(len(self._time_series) / 100.0, 1 / 4.0)))
                    print(f"Max lag has been set to {maxlag} (statsmodels)")
                    mod = ar_select_order(self._time_series, maxlag=maxlag, ic="aic", trend="c")
                    return len(mod.ar_lags), []
                
                case "statsmodels_bis":
                    maxlag = int(np.ceil(12.0 * np.power(len(self._time_series) / 100.0, 1 / 4.0)))
                    print(f"Max lag has been set to {maxlag} (statsmodels_bis)")
                    mod, times = bis.ar_select_order(self._time_series, maxlag=maxlag, ic="aic", trend="c")
                    return len(mod.ar_lags), times
                case "opti":
                    selected_lags, times = ar_select_order_opti(self._time_series, max_lag=None, ic="aic")
                    return len(selected_lags) if selected_lags != 0 else 0, times
        
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
        print(f"Max lag has been set to {max_lag} (opti)")

    x, y = lagmat(y, max_lag, original="sep")
    x = sm.add_constant(x)
    y = y[max_lag:]
    x = x[max_lag:]
    x_pd = pd.DataFrame(x)

    ics = []
    times = [[], [], [], [], [], [], [], [], []]
    for i in range(max_lag + 1):
        s_loop = time.time()

        s_selection = time.time()
        x_selection = x_pd.values[:, slice(i + 1)]
        e_selection = time.time()

        s_ols = time.time()
        ols_model = linear_models.OLS(y, x_selection)
        ols_model.df_model = x_selection.shape[1] - 1
        ols_model.k_constant = 1
        e_ols = time.time()

        s_fit = time.time()
        res = ols_model.fit()
        e_fit = time.time()
        
        s_llf = time.time()
        res.llf
        e_llf = time.time()
        lags = tuple(j for j in range(1, i + 1))
        lags = 0 if not lags else lags
        ics.append((lags, res.info_criteria(ic)))
        e_loop = time.time()
        
        times[0].append(e_loop - s_loop)
        times[1].append(e_fit - s_fit)
        times[2].append(e_selection - s_selection)
        times[3].append(e_ols - s_ols)
        times[4].append(e_llf - s_llf)
    
    selected_tuple = min(ics, key=lambda x: x[1])
    selected_lags = selected_tuple[0]
    return selected_lags, times
