import streamlit as st
import pandas as pd
import time
import requests
from datetime import datetime
from model import load_model, add_technical_indicators, create_features_and_labels
from pathlib import Path
from utils import load_all_excel_logs
from crypto_advisor import ask_gpt, get_rss_articles, load_saved_articles
import json

REFRESH_INTERVAL = 350
model = load_model()
session = requests.Session()
session.mount("https://", requests.adapters.HTTPAdapter(max_retries=3))


def get_ohlcv(symbol, interval="1m", limit=100):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    response = session.get(url, timeout=15)
    raw = response.json()
    df = pd.DataFrame(
        raw,
        columns=[
            "timestamp",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "close_time",
            "quote_asset_volume",
            "number_of_trades",
            "taker_buy_base_asset_volume",
            "taker_buy_quote_asset_volume",
            "ignore",
        ],
    )
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df.set_index("timestamp", inplace=True)
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = df[col].astype(float)
    return df[["open", "high", "low", "close", "volume"]]


def get_signal(symbol):
    try:
        df = get_ohlcv(symbol)
        df = add_technical_indicators(df)
        X, _ = create_features_and_labels(df)
        if X.empty:
            return "NO DATA"
        pred = model.predict(X.iloc[[-1]])[0]
        return "BUY" if pred == 1 else "SELL" if pred == -1 else "HOLD"
    except Exception:
        return "ERROR"


@st.cache_data
def load_all_excel_logs_cached():
    return load_all_excel_logs()


def get_article_news():
    rss_url = "https://www.coindesk.com/arc/outboundfeeds/rss/"
    headers = {"User-Agent": "Mozilla/5.0"}
    new_articles = get_rss_articles(rss_url, headers=headers)
    saved_articles = load_saved_articles()
    saved_titles = {item["title"] for item in saved_articles}
    combined_articles = saved_articles.copy()
    for title in new_articles:
        if title not in saved_titles:
            combined_articles.append(
                {"date": datetime.now().strftime("%Y-%m-%d"), "title": title}
            )
    with open("articles.json", "w", encoding="utf-8") as f:
        json.dump(combined_articles, f, ensure_ascii=False, indent=2)
    return combined_articles


def build_gpt_prompt(df_latest, df_all_history, articles):
    latest_signals = df_latest[["Symbol", "Signal"]].to_dict(orient="records")
    summary_signals = "\n".join(
        f"- {item['Symbol']}: {item['Signal']}" for item in latest_signals
    )
    signal_stats = df_all_history["Signal"].value_counts().to_dict()
    signal_summary = ", ".join([f"{k}: {v}" for k, v in signal_stats.items()])
    recent_news = "\n".join(
        f"- [{item['date']}] {item['title']}" for item in articles[-20:]
    )

    return f"""
Bạn là một chuyên gia phân tích đầu tư Crypto với hơn 10 năm kinh nghiệm. Hãy đóng vai trò là cố vấn đầu tư chuyên nghiệp, đưa ra nhận định chắc chắn với độ chính xác tối thiểu 75%.

---

🧠 **Phân tích kỹ thuật — Dữ liệu từ mô hình AI (tín hiệu mới nhất):**
{summary_signals}

📊 **Thống kê lịch sử tín hiệu gần đây (toàn bộ dữ liệu):**
{signal_summary}

📰 **Tin tức Crypto gần đây (bài viết mới nhất):**
{recent_news}

---

🎯 **Yêu cầu:**
- Dựa vào dữ liệu kỹ thuật và tin tức thị trường trên, hãy phân tích xu hướng tổng thể của thị trường crypto hiện tại.
- Đưa ra nhận định rõ ràng với độ tin cậy cao về những coin nên **MUA**, những coin nên **BÁN**.
- Đưa lý do ngắn gọn, dựa trên các yếu tố kỹ thuật hoặc tin tức liên quan.
- Trình bày theo định dạng:
  - 🔼 **MUA**: ...
  - 🔽 **BÁN**: ...
  - 📌 **Giải thích**: ...

Chỉ phản hồi dưới dạng phân tích đầu tư, không cần giải thích thêm về vai trò của bạn.
"""


def show_dashboard(symbols):
    st.title("📈 Crypto Bot Dashboard")

    if "history" not in st.session_state:
        st.session_state.history = []

    with st.spinner("🚀 Đang lấy tín hiệu..."):
        results = [{"Symbol": sym, "Signal": get_signal(sym)} for sym in symbols]

    df_result = pd.DataFrame(results)
    df_result["Color"] = df_result["Signal"].map(
        {"BUY": "🟢", "SELL": "🔴", "HOLD": "⚪", "NO DATA": "⚫", "ERROR": "❌"}
    )
    df_result["Hiển thị"] = df_result["Color"] + " " + df_result["Symbol"]
    df_result["Thời gian"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    df_result["SortOrder"] = df_result["Signal"].map(
        {"BUY": 0, "SELL": 1, "HOLD": 2, "NO DATA": 3, "ERROR": 4}
    )
    df_result.sort_values("SortOrder", inplace=True)

    output_dir = Path("excel_logs")
    output_dir.mkdir(exist_ok=True)
    filename = datetime.now().strftime("crypto_signals_%Y-%m-%d_%H-%M-%S.csv")
    df_result.to_csv(output_dir / filename, index=False)
    st.session_state.history.insert(0, df_result)

    df_all_history = load_all_excel_logs_cached()
    articles = get_article_news()
    if not df_all_history.empty and articles:
        prompt = build_gpt_prompt(df_result, df_all_history, articles)
        analysis_result = ask_gpt(prompt)
        with st.expander("📈 Đề xuất phân tích từ AI"):
            st.markdown(analysis_result)

    st.subheader("📊 Lịch sử tín hiệu")
    for i, df in enumerate(st.session_state.history):
        with st.expander(
            f"📌 Cập nhật {i + 1} — {df['Thời gian'].iloc[0]}", expanded=(i == 0)
        ):
            counts = df["Signal"].value_counts()
            st.markdown(
                f"""
                - 🟢 BUY: {counts.get("BUY", 0)}
                - 🔴 SELL: {counts.get("SELL", 0)}
                - ⚪ HOLD: {counts.get("HOLD", 0)}
                - ⚫ NO DATA: {counts.get("NO DATA", 0)}
                - ❌ ERROR: {counts.get("ERROR", 0)}
                """
            )
            st.dataframe(df[["Hiển thị", "Signal"]], use_container_width=True)

    countdown = st.empty()
    progress_bar = st.progress(0)
    for sec in range(REFRESH_INTERVAL):
        countdown.markdown(f"🔄 Cập nhật sau: `{REFRESH_INTERVAL - sec} giây`")
        progress_bar.progress((sec + 1) / REFRESH_INTERVAL)
        time.sleep(1)

    st.rerun()
