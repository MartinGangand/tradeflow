from datetime import datetime

print("DATES_UTILS")
        
def is_datetime_within_interval(current_date: datetime, start_date: datetime, end_date: datetime) -> bool:
    return current_date >= start_date and current_date <= end_date

def is_date_within_interval(current_date: str, start_date: str, end_date: str) -> bool:
    current_date = datetime.strptime(current_date, "%Y%m%d")
    start_date = datetime.strptime(start_date, "%Y-%m-%d")
    end_date = datetime.strptime(end_date, "%Y-%m-%d")
    return current_date >= start_date and current_date <= end_date
