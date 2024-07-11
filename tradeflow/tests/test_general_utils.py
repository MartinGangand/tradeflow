from enum import Enum

import numpy as np
import pytest

from tradeflow.exceptions import EnumValueException
from tradeflow.general_utils import check_condition, get_enum_values, \
    check_enum_value_is_valid, \
    is_value_within_interval_exclusive


class MyEnumWithoutNone(Enum):
    ENUM_1 = "enum_value_1"
    ENUM_2 = "enum_value_2"


class MyEnumWithNone(Enum):
    ENUM_1 = "enum_value_1"
    ENUM_2 = "enum_value_2"
    NONE = None


@pytest.fixture
def enum_without_none():
    yield MyEnumWithoutNone


@pytest.fixture
def enum_with_none():
    yield MyEnumWithNone


def test_check_condition():
    assert check_condition(condition=True, exception=Exception("Exception message")) is None


def test_check_condition_should_raise_exception():
    with pytest.raises(Exception) as ex:
        check_condition(condition=False, exception=Exception("Exception message"))
    assert str(ex.value) == "Exception message"


@pytest.mark.parametrize("enum,expected_enum_values", [
    ("enum_without_none", ["enum_value_1", "enum_value_2"]),
    ("enum_with_none", ["enum_value_1", "enum_value_2", None])
])
def test_get_enum_values(enum, expected_enum_values, request):
    actual_enum_values = get_enum_values(enum_obj=request.getfixturevalue(enum))
    assert np.array_equal(expected_enum_values, actual_enum_values)


@pytest.mark.parametrize("enum,enum_value,is_none_valid,expected_enum", [
    ("enum_without_none", "enum_value_1", True, MyEnumWithoutNone.ENUM_1),
    ("enum_without_none", "enum_value_1", False, MyEnumWithoutNone.ENUM_1),
    ("enum_without_none", None, True, None),
    ("enum_with_none", None, True, None),
])
def test_check_enum_value_is_valid(enum, enum_value, is_none_valid, expected_enum, request):
    enum = request.getfixturevalue(enum)
    assert check_enum_value_is_valid(enum_obj=enum, value=enum_value, is_none_valid=is_none_valid, parameter_name="enum_value") == expected_enum


@pytest.mark.parametrize("enum,enum_value,is_none_valid,expected_valid_values", [
    ("enum_without_none", "enum_3", True, "['enum_value_1', 'enum_value_2']"),
    ("enum_without_none", "enum_3", False, "['enum_value_1', 'enum_value_2']"),
    ("enum_without_none", None, False, "['enum_value_1', 'enum_value_2']"),
    ("enum_with_none", None, False, "['enum_value_1', 'enum_value_2', None]")
])
def test_check_enum_value_is_valid_should_raise_exception(enum, enum_value, is_none_valid, expected_valid_values, request):
    expected_exception_message = f"The value '{enum_value}' for enum_value is not valid, it must be among {expected_valid_values} or None if it is valid."
    enum = request.getfixturevalue(enum)
    with pytest.raises(EnumValueException) as ex:
        check_enum_value_is_valid(enum_obj=enum, value=enum_value, is_none_valid=is_none_valid, parameter_name="enum_value")

    assert str(ex.value) == expected_exception_message


@pytest.mark.parametrize("value,lower_bound,upper_bound,expected", [
    (1, 0, 2, True),
    (1, 0.9, 1.5, True),
    (1.5, 0.9, 1.6, True),
    (1, 1, 2, False),
    (1, 1.1, 1.5, False),
    (1.0, 1.0, 1.5, False),
])
def test_is_value_within_interval_exclusive(value, lower_bound, upper_bound, expected):
    assert is_value_within_interval_exclusive(value=value, lower_bound=lower_bound, upper_bound=upper_bound) == expected
