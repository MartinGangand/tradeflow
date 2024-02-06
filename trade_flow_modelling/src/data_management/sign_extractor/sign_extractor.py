from typing import List
from pyspark.sql import DataFrame
from pyspark.sql.functions import udf
from pyspark.sql.types import BooleanType
import pyspark.sql.functions as F

from ...modelisation.utils import pyspark_utils, general_utils, dates_utils
from ..data_loader import data_loader
from ..symbols import symbols

def retrieve_signs(
    symbol: str,
    start_date: str,
    end_date: str,
) -> List[int]:
    general_utils.check_condition(symbols.is_symbol_valid(symbol),
                                  Exception(f"The symbol {symbol} doesn't exist, please use another one"))
    data = data_loader.load_data(symbol, "daily", start_date, end_date)
    signs = pyspark_utils.get_column_from_pyspark_df(data, column_name="epsilon", sort_column=["time", "id"])
    return signs

def extract_signs_from_data(
        data: DataFrame,
        start_date: str | None = None,
        end_date: str | None = None
) -> List[int]:
    if (start_date is not None and end_date is not None):
        dates_within_interval_udf = udf(lambda date: dates_utils.is_date_within_interval(date, start_date, end_date), BooleanType())
        data = data.filter(dates_within_interval_udf(F.col("date")))
    signs = pyspark_utils.get_column_from_pyspark_df(data, column_name="epsilon", sort_column=["time", "id"])
    return signs

