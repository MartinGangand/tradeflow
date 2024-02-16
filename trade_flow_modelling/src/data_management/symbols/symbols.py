from binance.client import Client

print("SYMBOLS")

def is_symbol_valid(symbol: str) -> bool:
    return True
    return symbol in all_symbols

def retrieve_all_symbols() -> set[str]:
    symbols = set([symbol["symbol"] for symbol in Client().get_all_tickers()])
    print(f"RETRIEVE ALL SYMBOLS ({len(symbols)})")
    return symbols

# all_symbols = retrieve_all_symbols()