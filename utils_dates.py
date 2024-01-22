import datetime
from dateutil.relativedelta import relativedelta

class DateType:
    DAILY = "daily"
    MONTHLY = "monthly"

    date_type_to_format = {
        DAILY: "%Y-%m-%d",
        MONTHLY: "%Y-%m"
    }

    date_type_to_len_date_as_string = {
        DAILY: 10, # YYYY-mm-dd
        MONTHLY: 7 # YYYY-mm
    }

def string_to_datetime(date_as_string, format):
    return datetime.datetime.strptime(date_as_string, format)

def datetime_to_string(datetime, format):
    return datetime.strftime(format)

def increment_datetime_by_n_units(datetime_object, n_units, date_type):
    match date_type:
        case DateType.DAILY:
            return datetime_object + datetime.timedelta(days=n_units)
        case DateType.MONTHLY:
            return datetime_object + relativedelta(months=n_units)
        
def is_datetime_within_interval(current_date: datetime, start_date: datetime, end_date: datetime) -> bool:
    return current_date >= start_date and current_date <= end_date
        