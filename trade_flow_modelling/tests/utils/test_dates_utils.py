import pytest
import datetime

from trade_flow_modelling.src.utils import dates_utils

daily_format = dates_utils.DateType.date_type_to_format[dates_utils.DateType.DAILY]

# Tests for daily date_type
def test_string_to_date_daily():
    date_time_daily = dates_utils.string_to_datetime("2024-02-02", "%Y-%m-%d")
    assert type(date_time_daily) is datetime.datetime
    assert date_time_daily.year == 2024
    assert date_time_daily.month == 2
    assert date_time_daily.day == 2

def test_string_to_date_daily_too_short_format():
    with pytest.raises(ValueError) as ex_info:
        date_time_daily = dates_utils.string_to_datetime("2024-02-01", "%Y-%m")
    assert str(ex_info.value) == "unconverted data remains: -01"

def test_string_to_date_daily_too_long_format():
    with pytest.raises(ValueError) as ex_info:
        date_time_daily = dates_utils.string_to_datetime("2024-02-01", "%Y-%m-%d %H:%M:%S")
    assert str(ex_info.value) == "time data '2024-02-01' does not match format '%Y-%m-%d %H:%M:%S'"

def test_string_to_date_daily_incorrect_string():
    with pytest.raises(ValueError) as ex_info:
        date_time_daily = dates_utils.string_to_datetime("2024-02-0a", "%Y-%m-%d")
    assert str(ex_info.value) == "time data '2024-02-0a' does not match format '%Y-%m-%d'"

def test_string_to_date_daily_incorrect_string_start_and_too_short_format():
    with pytest.raises(ValueError) as ex_info:
        date_time_daily = dates_utils.string_to_datetime("20a4-02-02", "%Y-%m")
    assert str(ex_info.value) == "time data '20a4-02-02' does not match format '%Y-%m'"

def test_string_to_date_daily_incorrect_string_end_and_too_short_format():
    with pytest.raises(ValueError) as ex_info:
        date_time_daily = dates_utils.string_to_datetime("2024-02-0a", "%Y-%m")
    assert str(ex_info.value) == "unconverted data remains: -0a"

def test_string_to_date_daily_incorrect_string_and_too_long_format():
    with pytest.raises(ValueError) as ex_info:
        date_time_daily = dates_utils.string_to_datetime("2024-0a-02", "%Y-%m-%d %H:%M:%S")
    assert str(ex_info.value) == "time data '2024-0a-02' does not match format '%Y-%m-%d %H:%M:%S'"

# Tests for monthly date_type
def test_string_to_date_monthly():
    date_time_monthly = dates_utils.string_to_datetime("2024-02", "%Y-%m")
    assert type(date_time_monthly) is datetime.datetime
    assert date_time_monthly.year == 2024
    assert date_time_monthly.month == 2
    assert date_time_monthly.day == 1

def test_string_to_date_monthly_too_short_format():
    with pytest.raises(ValueError) as ex_info:
        date_time_monthly = dates_utils.string_to_datetime("2024-02", "%Y")
    assert str(ex_info.value) == "unconverted data remains: -02"

def test_string_to_date_monthly_too_long_format():
    with pytest.raises(ValueError) as ex_info:
        date_time_monthly = dates_utils.string_to_datetime("2024-02", "%Y-%m-%d")
    assert str(ex_info.value) == "time data '2024-02' does not match format '%Y-%m-%d'"

def test_string_to_date_monthly_incorrect_string():
    with pytest.raises(ValueError) as ex_info:
        date_time_monthly = dates_utils.string_to_datetime("20a4-02", "%Y-%m")
    assert str(ex_info.value) == "time data '20a4-02' does not match format '%Y-%m'"

def test_string_to_date_monthly_incorrect_string_start_and_too_short_format():
    with pytest.raises(ValueError) as ex_info:
        date_time_monthly = dates_utils.string_to_datetime("20a4-02", "%Y")
    assert str(ex_info.value) == "time data '20a4-02' does not match format '%Y'"

def test_string_to_date_monthly_incorrect_string_end_and_too_short_format():
    with pytest.raises(ValueError) as ex_info:
        date_time_monthly = dates_utils.string_to_datetime("2024-0a", "%Y")
    assert str(ex_info.value) == "unconverted data remains: -0a"

def test_string_to_date_monthly_incorrect_string_and_too_long_format():
    with pytest.raises(ValueError) as ex_info:
        date_time_monthly = dates_utils.string_to_datetime("202a-02", "%Y-%m-%d %H:%M:%S")
    assert str(ex_info.value) == "time data '202a-02' does not match format '%Y-%m-%d %H:%M:%S'"