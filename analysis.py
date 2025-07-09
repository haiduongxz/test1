import pandas as pd


# Hàm lấy stats từ SQLite
def get_coin_stats(conn, symbol):
    # Truy vấn dữ liệu OHLCV cho biểu tượng (symbol) đã cho
    query = """
    SELECT open_time, open, high, low, close, volume, taker_buy_base_volume
    FROM ohlcv WHERE symbol = ? ORDER BY open_time DESC LIMIT 1000
    """
    df = pd.read_sql_query(query, conn, params=(symbol,))

    # Nếu dữ liệu không tồn tại (rỗng), trả về None
    if df.empty:
        return None

    # Sắp xếp dữ liệu theo thứ tự thời gian tăng dần (từ quá khứ đến hiện tại)
    df = df.iloc[::-1]

    # Tính toán các chỉ số
    avg_volume = df["volume"].mean()
    volatility = df["close"].pct_change().std()  # Độ lệch chuẩn của sự biến động giá %
    price_growth = (df["close"].iloc[-1] - df["close"].iloc[0]) / df["close"].iloc[0]
    buy_ratio = (
        df["taker_buy_base_volume"].sum() / df["volume"].sum()
        if df["volume"].sum() != 0
        else 0
    )

    # Tính tỷ lệ phần trăm nến tăng / nến giảm
    up_candles = (df["close"] > df["open"]).sum()
    down_candles = (df["close"] < df["open"]).sum()
    total_candles = len(df)

    # Tính tỷ lệ thắng và tỷ lệ thua
    win_rate = up_candles / total_candles if total_candles > 0 else 0
    loss_rate = down_candles / total_candles if total_candles > 0 else 0

    # Trả về các chỉ số đã tính toán dưới dạng từ điển
    return {
        "symbol": symbol,
        "avg_volume": avg_volume,
        "volatility": volatility,
        "price_growth": price_growth,
        "buy_ratio": buy_ratio,
        "win_rate": win_rate,
        "loss_rate": loss_rate,
    }


def select_top_coins(conn, symbols, top_n=20):
    stats = []
    for s in symbols:
        data = get_coin_stats(conn, s)
        if data:
            stats.append(data)

    df_stats = pd.DataFrame(stats)
    df_stats = df_stats.sort_values(
        by=["avg_volume", "price_growth"], ascending=[False, False]
    )
    return df_stats.head(top_n)
