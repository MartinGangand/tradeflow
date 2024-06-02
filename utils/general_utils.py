from enum import EnumType, Enum
from numbers import Number
from typing import List, Any

from ..exceptions.custom_exceptions import EnumValueException


def check_condition(condition: bool, exception: Exception) -> bool:
    if not condition:
        raise exception
    return True


def get_enum_values(enum: EnumType) -> List[Any]:
    return [enum_object.value for enum_object in enum]


def check_enum_value_is_valid(enum: EnumType, value: object | None, is_none_valid: bool, parameter_name: str) -> Enum | None:
    exception_message = f"The value '{value}' for {parameter_name} is not valid, it must be among {get_enum_values(enum=enum)} or None if it is valid."
    if value is None:
        if is_none_valid:
            return value
        else:
            raise EnumValueException(exception_message)

    try:
        enum_object = enum(value)
    except ValueError:
        raise EnumValueException(exception_message)
    else:
        return enum_object


def is_value_within_interval_exclusive(value: Number, lower_bound: Number, upper_bound: Number) -> bool:
    return lower_bound < value < upper_bound
