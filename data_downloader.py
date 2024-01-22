import io
import requests
import zipfile

import utils_dates
import settings

zip_file_url = lambda frequency, symbol, date: f"https://data.binance.vision/data/spot/{frequency}/trades/{symbol}/{symbol}-trades-{date}.zip"

def download_data(symbol, date_type, start_date, end_date):
    date_type_format = utils_dates.DateType.date_type_to_format[date_type]
    start_date = utils_dates.string_to_datetime(start_date, date_type_format)
    end_date = utils_dates.string_to_datetime(end_date, date_type_format)
    folder_to_extract_data = settings.symbol_data_folder(date_type, symbol)
    
    current_date = start_date
    while (current_date <= end_date):
        current_date_as_string = utils_dates.datetime_to_string(current_date, date_type_format)
        current_url = zip_file_url(date_type, symbol, current_date_as_string)

        file = download_file_from_url(current_url)
        extract_file(file, folder_to_extract_data)
        print(f"Saved {date_type} data for {symbol} during {current_date_as_string} in {folder_to_extract_data}/{symbol}-trades-{current_date_as_string}.csv")
        current_date = utils_dates.increment_datetime_by_n_units(current_date, 1, date_type)

def download_file_from_url(url):
    request = requests.get(url, stream=True)
    assert(request.ok == True)
    file = zipfile.ZipFile(io.BytesIO(request.content))
    return file

def extract_file(file: zipfile.ZipFile, folder_to_extract_file: str) -> None:
    file.extract(file.namelist()[0], folder_to_extract_file)
