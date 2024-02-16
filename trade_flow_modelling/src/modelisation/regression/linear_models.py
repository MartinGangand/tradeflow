from typing import Literal, List
from numbers import Number
import numpy as np
from statsmodels.tools.tools import pinv_extended
from statsmodels.tools.sm_exceptions import MissingDataError
from statsmodels.tools.validation import array_like
import time
from scipy import linalg
from numpy.core import asarray, count_nonzero, finfo
from statsmodels.tools import eval_measures

from ..utils import general_utils

class RegressionModel():
    def __init__(self, y: List[Number], x: List[List[Number]]) -> None:
        self._y = array_like(y, "_y", ndim=1)
        self._x = array_like(x, "_x", ndim=2)
        self._nobs = self._x.shape[0]

        self._df_model = None
        self._rank = None
        self._k_constant = None

        self._prediction = None

    @property
    def nobs(self) -> int:
        return self._nobs
    
    @property
    def df_model(self) -> int:
        if self._df_model is None:
            self._df_model = self.rank - self.k_constant
        return self._df_model
    
    @df_model.setter
    def df_model(self, df_model: int) -> None:
        general_utils.check_condition(df_model >= 0, Exception("The model degree of freedom df_model must be greater than or equal to 0"))
        self._df_model = df_model
    
    @property
    def rank(self) -> int:
        if self._rank is None:
            self._rank = np.linalg.matrix_rank(self._x, tol=0)
        return self._rank
    
    @rank.setter
    def rank(self, rank: int) -> None:
        general_utils.check_condition(rank >= 0, Exception("The rank must be greater than or equal to 0"))
        self._rank = rank
    
    @property
    def k_constant(self) -> int:
        if (self._k_constant is None):
            self._k_constant = int(np.array_equal(self._x[:, 0], np.ones(self._nobs)))
            # if self._x is None:
            #     self._k_constant = 0
            # else:
            #     x_max = np.max(self._x, axis=0)
            #     if not np.isfinite(x_max).all():
            #         raise MissingDataError('exog contains inf or nans')
            #     x_min = np.min(self._x, axis=0)
            #     const_idx = np.where(x_max == x_min)[0].squeeze()
            #     self._k_constant = const_idx.size
        return self._k_constant
    
    @k_constant.setter
    def k_constant(self, k_constant: int) -> None:
        k_constant_cond = k_constant == 0 or k_constant == 1
        general_utils.check_condition(k_constant_cond, Exception("The number of constant must be either 0 or 1"))
        self._k_constant = k_constant

    def _sum_of_squares(self, x: List[Number]) -> float:
        """Helper function to calculate sum of squares"""
        return np.sum(x**2)
    
class OLS(RegressionModel):
    def __init__(self, y: List[Number], x: List[List[Number]]) -> None:
        super().__init__(y, x)
        
    def fit(self, method: Literal["pinv", "qr"] = "pinv"):
        if (method == "pinv"):
            # pseudo_inverse = np.linalg.pinv(self._x)
            # pseudo_inverse, singular_values = pinv_extended(self._x)
            pseudo_inverse, self._rank = linalg.pinv(self._x, atol=0, rtol=0, return_rank=True)
            beta = np.dot(pseudo_inverse, self._y)

        return OLSResults(self, beta)

    def predict(self, beta: List[Number], x=None) -> List[Number]:
        if x is None:
            x = self._x

        return np.dot(x, beta)
    
    def predict_opti(self, beta: List[Number]) -> List[Number]:
        if (self._prediction is None):
            return
    
    def residuals(self, beta: List[Number]) -> List[Number]:
        return self._y - self.predict(beta, self._x)
    
    def log_likelihood(self, beta: List[Number]) -> float:
        s = time.time()
        residuals = self.residuals(beta)
        e = time.time()
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

    def info_criteria(self, criteria: str) -> float:
        match criteria:
            case "aic":
                return eval_measures.aic(self.llf, self.nobs, self.df_model_with_cst)
            case "bic":
                return eval_measures.bic(self.llf, self.nobs, self.df_model_with_cst)
            case "hqic":
                return eval_measures.hqic(self.llf, self.nobs, self.df_model_with_cst)
