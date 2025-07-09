import streamlit as st
from datetime import datetime
from crypto_advisor import ask_gpt
from utils import load_all_excel_logs
import json


def show_chat_ai(symbols):
    st.header("🤖 Hỏi AI về vị thế đầu tư của bạn")

    # Load lịch sử tín hiệu & tin tức
    df_all_history = load_all_excel_logs()
    with open("articles.json", "r", encoding="utf-8") as f:
        articles = json.load(f)

    with st.form("investment_form"):
        col1, col2 = st.columns(2)
        with col1:
            coin_input = st.selectbox("🔍 Coin bạn đã mua", symbols, key="coin_input")
            price_input = st.text_input(
                "💰 Giá bạn đã mua (USDT)", "", key="price_input"
            )
        with col2:
            date_input = st.date_input(
                "📅 Ngày bạn mua", datetime.today(), key="date_input"
            )
            strategy = st.selectbox(
                "🎯 Phong cách đầu tư",
                ["Ngắn hạn", "Trung hạn", "Dài hạn"],
                key="strategy",
            )

        user_question = st.text_area(
            "✏️ Câu hỏi cụ thể (nếu có)",
            placeholder="Tôi nên bán bây giờ không?",
            key="user_question",
        )
        submitted = st.form_submit_button("📤 Gửi yêu cầu phân tích")

    if submitted:
        try:
            signal_stats = df_all_history["Signal"].value_counts().to_dict()
            signal_summary = ", ".join([f"{k}: {v}" for k, v in signal_stats.items()])

            recent_news = "\n".join(
                f"- [{item['date']}] {item['title']}" for item in articles[-20:]
            )

            prompt = f"""
Tôi đã mua {coin_input} với giá {price_input} USDT vào ngày {date_input.strftime('%Y-%m-%d')}.
Tôi đang đầu tư theo phong cách {strategy}.
Câu hỏi: {user_question or "Tôi nên giữ hay bán?"}

---

📊 **Thống kê lịch sử tín hiệu gần đây (toàn bộ dữ liệu):**
{signal_summary}

📰 **Tin tức Crypto gần đây (bài viết mới nhất):**
{recent_news}

---

🎯 **Yêu cầu:**
- Dựa vào dữ liệu trên và thông tin cá nhân tôi cung cấp, hãy đánh giá liệu tôi nên giữ, bán, hay mua thêm coin {coin_input}.
- Trình bày theo định dạng:
  - ✅ Khuyến nghị: ...
  - 💬 Giải thích: ...
            """

            with st.spinner("🤖 AI đang phân tích, vui lòng chờ..."):
                reply = ask_gpt(prompt)

            st.success("✅ Phân tích từ AI:")
            st.info(reply)

        except Exception as e:
            st.error(f"Lỗi: {e}")
