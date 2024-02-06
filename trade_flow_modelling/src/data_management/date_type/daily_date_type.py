import datetime

from trade_flow_modelling.src.data_management.date_type.date_type import DateType

class DailyDateType(DateType):
    def increment_datetime_by_n_units(self, datetime_object: datetime.datetime, n_units: int):
        return datetime_object + datetime.timedelta(days=n_units)
