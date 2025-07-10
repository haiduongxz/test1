from sqlalchemy import (
    create_engine,
    Table,
    Column,
    String,
    BigInteger,
    Float,
    Integer,
    MetaData,
)
from sqlalchemy.dialects.postgresql import insert as pg_insert
import pandas as pd
import time
from binance_api import get_ohlcv
from config import SLEEP_BETWEEN_REQUESTS, PG_CONN_STRING
from concurrent.futures import ThreadPoolExecutor, as_completed

# Constants
MAX_WORKERS = 5
INTERVALS = ["15m", "1h", "4h"]

engine = create_engine(PG_CONN_STRING)
metadata = MetaData()

# ✅ Thêm cột `interval`
ohlcv_table = Table(
    "ohlcv",
    metadata,
    Column("symbol", String, primary_key=True),
    Column("interval", String, primary_key=True),
    Column("open_time", BigInteger, primary_key=True),
    Column("open", Float),
    Column("high", Float),
    Column("low", Float),
    Column("close", Float),
    Column("volume", Float),
    Column("close_time", BigInteger),
    Column("quote_asset_volume", Float),
    Column("number_of_trades", Integer),
    Column("taker_buy_base_volume", Float),
    Column("taker_buy_quote_volume", Float),
)


def create_table_if_not_exists():
    metadata.create_all(engine)


def save_ohlcv_to_db(symbol, interval, ohlcv_data):
    records = [
        {
            "symbol": symbol,
            "interval": interval,
            "open_time": int(row[0]),
            "open": float(row[1]),
            "high": float(row[2]),
            "low": float(row[3]),
            "close": float(row[4]),
            "volume": float(row[5]),
            "close_time": int(row[6]),
            "quote_asset_volume": float(row[7]),
            "number_of_trades": int(row[8]),
            "taker_buy_base_volume": float(row[9]),
            "taker_buy_quote_volume": float(row[10]),
        }
        for row in ohlcv_data
    ]

    if not records:
        return

    with engine.begin() as conn:
        stmt = (
            pg_insert(ohlcv_table)
            .values(records)
            .on_conflict_do_nothing(index_elements=["symbol", "interval", "open_time"])
        )
        conn.execute(stmt)


def load_data_multi_symbols(symbols):
    dfs = []
    with engine.connect() as conn:
        for sym in symbols:
            df = pd.read_sql_query(
                f"SELECT * FROM ohlcv WHERE symbol = %s ORDER BY open_time",
                conn,
                params=(sym,),
            )
            df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
            df["symbol"] = sym
            dfs.append(df)
    return pd.concat(dfs, ignore_index=True)


def crawl_and_save_batch(symbols):
    errors = []

    def fetch_and_save(symbol, interval):
        print(f"🔄 Processing {symbol} {interval} ...")
        try:
            print(f"📥 Fetching {symbol} {interval} ...")
            ohlcv = get_ohlcv(symbol, interval=interval, limit=1000)
            if ohlcv:
                save_ohlcv_to_db(symbol, interval, ohlcv)
                print(f"✅ Saved {symbol} {interval} ({len(ohlcv)} records)")
            else:
                print(f"⚠️ No data returned for {symbol} {interval}")
            return None
        except Exception as e:
            print(f"❌ Error {symbol} {interval}: {e}")
            return f"{symbol}_{interval}"

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = []
        for symbol in symbols:
            for interval in INTERVALS:
                futures.append(executor.submit(fetch_and_save, symbol, interval))
                time.sleep(SLEEP_BETWEEN_REQUESTS)

        for future in as_completed(futures):
            result = future.result()
            if result:
                errors.append(result)

    if errors:
        print("\n⚠️ Lỗi khi lấy dữ liệu các cặp sau:")
        for err in errors:
            print(" -", err)


create_table_if_not_exists()
