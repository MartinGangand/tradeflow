PROJECT_FOLDER = "/Users/martingangand/Documents/trade_flow_modelling"

DATA_FOLDER = f"{PROJECT_FOLDER}/data"
symbol_data_folder = lambda date_type, symbol: f"{DATA_FOLDER}/{date_type}/{symbol}"

EXTENSION = "csv"
PRECISION = 2