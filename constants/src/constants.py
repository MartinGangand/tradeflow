from enum import Enum
import logging

class OrderSelectionMethodAR(Enum):        
    IC_STATSMODELS = "ic_statsmodels", True
    IC_STATSMODELS_WITH_CST = "ic_statsmodels_with_cst", True
    IC_CUSTOM_OLS = "ic_custom_OLS", True
    IC_MULTI_PROCESSES = "ic_multi_processes", True
    IC_MYSTIC_OPTI = "ic_mystic_opti", True
    PACF = "pacf", False

    def __new__(cls, *args, **kwds):
        obj = object.__new__(cls)
        obj._value_ = args[0]
        return obj
    
    def __init__(self, _: str, requires_ic: bool) -> None:
        self._requires_ic_ = requires_ic

    def __str__(self) -> str:
        return self._value_

    @property
    def requires_ic(self) -> bool:
        return self._requires_ic_

class FitMethodAR(Enum):
    STATSMODELS_OLS = "statsmodels_ols"
    STATSMODELS_OLS_WITH_CST = "statsmodels_ols_with_cst"
    YULE_WALKER = "yule_walker"
    
    def __str__(self) -> str:
        return self._value_

class InformationCriterion(Enum):
    AIC = "aic"
    BIC = "bic"
    HQIC = "hqic"

    def __str__(self) -> str:
        return self._value_

class CorrelationFunction(Enum):
    ACF = "acf"
    PACF = "pacf"

    def __str__(self) -> str:
        return self._value_

class OLSMethod(Enum):
    PINV = "pinv"

class Logger:
    FORMAT = "%(asctime)s [%(filename)s] [%(levelname)s] - %(message)s"
    LEVEL = logging.INFO
    