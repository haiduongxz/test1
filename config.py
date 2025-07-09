# config.py

DB_PATH = "binance_data.db"
MODEL_PATH = "model.xgb"  # Path to save the model

# Request parameters
BATCH_SIZE = 50
SLEEP_BETWEEN_REQUESTS = 0.25
INTERVAL = "1m"
LIMIT_OHLCV = 500  # The amount of historical data to fetch per symbol

# List of symbols to train on
SYMBOLS_LIMIT = 20
