from typing import Dict
from enum import Enum

from ...exceptions.src.custom_exceptions import EnumValueException

def check_condition(condition: bool, exception: Exception):
    if (not condition):
        raise exception
    
def get_valid_enum_values(enum: Enum) -> Dict[str, Enum]:
    valid_enum_values = []
    for valid_enun in enum:
        valid_enum_values.append(valid_enun.value)
    return valid_enum_values

def check_enum_value_is_valid(enum: Enum, value: str) -> str:
    valid_enum_values = get_valid_enum_values(enum=enum)
    check_condition(value in valid_enum_values,
                                  EnumValueException(f"The value '{value}' is not valid, it must be among {valid_enum_values}"))
    return value
