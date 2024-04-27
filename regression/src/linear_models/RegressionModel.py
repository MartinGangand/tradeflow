from abc import ABC
from typing import List
from numbers import Number
import numpy as np
from statsmodels.tools.validation import array_like

from ....utils.src import general_utils
from ....exceptions.src.custom_exceptions import IllegalValueException

class RegressionModel(ABC):
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
        general_utils.check_condition(df_model >= 0, IllegalValueException("The model degree of freedom df_model must be greater than or equal to 0"))
        self._df_model = df_model
    
    @property
    def rank(self) -> int:
        if self._rank is None:
            self._rank = np.linalg.matrix_rank(self._x, tol=0)
        return self._rank
    
    @rank.setter
    def rank(self, rank: int) -> None:
        general_utils.check_condition(rank >= 0, IllegalValueException("The rank must be greater than or equal to 0"))
        self._rank = rank
    
    @property
    def k_constant(self) -> int:
        if (self._k_constant is None):
            self._k_constant = int(np.array_equal(self._x[:, 0], np.ones(self._nobs)))
        return self._k_constant
    
    @k_constant.setter
    def k_constant(self, k_constant: int) -> None:
        k_constant_cond = k_constant == 0 or k_constant == 1
        general_utils.check_condition(k_constant_cond, IllegalValueException("The number of constant must be either 0 or 1"))
        self._k_constant = k_constant

    def _sum_of_squares(self, x: List[Number]) -> float:
        """Helper function to calculate sum of squares"""
        return np.sum(x**2)
    