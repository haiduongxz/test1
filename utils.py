# utils_postgres.py

import pandas as pd
import os
import matplotlib.pyplot as plt
import ta
import glob
from datetime import datetime
from sqlalchemy import create_engine
from config import PG_CONN_STRING  # PostgreSQL connection string

# Kết nối đến PostgreSQL qua SQLAlchemy
engine = create_engine(PG_CONN_STRING)


def log(msg):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")


def save_to_db(symbol, df):
    """
    Lưu DataFrame vào PostgreSQL.
    """
    try:
        df.to_sql(symbol.lower(), engine, if_exists="append", index=False)
        log(f"✔ Lưu {symbol} vào database thành công.")
    except Exception as e:
        log(f"❌ Lỗi khi lưu {symbol} vào database: {e}")


def save_ohlcv_to_csv(data, filename, folder="data"):
    if not os.path.exists(folder):
        os.makedirs(folder)

    df = pd.DataFrame(
        data,
        columns=[
            "timestamp",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "close_time",
            "quote_asset_volume",
            "number_of_trades",
            "taker_buy_base_vol",
            "taker_buy_quote_vol",
            "ignore",
        ],
    )

    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df["close_time"] = pd.to_datetime(df["close_time"], unit="ms")

    path = os.path.join(folder, filename)
    df.to_csv(path, index=False)
    print(f"Saved {path}")


def load_all_excel_logs():
    all_files = glob.glob("excel_logs/*.csv")
    dfs = []
    for file in all_files:
        try:
            df = pd.read_csv(file)
            dfs.append(df)
        except Exception as e:
            print(f"❌ Không thể đọc file {file}: {e}")
    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()


def find_top_movers(data_folder="data"):
    results = []
    for file in os.listdir(data_folder):
        if file.endswith("_1h.csv"):
            df = pd.read_csv(os.path.join(data_folder, file))
            if len(df) >= 2:
                try:
                    change = (
                        (float(df["close"].iloc[-1]) - float(df["open"].iloc[0]))
                        / float(df["open"].iloc[0])
                        * 100
                    )
                    results.append((file.replace("_1h.csv", ""), round(change, 2)))
                except:
                    continue
    results.sort(key=lambda x: x[1], reverse=True)
    return results[:10]


def plot_price(file):
    df = pd.read_csv(file)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    plt.plot(df["timestamp"], df["close"], label="Close Price")
    plt.title(file)
    plt.xlabel("Time")
    plt.ylabel("Price")
    plt.legend()
    plt.show()


def add_indicators(df):
    df["rsi"] = ta.momentum.RSIIndicator(df["close"]).rsi()
    df["ema_20"] = ta.trend.EMAIndicator(df["close"], window=20).ema_indicator()
    df["macd"] = ta.trend.MACD(df["close"]).macd()
    return df
