from binance_api import get_all_symbols, get_price, get_ohlcv
from utils import save_ohlcv_to_csv
import time


def crawl_all():
    symbols = get_all_symbols()
    print(f"Found {len(symbols)} trading pairs.")
    for symbol in symbols:
        try:
            price = get_price(symbol)
            print(f"{symbol}: {price['price']}")

            ohlcv = get_ohlcv(symbol, interval="1h", limit=100)
            save_ohlcv_to_csv(ohlcv, f"{symbol}_1h.csv")

            time.sleep(0.2)  # Avoid rate limit
        except Exception as e:
            print(f"Error with {symbol}: {e}")


if __name__ == "__main__":
    crawl_all()
