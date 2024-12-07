import enum
from typing import List, Any, Optional, Union

from tradeflow.common.exceptions import EnumValueException


def check_condition(condition: bool, exception: Exception) -> None:
    """
    Raise an exception if a condition is false, otherwise do nothing.

    Parameters
    ----------
    condition : bool
        The condition to check.
    exception : Exception
        The exception to raise if the condition is false.

    Raises
    ------
    Exception
        If the condition is false.
    """
    if not condition:
        raise exception


def get_enum_values(enum_obj: enum) -> List[Any]:
    """
    Return a list containing the values of an enum.

    Parameters
    ----------
    enum_obj : enum.EnumType
        The enum for which the values will be retrieved.

    Returns
    -------
    list of any
        The values of the enum.
    """
    return [enum_object.value for enum_object in enum_obj]


def check_enum_value_is_valid(enum_obj: enum, value: Optional[object], is_none_valid: bool, parameter_name: str) -> Optional[enum.Enum]:
    """
    Raise an EnumValueException if a value is not within an enum.

    Parameters
    ----------
    enum_obj : enum.EnumType
        The enum to check the value against.
    value : object or None
        The value to verify.
    is_none_valid : bool
        Flag indicating whether None is allowed.
    parameter_name : str
        Variable name for exceptions.

    Returns
    -------
    enum.Enum or None
        Enum associated to the passed value or None if the value is None and is_none_valid is true.

    Raises
    ------
    EnumValueException
        If the value does not exist withing the enum or if the value is None and `is_none_valid` is false.
    """
    exception_message = f"The value '{value}' for {parameter_name} is not valid, it must be among {get_enum_values(enum_obj=enum_obj)} or None if it is valid."
    if value is None:
        if is_none_valid:
            return value
        else:
            raise EnumValueException(exception_message)

    try:
        enum_obj = enum_obj(value)
    except ValueError:
        raise EnumValueException(exception_message)
    else:
        return enum_obj


def is_value_within_interval_exclusive(value: Union[int, float], lower_bound: Union[int, float], upper_bound: Union[int, float]) -> bool:
    """
    Return whether a value is strictly within an interval or not.

    Parameters
    ----------
    value : int or float
        The value to check.
    lower_bound : int or float
        The strict lower bound of the interval.
    upper_bound : int or float
        The strict upper bound of the interval

    Returns
    -------
    bool
        True if the value is strictly within the interval, false otherwise.
    """
    return lower_bound < value < upper_bound
