import requests

BASE_URL = "https://api.binance.com"


def get_exchange_info():
    url = f"{BASE_URL}/api/v3/exchangeInfo"
    return requests.get(url).json()


# def get_all_symbols():
#     data = get_exchange_info()
#     return [s["symbol"] for s in data["symbols"] if s["status"] == "TRADING"]


def get_all_symbols():
    data = get_exchange_info()
    return [
        s["symbol"]
        for s in data["symbols"]
        if s["status"] == "TRADING" and s["symbol"].endswith("USDT")
    ]


def get_all_base_assets():
    data = get_exchange_info()
    return sorted(list(set(s["baseAsset"] for s in data["symbols"])))


def get_price(symbol):
    url = f"{BASE_URL}/api/v3/ticker/price"
    return requests.get(url, params={"symbol": symbol}).json()


def get_ohlcv(symbol, interval="1h", limit=5):
    url = f"{BASE_URL}/api/v3/klines"
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    return requests.get(url, params=params).json()
