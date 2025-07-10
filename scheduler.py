import time
import schedule
from model import train_model, upload_model_to_drive, load_model_from_drive
from data_manager import (
    crawl_and_save_batch,
    load_data_multi_symbols,
    create_table_if_not_exists,
)
from binance_api import get_all_symbols
from config import SYMBOLS_LIMIT
from utils import log
import pandas as pd
from model import (
    add_technical_indicators,
    create_features_and_labels,
)  # Import missing functions

create_table_if_not_exists()


def retrain_model():
    log("Retraining model...")

    # Crawl data
    selected_symbols = get_all_symbols()
    log(f"Selected symbols: {selected_symbols}")

    # Load and prepare data
    df_all = load_data_multi_symbols(selected_symbols)
    all_X = []
    all_y = []

    for sym in selected_symbols:
        df_sym = df_all[df_all["symbol"] == sym].copy()
        # Add technical indicators and create features
        df_sym = add_technical_indicators(df_sym)
        X, y = create_features_and_labels(df_sym)
        all_X.append(X)
        all_y.append(y)

    X_train = pd.concat(all_X)
    y_train = pd.concat(all_y)

    # Train the model
    model = train_model(X_train, y_train)

    # Save the trained model
    upload_model_to_drive(model)


# Schedule training every day at midnight
schedule.every().day.at("00:00").do(retrain_model)

if __name__ == "__main__":
    retrain_model()  # Run the model training immediately on the first start
    while True:
        schedule.run_pending()  # Run pending scheduled jobs
        time.sleep(10)  # Sleep to prevent high CPU usage
