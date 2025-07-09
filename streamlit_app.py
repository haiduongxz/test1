import streamlit as st
from dashboard import show_dashboard
from chat_ai import show_chat_ai
from watchlist import show_watchlist
from binance_api import get_all_symbols

st.set_page_config(page_title="Crypto Bot", layout="wide")
st.sidebar.title("📌 Chọn chức năng")

tab = st.sidebar.radio("Đi đến", ["Dashboard", "Chat AI", "Theo dõi Coin"])
symbols = get_all_symbols()
if tab == "Dashboard":
    show_dashboard(symbols)
elif tab == "Chat AI":
    show_chat_ai(symbols)
elif tab == "Theo dõi Coin":
    show_watchlist(symbols)
