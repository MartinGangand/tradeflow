import datetime

from trade_flow_modelling.src.date_type import date_types, DateType
from trade_flow_modelling.src.utils import general_utils
        
def is_datetime_within_interval(current_date: datetime, start_date: datetime, end_date: datetime) -> bool:
    return current_date >= start_date and current_date <= end_date
