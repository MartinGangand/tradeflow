from numbers import Number
from typing import List, Literal
import numpy as np

from ..TimeSeriesModel import TimeSeriesModel
from ....constants.src.constants import NbLagsSelectionMethod, InformationCriteria
from ....utils.src import general_utils, logger_utils
from .select_nb_lags_methods import ar_select_order_ic_statsmodels, ar_select_order_ic_custom_ols, ar_select_order_ic_multi_processes, ar_select_order_mystic_optimization

logger = logger_utils.get_logger(__name__)

class ARModel(TimeSeriesModel):
    def __init__(self, time_series: List[Number], nb_lags_selection_method: Literal["ic_statsmodels", "ic_custom_OLS", "ic_multi_processes", "ic_mystic_opti"] = "statsmodels", criteria: Literal["aic", "bic", "hqic"] = "aic") -> None:
        super().__init__(time_series=time_series)
        self._nb_lags_selection_method = general_utils.check_enum_value_is_valid(enum=NbLagsSelectionMethod, value=nb_lags_selection_method)
        self._criteria = general_utils.check_enum_value_is_valid(enum=InformationCriteria, value=criteria)

    def select_nb_lags(self) -> int:
        max_nb_lags = self._compute_max_nb_lags()
        match self._nb_lags_selection_method:
            case NbLagsSelectionMethod.IC_STATSMODELS.value:
                nb_lags = ar_select_order_ic_statsmodels(time_series=self._time_series, max_nb_lags=max_nb_lags, criteria=self._criteria)
            
            case NbLagsSelectionMethod.IC_CUSTOM_OLS.value:
                nb_lags = ar_select_order_ic_custom_ols(time_series=self._time_series, max_nb_lags=max_nb_lags, criteria=self._criteria)
            
            case NbLagsSelectionMethod.IC_MULTI_PROCESSES.value:
                nb_lags = ar_select_order_ic_multi_processes(time_series=self._time_series, max_nb_lags=max_nb_lags, criteria=self._criteria, nb_processes=4)
            
            case NbLagsSelectionMethod.IC_MYSTIC_OPTI.value:
                nb_lags = ar_select_order_mystic_optimization(time_series=self._time_series, max_nb_lags=max_nb_lags, criteria=self._criteria)
        
        logger.info(f"Selected {nb_lags} lags with method {self._nb_lags_selection_method} and information criterion {self._criteria} (len of the time series: {len(self._time_series)})")
        return nb_lags
            
    def _compute_max_nb_lags(self):
        # Schwert (1989)
        max_nb_lags = int(np.ceil(12.0 * np.power(len(self._time_series) / 100.0, 1 / 4.0)))
        logger.info(f"The maximun number of lags has been set to {max_nb_lags} (Schwert 1989)")
        return max_nb_lags
