from enum import Enum


class OrderSelectionMethodAR(Enum):
    PACF = "pacf"

    def __str__(self) -> str:
        return self._value_


class FitMethodAR(Enum):
    YULE_WALKER = "yule_walker"
    BURG = "burg"
    OLS_WITH_CST = "ols_with_cst"

    def __str__(self) -> str:
        return self._value_
