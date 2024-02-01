import pyspark.sql.functions as F
import glob

from utils import pyspark_utils
from utils import dates_utils
from utils.dates_utils import DateType
import settings
from typing import Literal

from utils import dates_utils
from utils import general_utils

# class DataAgregator():
#     def __init__(self, project_folder, symbol, extension):
#         self.project_folder = project_folder
#         self.symbol = symbol
#         self.extension = extension

def load_data(symbol, date_type_name: Literal["daily", "monthly"], start_date, end_date, sort_column=["time", "id"]):
    date_type = dates_utils.retrieve_date_type_from_name(date_type_name)

    data_folder = settings.symbol_data_folder(date_type.name, symbol)
    data = aggregate_data_several_dates(data_folder, symbol, date_type, start_date, end_date)
    data = rename_columns(data)
    data = add_date_and_time(data)
    data = add_trade_sign(data)
    return data.sort(sort_column)

def aggregate_data_several_dates(data_folder, symbol, date_type: DateType, start_date, end_date):
    spark = pyspark_utils.get_spark_session()
    
    start_date = date_type.string_to_datetime(start_date)
    end_date = date_type.string_to_datetime(end_date)

    data = None
    file_paths = glob.glob(f"{data_folder}/*.csv")
    for file_path in file_paths:
        current_file_date_as_string = date_type.retrieve_date_as_string_from_file_path(file_path)
        current_date = date_type.string_to_datetime(current_file_date_as_string)

        if (dates_utils.is_datetime_within_interval(current_date, start_date, end_date) and general_utils.is_symbol_in_file_path(symbol, file_path)):
            data_current_date = spark.read.csv(file_path, sep=',', inferSchema=True, header=False)
            data = data_current_date if data is None else data.union(data_current_date)
    return data

def rename_columns(data):
    data = data.withColumnRenamed("_c0", "id")\
               .withColumnRenamed("_c1", "price")\
               .withColumnRenamed("_c2", "qty")\
               .withColumnRenamed("_c3", "dollar_value")\
               .withColumnRenamed("_c4", "time")\
               .withColumnRenamed("_c5", "is_buyer_maker")
    return data

def add_date_and_time(data):
    date_expr = F.from_unixtime(F.col("time") / 1000, "yyyyMMdd")
    date_time_expr = F.from_unixtime(F.col("time") / 1000, "yyyy-MM-dd HH:mm:ss")

    data = data.withColumn("date", date_expr)\
               .withColumn("date_time", date_time_expr)
    return data

def add_trade_sign(data):
    side_expr = F.when(F.col("is_buyer_maker") == "true", "sell").otherwise("buy")
    epsilon_expr = F.when(F.col("side") == "buy", 1.0).otherwise(-1.0)

    data = data.withColumn("side", side_expr)\
               .withColumn("epsilon", epsilon_expr)
    return data
