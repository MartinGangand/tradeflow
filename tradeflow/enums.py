from enum import Enum


class OrderSelectionMethodAR(Enum):
    PACF = "pacf"

    def __str__(self) -> str:
        return self._value_


class FitMethodAR(Enum):
    YULE_WALKER = ("yule_walker", False)
    BURG = ("burg", False)
    CMLE_WITHOUT_CST = ("cmle_without_cst", False)
    CMLE_WITH_CST = ("cmle_with_cst", True)
    MLE_WITHOUT_CST = ("mle_without_cst", False)
    MLE_WITH_CST = ("mle_with_cst", True)

    def __new__(cls, name: str, has_cst_parameter: bool):
        obj = object.__new__(cls)
        obj._value_ = name
        obj.has_cst_parameter = has_cst_parameter
        return obj

    def __str__(self) -> str:
        return self._value_
