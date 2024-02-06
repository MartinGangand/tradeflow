from pyspark.sql import SparkSession
from typing import List, Any

print("PYSPARK_UTILS")

def get_spark_session():
    spark = SparkSession.builder\
                        .appName(__name__)\
                        .config('spark.sql.session.timeZone', 'UTC')\
                        .config("spark.driver.memory", "10g")\
                        .config("spark.executor.memory", "10g")\
                        .getOrCreate()
    return spark
# .config("spark.driver.bindAddress", "127.0.0.1")\

def get_column_from_pyspark_df(pyspark_df, column_name: str, sort_column: str | List[str] | None = None) -> List[Any]:
    if (sort_column is not None):
        return pyspark_df.sort(sort_column).select(column_name).rdd.flatMap(lambda x: x).collect()
    else:
        return pyspark_df.select(column_name).rdd.flatMap(lambda x: x).collect()
    