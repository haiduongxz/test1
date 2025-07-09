# config.py
PG_CONN_STRING = "postgresql://crypto_db_wuvy_user:9kemWCUVQDgiCAI863bif4Fg8UmKfBUc@dpg-d1n9qbruibrs73c281ug-a.oregon-postgres.render.com/crypto_db_wuvy"
DB_PATH = "binance_data.db"
MODEL_PATH = "model.xgb"  # Path to save the model

# Request parameters
BATCH_SIZE = 50
SLEEP_BETWEEN_REQUESTS = 0.25
INTERVAL = "1m"
LIMIT_OHLCV = 500  # The amount of historical data to fetch per symbol

# List of symbols to train on
SYMBOLS_LIMIT = 20
