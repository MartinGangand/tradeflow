from .date_type import DateType
from .daily_date_type import DailyDateType
from .monthly_date_type import MonthlyDateType
from ...modelisation.utils import general_utils

print("DATES TYPES")

date_types = {
    "daily": DailyDateType("daily", "%Y-%m-%d", 10), # YYYY-mm-dd
    "monthly": MonthlyDateType("monthly", "%Y-%m", 7) # YYYY-mm
}

def retrieve_date_type_from_periodicity(date_type_periodicity: str) -> DateType:
    is_periodicity_valid = is_date_type_periodicity_valid(date_type_periodicity)
    general_utils.check_condition(is_periodicity_valid, Exception(f"The periodicity '{date_type_periodicity}' is valid, it must be among {list(date_types.keys())}"))
    return date_types[date_type_periodicity]

def is_date_type_periodicity_valid(date_type_periodicity: str):
    return date_type_periodicity in date_types.keys()
