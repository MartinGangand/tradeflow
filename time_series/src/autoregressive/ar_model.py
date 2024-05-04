from numbers import Number
from typing import List, Literal
import numpy as np

from ..TimeSeriesModel import TimeSeriesModel
from ....constants.src.constants import OrderSelectionMethodAR, FitMethodAR, InformationCriterion
from ....utils.src import logger_utils
from ....utils.src.general_utils import check_condition, check_enum_value_is_valid, get_valid_enum_values
from ....exceptions.src.custom_exceptions import IllegalValueException
from .order_selection import ar_select_order_ic_statsmodels, ar_select_order_ic_custom_ols, ar_select_order_ic_multi_processes, ar_select_order_mystic_optimization, ar_select_order_pacf
from .parameters_estimation import ar_estimate_model_parameters_statsmodels_ols, ar_estimate_model_parameters

logger = logger_utils.get_logger(__name__)

class AR(TimeSeriesModel):
    def __init__(self, time_series: List[Number],  max_nb_lags: int | None, order_selection_method: Literal["ic_statsmodels", "ic_custom_OLS", "ic_multi_processes", "ic_mystic_opti", "pacf"] | None = "pacf", information_criterion: Literal["aic", "bic", "hqic"] | None = None) -> None:
        super().__init__(time_series=time_series)
        self._max_nb_lags = self._init_max_nb_lags(max_nb_lags=max_nb_lags)
        self._order_selection_method = check_enum_value_is_valid(enum=OrderSelectionMethodAR, value=order_selection_method, is_none_valid=True)
        self._information_criterion = check_enum_value_is_valid(enum=InformationCriterion, value=information_criterion, is_none_valid=self._order_selection_method is None or not self._order_selection_method.requires_ic)
        if (self._order_selection_method is not None and not self._order_selection_method.requires_ic and self._information_criterion is not None):
            logger.info(f"The information criterion '{self._information_criterion}' will have no effect as the order selection method '{self._order_selection_method}' doesn't use it.")
        self._order = self._init_order()

    def _init_max_nb_lags(self, max_nb_lags: int | None) -> int:
        if (max_nb_lags is None):
            # Schwert (1989)
            max_nb_lags = int(np.ceil(12.0 * np.power(len(self._time_series) / 100.0, 1 / 4.0)))    

        check_condition(max_nb_lags >= 1, IllegalValueException(f"{max_nb_lags} is not valid for 'max_nb_lags', it must be >= 1."))
        logger.info(f"The maximun number of lags has been set to {max_nb_lags}.")
        return max_nb_lags

    def _init_order(self) -> int:
        if (self._order_selection_method is None):
            return self._max_nb_lags
        
        match self._order_selection_method:
            case OrderSelectionMethodAR.IC_STATSMODELS:
                order = ar_select_order_ic_statsmodels(time_series=self._time_series, max_nb_lags=self._max_nb_lags, criterion=self._information_criterion.value)
            case OrderSelectionMethodAR.IC_CUSTOM_OLS:
                order = ar_select_order_ic_custom_ols(time_series=self._time_series, max_nb_lags=self._max_nb_lags, criterion=self._information_criterion.value)
            case OrderSelectionMethodAR.IC_MULTI_PROCESSES:
                order = ar_select_order_ic_multi_processes(time_series=self._time_series, max_nb_lags=self._max_nb_lags, criterion=self._information_criterion.value, nb_processes=4)
            case OrderSelectionMethodAR.IC_MYSTIC_OPTI:
                order = ar_select_order_mystic_optimization(time_series=self._time_series, max_nb_lags=self._max_nb_lags, criterion=self._information_criterion.value)
            case OrderSelectionMethodAR.PACF:
                order = ar_select_order_pacf(time_series=self._time_series, max_nb_lags=self._max_nb_lags, alpha=0.05)
            case _:
                raise IllegalValueException(f"The method '{self._order_selection_method}' for the order selection is not valid, it must be among {list(get_valid_enum_values(enum=OrderSelectionMethodAR).keys())}")
        
        logger.info(f"AR order selection: {order} lags (method: {self._order_selection_method}, information criterion: {self._information_criterion}, length time series: {len(self._time_series)}).")
        return order
    
    def fit(self, method: Literal["statsmodels_ols", "yule_walker"]) -> List[Number]:
        method = check_enum_value_is_valid(enum=FitMethodAR, value=method, is_none_valid=False)

        match method:
            case FitMethodAR.STATSMODELS_OLS:
                parameters = ar_estimate_model_parameters_statsmodels_ols(time_series=self._time_series, order=self._order)
            case FitMethodAR.YULE_WALKER:
                parameters = ar_estimate_model_parameters(time_series=self._time_series, order=self._order)
            case _:
                raise IllegalValueException(f"The method '{method}' for the parameters estimation is not valid, it must be among {list(get_valid_enum_values(enum=FitMethodAR).keys())}")

        logger.info(f"The AR model has been fitted with method '{method}'.")
        return parameters
