from numbers import Number
from typing import List, Tuple
from statsmodels.tsa.ar_model import AutoReg, ar_select_order
import numpy as np

from .time_series_model import TimeSeriesModel

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

    def select_model_nb_lags(self):
        if (self._nb_lags is None):
            mod = ar_select_order(self._time_series, maxlag=100, ic="aic", trend="c")
            return len(mod.ar_lags)
        
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
