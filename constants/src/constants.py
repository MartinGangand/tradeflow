from enum import Enum
import logging

class NbLagsSelectionMethod(Enum):
    IC_STATSMODELS = "ic_statsmodels"
    IC_CUSTOM_OLS = "ic_custom_OLS"
    IC_MULTI_PROCESSES = "ic_multi_processes"
    IC_MYSTIC_OPTI = "ic_mystic_opti"
    
class InformationCriteria(Enum):
    AIC = "aic"
    BIC = "bic"
    HQIC = "hqic"

class OLSMethod(Enum):
    PINV = "pinv"

class Logger:
    FORMAT = "%(asctime)s [%(filename)s] [%(levelname)s] - %(message)s"
    LEVEL = logging.INFO
    