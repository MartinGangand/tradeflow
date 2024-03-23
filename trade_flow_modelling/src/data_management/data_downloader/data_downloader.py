import io
import requests
import zipfile
from typing import Literal

from ..date_type import date_types
from  ... import settings

print("DATA_DOWNLOADER")

zip_file_url = lambda periodicity, symbol, date: f"https://data.binance.vision/data/spot/{periodicity}/trades/{symbol}/{symbol}-trades-{date}.zip"

def download_data(symbol: str, date_type_periodicity: Literal["daily", "monthly"], start_date: str, end_date: str, verbose: bool = True):
    date_type = date_types.retrieve_date_type_from_periodicity(date_type_periodicity)

    start_date = date_type.string_to_datetime(start_date)
    end_date = date_type.string_to_datetime(end_date)
    folder_to_extract_data = settings.symbol_data_folder(date_type.periodicity, symbol)
    
    current_date = start_date
    while (current_date <= end_date):
        current_date_as_string = date_type.datetime_to_string(current_date)
        current_url = zip_file_url(date_type.periodicity, symbol, current_date_as_string)

        file = download_file_from_url(current_url)
        extract_file(file, folder_to_extract_data)
        if (verbose):
            print(f"Saved {date_type.periodicity} data for {symbol} during {current_date_as_string} in {folder_to_extract_data}/{symbol}-trades-{current_date_as_string}.csv")
        current_date = date_type.increment_datetime_by_n_units(current_date, 1)

def download_file_from_url(url):
    request = requests.get(url, stream=True)
    assert(request.ok == True)
    file = zipfile.ZipFile(io.BytesIO(request.content))
    return file

def extract_file(file: zipfile.ZipFile, folder_to_extract_file: str) -> None:
    file.extract(file.namelist()[0], folder_to_extract_file)
