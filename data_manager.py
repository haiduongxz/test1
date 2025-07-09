import sqlite3
import pandas as pd
from config import DB_PATH
import time
from binance_api import (
    get_ohlcv,
)  # Bạn cần phải tạo file binance_api.py với các hàm lấy dữ liệu từ Binance API
from config import SLEEP_BETWEEN_REQUESTS  # Tùy chỉnh thời gian chờ giữa các request


def crawl_and_save_batch(symbols):
    """
    Lấy dữ liệu OHLCV từ Binance cho một nhóm các cặp giao dịch và lưu vào cơ sở dữ liệu.

    :param symbols: Danh sách các cặp giao dịch cần lấy dữ liệu
    """
    errors = []
    intervals = [
        "1m",
        "5m",
        "15m",
        "1h",
        "4h",
        "1d",
    ]  # Các khoảng thời gian cần lấy dữ liệu

    for interval in intervals:
        for i, symbol in enumerate(symbols, 1):
            try:
                print(f"[{i}/{len(symbols)}] Fetching {symbol} {interval} data...")
                ohlcv = get_ohlcv(symbol, interval=interval, limit=1000)
                save_ohlcv_to_db(symbol, ohlcv)
                print(f"✔ Saved {symbol} {interval}")
            except Exception as e:
                print(f"✖ Error {symbol} {interval}: {e}")
                errors.append(f"{symbol}_{interval}")

            time.sleep(SLEEP_BETWEEN_REQUESTS)

    # for i, symbol in enumerate(symbols, 1):
    #     try:
    #         print(f"[{i}/{len(symbols)}] Fetching {symbol} data...")
    #         ohlcv = get_ohlcv(
    #             symbol, interval="1m", limit=500
    #         )  # Giới hạn lấy 500 cây nến gần nhất
    #         save_ohlcv_to_db(symbol, ohlcv)  # Lưu dữ liệu vào DB
    #         print(f"✔ Saved {symbol}")
    #     except Exception as e:
    #         print(f"✖ Error {symbol}: {e}")
    #         errors.append(symbol)

    #     time.sleep(
    #         SLEEP_BETWEEN_REQUESTS
    #     )  # Giới hạn thời gian giữa các request để tránh quá tải API

    # if errors:
    #     print(f"Retry failed symbols later: {errors}")


# Tạo bảng ohlcv nếu chưa tồn tại trong cơ sở dữ liệu
def create_table_if_not_exists():
    conn = sqlite3.connect(DB_PATH)
    query = """
    CREATE TABLE IF NOT EXISTS ohlcv (
        symbol TEXT,
        open_time INTEGER,
        open REAL,
        high REAL,
        low REAL,
        close REAL,
        volume REAL,
        close_time INTEGER,
        quote_asset_volume REAL,
        number_of_trades INTEGER,
        taker_buy_base_volume REAL,
        taker_buy_quote_volume REAL,
        PRIMARY KEY (symbol, open_time)
    )
    """
    conn.execute(query)
    conn.commit()
    conn.close()


# Lưu dữ liệu OHLCV vào cơ sở dữ liệu SQLite
def save_ohlcv_to_db(symbol, ohlcv_data):
    conn = sqlite3.connect(DB_PATH)
    records = [
        (
            symbol,
            int(row[0]),  # open_time
            float(row[1]),  # open
            float(row[2]),  # high
            float(row[3]),  # low
            float(row[4]),  # close
            float(row[5]),  # volume
            int(row[6]),  # close_time
            float(row[7]),  # quote_asset_volume
            int(row[8]),  # number_of_trades
            float(row[9]),  # taker_buy_base_volume
            float(row[10]),  # taker_buy_quote_volume
        )
        for row in ohlcv_data
    ]
    query = """
    INSERT OR IGNORE INTO ohlcv (
        symbol, open_time, open, high, low, close, volume, close_time,
        quote_asset_volume, number_of_trades, taker_buy_base_volume, taker_buy_quote_volume
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    conn.executemany(query, records)
    conn.commit()
    conn.close()


# Tải dữ liệu OHLCV của nhiều symbol từ cơ sở dữ liệu
def load_data_multi_symbols(symbols):
    conn = sqlite3.connect(DB_PATH)
    dfs = []
    for sym in symbols:
        df = pd.read_sql_query(
            f"SELECT * FROM ohlcv WHERE symbol = '{sym}' ORDER BY open_time", conn
        )
        # Chuyển đổi cột 'open_time' thành datetime
        df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
        df["symbol"] = sym  # Gắn thêm cột symbol để phân biệt giữa các symbol
        dfs.append(df)
    conn.close()
    # Trả về dữ liệu đã được kết hợp từ tất cả các symbol
    return pd.concat(dfs, ignore_index=True)
