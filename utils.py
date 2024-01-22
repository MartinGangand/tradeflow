from pyspark.sql import SparkSession

def get_spark_session():
    spark = SparkSession.builder\
                        .appName(__name__)\
                        .config('spark.sql.session.timeZone', 'UTC')\
                        .getOrCreate()
    return spark

def get_column_from_pyspark_df(pyspark_df, column_name, sort_column=None):
    if (sort_column is not None):
        return pyspark_df.sort(sort_column).select(column_name).rdd.flatMap(lambda x: x).collect()
    else:
        return pyspark_df.select(column_name).rdd.flatMap(lambda x: x).collect()
    
def is_symbol_in_file_path(symbol: str, file_path: str) -> bool:
    return symbol in file_path