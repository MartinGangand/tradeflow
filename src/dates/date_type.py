from abc import ABC, abstractmethod
from datetime import datetime

class DateType(ABC):
    def __init__(self, name: str, format: str, len_date: int):
        self._name = name
        self._format = format
        self._len_date = len_date

    @property
    def name(self):
        return self._name
    
    @property
    def format(self):
        return self._format
    
    @property
    def len_date(self):
        return self._len_date

    def string_to_datetime(self, date_as_string: str) -> datetime:
        return datetime.strptime(date_as_string, self._format)
    
    def datetime_to_string(self, datetime: datetime) -> str:
        return datetime.strftime(self._format)
    
    def retrieve_date_as_string_from_file_path(self, file_path: str) -> str:
        # file_path format is https://data.binance.vision/data/spot/{frequency}/trades/{symbol}/{symbol}-trades-{date}.zip
        return file_path.split(".")[0][-self._len_date:]

    
    @abstractmethod
    def increment_datetime_by_n_units(datetime_object: datetime, n_units: int):
        pass