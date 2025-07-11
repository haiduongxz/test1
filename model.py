import xgboost as xgb
import joblib
import pandas as pd
import gdown
import io
import os
from binance_api import get_ohlcv
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from dotenv import load_dotenv
from functools import lru_cache

load_dotenv()
MODEL_FILE_ID = os.getenv("MODEL_FILE_ID")
gauth = GoogleAuth()
gauth.LocalWebserverAuth()  # mở trình duyệt để xác thực lần đầu
drive = GoogleDrive(gauth)


# def get_authenticated_drive():
#     gauth = GoogleAuth()

#     # Tìm file token đã xác thực trước đó
#     gauth.LoadCredentialsFile("client_secrets.json")

#     if gauth.credentials is None:
#         raise Exception("❌ Google Drive chưa được xác thực OAuth.")
#     elif gauth.access_token_expired:
#         gauth.Refresh()
#     else:
#         gauth.Authorize()

#     gauth.SaveCredentialsFile("client_secrets.json")
#     return GoogleDrive(gauth)


def upload_model_to_drive(model, filename="model.xgb"):
    try:
        buffer = io.BytesIO()
        joblib.dump(model, buffer)
        buffer.seek(0)

        # drive = get_authenticated_drive()
        gfile = drive.CreateFile({"title": filename})
        gfile.SetContentString(buffer.getvalue(), encoding="ISO-8859-1")
        gfile.Upload()
        print(f"✅ Model uploaded to Google Drive as '{filename}'")
    except Exception as e:
        print(f"❌ Failed to upload model: {e}")


@lru_cache(maxsize=1)
def load_model_from_drive():
    url = f"https://drive.google.com/uc?id={MODEL_FILE_ID}"
    output = io.BytesIO()

    try:
        print(f"📥 Tải model từ: {url}")
        gdown.download(url, output, quiet=False)
        output.seek(0)
        model = joblib.load(output)
        print("✅ Model loaded from Google Drive (memory only)")
        return model
    except Exception as e:
        print(f"❌ Failed to load model: {e.__class__.__name__}: {e}")
        return None


def add_technical_indicators(df):
    df["EMA_10"] = df["close"].ewm(span=10, adjust=False).mean()

    delta = df["close"].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / avg_loss
    df["RSI_14"] = 100 - (100 / (1 + rs))

    df["pct_change"] = df["close"].pct_change()
    df.fillna(0, inplace=True)
    return df


def create_features_and_labels(df):
    feature_cols = [
        "open",
        "high",
        "low",
        "close",
        "volume",
        "EMA_10",
        "RSI_14",
        "pct_change",
    ]
    df["close_next"] = df["close"].shift(-1)
    df["label"] = (df["close_next"] > df["close"]).astype(int)
    df.dropna(inplace=True)

    X = df[feature_cols]
    y = df["label"]
    return X, y


def train_model(X, y):
    model = xgb.XGBClassifier(
        # use_label_encoder=False,
        n_estimators=100,
        max_depth=4,
        learning_rate=0.1,
        eval_metric="logloss",
    )
    model.fit(X, y)
    return model


def predict_and_trade(symbol="BTCUSDT"):
    print(f"🔍 Predicting for {symbol}...")
    model = load_model_from_drive()
    if model is None:
        print("❌ Không thể load model.")
        return

    df = get_ohlcv(symbol, interval="1m", limit=100)
    df = add_technical_indicators(df)
    X, _ = create_features_and_labels(df)

    if X.empty:
        print("❌ Not enough data to predict.")
        return

    last_row = X.iloc[[-1]]
    prediction = model.predict(last_row)[0]

    if prediction == 1:
        print(f"🟢 {symbol}: BUY signal!")
    elif prediction == 0:
        print(f"🔴 {symbol}: SELL signal!")
    else:
        print(f"⚪ {symbol}: HOLD signal.")
