from typing import Literal, List
from numbers import Number
import numpy as np
from scipy import linalg
from typing import List
from numbers import Number
from statsmodels.tools import eval_measures

from .RegressionModel import RegressionModel
from ....constants.src.constants import InformationCriterion, OLSMethod
from ....utils.src.general_utils import check_enum_value_is_valid, get_valid_enum_values
from ....exceptions.src.custom_exceptions import IllegalValueException

class OLS(RegressionModel):
    def __init__(self, y: List[Number], x: List[List[Number]]) -> None:
        super().__init__(y=y, x=x)
        
    def fit(self, method: Literal["pinv"]):
        method = check_enum_value_is_valid(enum=OLSMethod, value=method, is_none_valid=False)
        match method:
            case OLSMethod.PINV:
                pseudo_inverse, self._rank = linalg.pinv(self._x, atol=0, rtol=0, return_rank=True)
                beta = pseudo_inverse @ self._y
            case _:
                raise IllegalValueException(f"The method '{method}' for the OLS fit is not valid, it must be among {list(get_valid_enum_values(enum=OLSMethod).keys())}.")
        # TODO: QR method

        return OLSResults(self, beta) 

    def predict(self, beta: List[Number], x=None) -> List[Number]:
        if x is None:
            x = self._x

        return x @ beta
    
    def residuals(self, beta: List[Number]) -> List[Number]:
        return self._y - self.predict(beta, self._x)
    
    def log_likelihood(self, beta: List[Number]) -> float:
        residuals = self.residuals(beta)
        sigma2 = (1.0 / self._nobs) * self._sum_of_squares(residuals)
        llf = -self._nobs * (np.log(2 * np.pi * sigma2) + 1) / 2
        return llf


class OLSResults:
    def __init__(self, model: OLS, beta: List[Number]) -> None:
        self._model = model
        self.beta = beta
        self.nobs = self._model.nobs
        
        self._rank = None
        self._df_model = None
        self._df_model_with_cst = None
        self._k_constant = None
        self._llf = None

    @property
    def rank(self) -> int:
        if (self._rank is None):
            self._rank = self._model.rank
        return self._rank
    
    @property
    def df_model(self) -> int:
        if (self._df_model is None):
            self._df_model = self._model.df_model
        return self._df_model
    
    @property
    def df_model_with_cst(self) -> int:
        if (self._df_model_with_cst is None):
            self._df_model_with_cst = self.df_model + self.k_constant
        return self._df_model_with_cst
    
    @property
    def k_constant(self) -> int:
        if (self._k_constant is None):
            self._k_constant = self._model.k_constant
        return self._k_constant
    
    @property
    def llf(self) -> float:
        """Log-likelihood of the model"""
        if (self._llf is None):
            self._llf = self._model.log_likelihood(self.beta)
        return self._llf

    def info_criterion(self, criterion: Literal["aic", "bic", "hqic"]) -> float:
        criterion = check_enum_value_is_valid(enum=InformationCriterion, value=criterion, is_none_valid=False)
        match criterion:
            case InformationCriterion.AIC:
                return eval_measures.aic(self.llf, self.nobs, self.df_model_with_cst)
            case InformationCriterion.BIC:
                return eval_measures.bic(self.llf, self.nobs, self.df_model_with_cst)
            case InformationCriterion.HQIC:
                return eval_measures.hqic(self.llf, self.nobs, self.df_model_with_cst)
            case _:
                raise IllegalValueException(f"The information criterion '{criterion}' is not valid, it must be among {list(get_valid_enum_values(enum=InformationCriterion).keys())}.")
