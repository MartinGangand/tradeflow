from dateutil.relativedelta import relativedelta
from datetime import datetime

from trade_flow_modelling.src.data_management.date_type.date_type import DateType

class MonthlyDateType(DateType):
    def increment_datetime_by_n_units(self, datetime_object: datetime, n_units: int):
        return datetime_object + relativedelta(months=n_units)
