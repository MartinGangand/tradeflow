import datetime

from trade_flow_modelling.src.dates import DateType, DailyDateType, MonthlyDateType

date_types = {
    "daily": DailyDateType("daily", "%Y-%m-%d", 10), # YYYY-mm-dd
    "monthly": MonthlyDateType("monthly", "%Y-%m", 7) # YYYY-mm
}
        
def is_datetime_within_interval(current_date: datetime, start_date: datetime, end_date: datetime) -> bool:
    return current_date >= start_date and current_date <= end_date

def retrieve_date_type_from_name(name: str) -> DateType:
    return date_types[name]
