# model.py

import xgboost as xgb
import joblib
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from config import MODEL_PATH
from binance_api import get_ohlcv


def add_technical_indicators(df):
    """
    Thêm các chỉ báo kỹ thuật vào DataFrame bao gồm EMA, RSI, và % thay đổi giá đóng cửa.

    :param df: DataFrame chứa dữ liệu OHLCV của một cặp giao dịch
    :return: DataFrame với các chỉ báo kỹ thuật được thêm vào
    """

    # 1. Exponential Moving Average (EMA) với chu kỳ 10
    df["EMA_10"] = df["close"].ewm(span=10, adjust=False).mean()

    # 2. Relative Strength Index (RSI) với chu kỳ 14
    delta = df["close"].diff()
    gain = delta.where(
        delta > 0, 0
    )  # Nếu có lãi (giá tăng) thì giữ lại, nếu không thì cho giá trị 0
    loss = -delta.where(
        delta < 0, 0
    )  # Nếu có lỗ (giá giảm) thì giữ lại, nếu không thì cho giá trị 0
    avg_gain = gain.rolling(window=14).mean()  # Trung bình động của lãi
    avg_loss = loss.rolling(window=14).mean()  # Trung bình động của lỗ
    rs = avg_gain / avg_loss  # Tính tỷ lệ của lãi và lỗ
    df["RSI_14"] = 100 - (100 / (1 + rs))  # Tính RSI theo công thức chuẩn

    # 3. Tính % thay đổi của giá đóng cửa
    df["pct_change"] = df[
        "close"
    ].pct_change()  # Thay đổi theo phần trăm giữa các giá đóng cửa

    # 4. Điền giá trị NaN bằng 0 (tránh lỗi khi tính toán)
    df.fillna(0, inplace=True)

    return df


def train_model(X, y):
    model = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=4,
        learning_rate=0.1,
        eval_metric="logloss",
    )
    model.fit(X, y)
    return model


def create_features_and_labels(df):
    """
    Tạo các đặc trưng (features) và nhãn (labels) từ dữ liệu OHLCV.

    :param df: DataFrame chứa dữ liệu OHLCV đã được tính các chỉ báo kỹ thuật
    :return: X (các đặc trưng), y (nhãn)
    """

    # Các cột đặc trưng (features)
    feature_cols = [
        "open",  # Giá mở cửa
        "high",  # Giá cao nhất
        "low",  # Giá thấp nhất
        "close",  # Giá đóng cửa
        "volume",  # Khối lượng giao dịch
        "EMA_10",  # Exponential Moving Average (EMA) với chu kỳ 10
        "RSI_14",  # Relative Strength Index (RSI) với chu kỳ 14
        "pct_change",  # Tỷ lệ thay đổi giá đóng cửa
    ]

    # Tạo nhãn: Dự đoán giá đóng cửa của kỳ tiếp theo có lớn hơn kỳ hiện tại không?
    df["close_next"] = df["close"].shift(-1)  # Dịch giá đóng cửa của kỳ tiếp theo
    df["label"] = (df["close_next"] > df["close"]).astype(
        int
    )  # Nếu đóng cửa tiếp theo lớn hơn => Label = 1, ngược lại là 0

    df.dropna(inplace=True)  # Loại bỏ các dòng có giá trị NaN (do shift)

    # Tạo các đặc trưng (X) và nhãn (y)
    X = df[feature_cols]  # Các đặc trưng
    y = df["label"]  # Nhãn (label)

    return X, y


def save_model(model):
    joblib.dump(model, MODEL_PATH)
    print(f"Model saved to {MODEL_PATH}")


def load_model():
    try:
        model = joblib.load(MODEL_PATH)
        print(f"Model loaded from {MODEL_PATH}")
        return model
    except Exception as e:
        print(f"Error loading model: {e}")
        return None


def predict_and_trade(symbol="BTCUSDT"):
    print(f"🔍 Predicting for {symbol}...")

    # 1. Load model
    model = load_model()

    # 2. Lấy dữ liệu mới
    df = get_ohlcv(symbol, interval="1m", limit=100)
    df = add_technical_indicators(df)

    # 3. Tạo feature (X) như lúc train
    X, _ = create_features_and_labels(df)

    if X.empty:
        print("❌ Not enough data to predict.")
        return

    # 4. Lấy hàng cuối cùng để predict
    last_row = X.iloc[[-1]]
    prediction = model.predict(last_row)[0]

    # 5. Hiển thị kết quả
    if prediction == 1:
        print(f"🟢 {symbol}: BUY signal!")
    elif prediction == -1:
        print(f"🔴 {symbol}: SELL signal!")
    else:
        print(f"⚪ {symbol}: HOLD signal.")
