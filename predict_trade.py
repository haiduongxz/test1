import schedule
import time
from model import predict_and_trade
from binance_api import get_all_symbols

symbols = get_all_symbols()

for symbol in symbols:
    schedule.every(1).minutes.do(lambda s=symbol: predict_and_trade(s))

while True:
    schedule.run_pending()
    time.sleep(1)
