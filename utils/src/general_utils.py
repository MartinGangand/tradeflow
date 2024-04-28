from typing import Dict
from enum import Enum
from numbers import Number

from ...exceptions.src.custom_exceptions import EnumValueException

def check_condition(condition: bool, exception: Exception):
    if (not condition):
        raise exception
    
def get_valid_enum_values(enum: Enum) -> Dict[str, Enum]:
    valid_enum_values = []
    for valid_enun in enum:
        valid_enum_values.append(valid_enun.value)
    return valid_enum_values

def check_enum_value_is_valid(enum: Enum, value: str, is_none_valid: bool = False) -> str:
    valid_enum_values = get_valid_enum_values(enum=enum)
    is_value_valid = value in valid_enum_values
    if (not is_value_valid and is_none_valid):
        is_value_valid = value is None
    check_condition(is_value_valid, EnumValueException(f"The value '{value}' is not valid, it must be among {valid_enum_values}"))
    return value

def isValueWithinIntervalExclusive(lower_bound: Number, upper_bound: Number, value: Number) -> bool:
    return value > lower_bound and value < upper_bound
