from fastapi import FastAPI
from scheduler import retrain_model  # Giả sử mã bạn đưa nằm trong file retrain.py
from utils import log
from data_manager import crawl_and_save_batch
from fastapi.responses import JSONResponse
from binance_api import get_all_symbols
from dashboard import get_ohlcv
from model import (
    load_model_from_drive,
    add_technical_indicators,
    create_features_and_labels,
)
import time
from utils import save_signals_to_db
from datetime import datetime
from sqlalchemy import text
from sqlalchemy import (
    create_engine,
)
from config import PG_CONN_STRING

engine = create_engine(PG_CONN_STRING)
app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "Model retraining API is running."}


def get_signal(symbol: str, model):
    try:
        df = get_ohlcv(symbol)
        df = add_technical_indicators(df)
        X, _ = create_features_and_labels(df)
        if X.empty:
            return "NO DATA"
        pred = model.predict(X.iloc[[-1]])[0]
        return "BUY" if pred == 1 else "SELL" if pred == -1 else "HOLD"
    except Exception as e:
        print(f"Lỗi khi xử lý symbol {symbol}: {e}")
        return "ERROR"


@app.post("/generate-and-save-signals")
def generate_and_save_signals():
    try:
        model = load_model_from_drive()
        if model is None:
            return {"status": "error", "message": "Không thể tải model"}

        symbols = get_all_symbols()
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        values = []
        result_list = []

        for symbol in symbols:
            signal = get_signal(symbol, model)
            values.append((symbol, signal, current_time))
            result_list.append(
                {"Symbol": symbol, "Signal": signal, "Thời gian": current_time}
            )
            time.sleep(0.5)

        save_signals_to_db(values)

        return {
            "status": "success",
            "message": "Signals generated and saved successfully",
            "data": result_list,
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/crawl")
def crawl_data():
    try:
        crawl_and_save_batch(get_all_symbols())
        return {"status": "success", "message": "Data crawled successfully"}
    except Exception as e:
        print(f"❌ Lỗi crawl: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": "Crawl failed", "detail": str(e)},
        )


def clean_old_data():
    with engine.begin() as conn:
        conn.execute(
            text(
                """
            DELETE FROM ohlcv
            WHERE open_time < EXTRACT(EPOCH FROM NOW() - INTERVAL '7 days') * 1000
        """
            )
        )


@app.post("/train-bot-coins")
def train():
    try:
        clean_old_data()
        retrain_model()
        return {"status": "success", "message": "Model trained successfully"}
    except Exception as e:
        print(f"❌ Lỗi train: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": "Training failed", "detail": str(e)},
        )
