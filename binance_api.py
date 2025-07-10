import requests

BASE_URL = "https://api.binance.com"


def get_exchange_info():
    url = f"{BASE_URL}/api/v3/exchangeInfo"
    response = requests.get(url, timeout=10)

    print("Status code:", response.status_code)
    print("Response content:", response.text[:500])  # In ra 500 ký tự đầu
    return response.json()


# def get_all_symbols():
#     data = get_exchange_info()
#     return [s["symbol"] for s in data["symbols"] if s["status"] == "TRADING"]


def get_all_symbols():
    data = get_exchange_info()
    if "symbols" not in data:
        print("Không lấy được dữ liệu từ Binance. Có thể bị chặn IP.")
        return []
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


def get_ohlcv(symbol, interval="1h", limit=1000):
    url = f"{BASE_URL}/api/v3/klines"
    params = {
        "symbol": symbol.upper(),
        "interval": interval,
        "limit": limit,
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()  # Nếu mã HTTP lỗi thì raise luôn
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Lỗi khi gọi OHLCV {symbol} {interval}: {e}")
        return []
