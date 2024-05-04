from typing import Dict
from enum import Enum
from numbers import Number

from ...exceptions.src.custom_exceptions import EnumValueException

def check_condition(condition: bool, exception: Exception):
    if (not condition):
        raise exception
    
def get_valid_enum_values(enum: Enum) -> Dict[str, Enum]:
    enum_value_to_enum = {}
    for valid_enum in enum:
        assert(valid_enum.value not in enum_value_to_enum)
        enum_value_to_enum[valid_enum.value] = valid_enum
    return enum_value_to_enum

def check_enum_value_is_valid(enum: Enum, value: str, is_none_valid: bool = False) -> Enum:
    if (value is None and is_none_valid):
        return value
    
    enum_value_to_enum = get_valid_enum_values(enum=enum)
    check_condition(value in enum_value_to_enum, EnumValueException(f"The value '{value}' is not valid, it must be among {list(enum_value_to_enum.keys())}."))
    return enum_value_to_enum[value]

def isValueWithinIntervalExclusive(lower_bound: Number, upper_bound: Number, value: Number) -> bool:
    return value > lower_bound and value < upper_bound
