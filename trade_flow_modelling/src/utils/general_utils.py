def is_symbol_in_file_path(symbol: str, file_path: str) -> bool:
    return symbol in file_path

def check_condition(condition: bool, exception: Exception):
    if (not condition):
        raise exception
