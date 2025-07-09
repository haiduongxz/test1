import streamlit as st
import pandas as pd
import plotly.express as px
from binance_api import get_ohlcv
from sqlalchemy import create_engine
from config import PG_CONN_STRING
from analysis import (
    select_top_coins,
)  # Đảm bảo dùng kết nối PostgreSQL bên trong hàm này

# Kết nối đến PostgreSQL
engine = create_engine(PG_CONN_STRING)


def show_watchlist(symbols):
    st.set_page_config(
        layout="wide", page_title="Theo dõi Coin Binance", page_icon="💰"
    )
    col1, col2 = st.columns([1, 3])

    with col1:
        with st.expander("Bộ lọc (Click để thu gọn/hiện)", expanded=True):
            st.title("Bộ lọc")
            symbol = st.selectbox(
                "Chọn đồng coin",
                symbols,
                help=f"Chọn coin bạn muốn xem ({len(symbols)} coin)",
            )
            interval = st.selectbox(
                "Chọn khung thời gian",
                ["1m", "5m", "15m", "1h", "4h", "1d", "1w"],
                index=3,
            )

            data_raw = get_ohlcv(symbol, interval, limit=1000)
            df_raw = pd.DataFrame(
                data_raw,
                columns=[
                    "Thời gian mở nến",
                    "Giá mở cửa",
                    "Giá cao nhất",
                    "Giá thấp nhất",
                    "Giá đóng cửa",
                    "Khối lượng giao dịch",
                    "Thời gian đóng nến",
                    "Khối lượng quy đổi USDT",
                    "Số lượng giao dịch",
                    "Khối lượng mua (base)",
                    "Khối lượng mua (USDT)",
                    "Bỏ qua",
                ],
            )
            df_raw["Thời gian mở nến"] = pd.to_datetime(
                df_raw["Thời gian mở nến"], unit="ms"
            )

            # Convert numeric columns
            num_cols = [
                "Giá mở cửa",
                "Giá cao nhất",
                "Giá thấp nhất",
                "Giá đóng cửa",
                "Khối lượng giao dịch",
                "Số lượng giao dịch",
                "Khối lượng mua (base)",
                "Khối lượng mua (USDT)",
                "Khối lượng quy đổi USDT",
            ]
            for col in num_cols:
                df_raw[col] = pd.to_numeric(df_raw[col], errors="coerce")

            # Các bộ lọc
            start_date = st.date_input(
                "Ngày bắt đầu", df_raw["Thời gian mở nến"].min().date()
            )
            end_date = st.date_input(
                "Ngày kết thúc", df_raw["Thời gian mở nến"].max().date()
            )
            if start_date > end_date:
                st.error("Ngày bắt đầu phải nhỏ hơn ngày kết thúc.")

            min_open, max_open = st.slider(
                "Khoảng giá mở cửa",
                float(df_raw["Giá mở cửa"].min()),
                float(df_raw["Giá mở cửa"].max()),
                (float(df_raw["Giá mở cửa"].min()), float(df_raw["Giá mở cửa"].max())),
                step=0.01,
            )
            min_close, max_close = st.slider(
                "Khoảng giá đóng cửa",
                float(df_raw["Giá đóng cửa"].min()),
                float(df_raw["Giá đóng cửa"].max()),
                (
                    float(df_raw["Giá đóng cửa"].min()),
                    float(df_raw["Giá đóng cửa"].max()),
                ),
                step=0.01,
            )
            min_vol, max_vol = st.slider(
                "Khối lượng giao dịch",
                float(df_raw["Khối lượng giao dịch"].min()),
                float(df_raw["Khối lượng giao dịch"].max()),
                (
                    float(df_raw["Khối lượng giao dịch"].min()),
                    float(df_raw["Khối lượng giao dịch"].max()),
                ),
                step=0.01,
            )
            min_trades = st.number_input(
                "Tối thiểu số lượng giao dịch", min_value=0, value=0, step=1
            )
            min_buy_base, max_buy_base = st.slider(
                "Khối lượng mua (base)",
                float(df_raw["Khối lượng mua (base)"].min()),
                float(df_raw["Khối lượng mua (base)"].max()),
                (
                    float(df_raw["Khối lượng mua (base)"].min()),
                    float(df_raw["Khối lượng mua (base)"].max()),
                ),
                step=0.01,
            )

            df_raw["Biến động"] = df_raw["Giá cao nhất"] - df_raw["Giá thấp nhất"]
            min_volatility, max_volatility = st.slider(
                "Biến động giá (High - Low)",
                float(df_raw["Biến động"].min()),
                float(df_raw["Biến động"].max()),
                (float(df_raw["Biến động"].min()), float(df_raw["Biến động"].max())),
                step=0.01,
            )

            num_rows = st.slider("Số dòng dữ liệu hiển thị", 10, 1000, 100)

    with col2:
        with st.spinner("Đang tải dữ liệu..."):
            all_symbols = [s for s in symbols if s.endswith("USDT")]
            with engine.connect() as conn:
                top_coins = select_top_coins(conn, all_symbols, top_n=20)

            if top_coins.empty:
                st.warning("Không có dữ liệu để hiển thị.")
            else:
                st.write("### Top 20 đồng coin nên đầu tư")
                st.dataframe(
                    top_coins[
                        [
                            "symbol",
                            "win_rate",
                            "loss_rate",
                            "avg_volume",
                            "volatility",
                            "price_growth",
                        ]
                    ],
                    use_container_width=True,
                )

        st.title("📊 Bảng điều khiển giá Coin Binance")

        df = df_raw[
            (df_raw["Thời gian mở nến"].dt.date >= start_date)
            & (df_raw["Thời gian mở nến"].dt.date <= end_date)
            & (df_raw["Giá mở cửa"] >= min_open)
            & (df_raw["Giá mở cửa"] <= max_open)
            & (df_raw["Giá đóng cửa"] >= min_close)
            & (df_raw["Giá đóng cửa"] <= max_close)
            & (df_raw["Khối lượng giao dịch"] >= min_vol)
            & (df_raw["Khối lượng giao dịch"] <= max_vol)
            & (df_raw["Số lượng giao dịch"] >= min_trades)
            & (df_raw["Khối lượng mua (base)"] >= min_buy_base)
            & (df_raw["Khối lượng mua (base)"] <= max_buy_base)
            & (df_raw["Biến động"] >= min_volatility)
            & (df_raw["Biến động"] <= max_volatility)
        ]

        if df.empty:
            st.warning("Không có dữ liệu phù hợp với bộ lọc.")
        else:
            fig = px.line(
                df,
                x="Thời gian mở nến",
                y="Giá đóng cửa",
                title=f"Biểu đồ giá {symbol}",
                hover_data=[
                    "Giá mở cửa",
                    "Giá cao nhất",
                    "Giá thấp nhất",
                    "Khối lượng giao dịch",
                ],
            )
            fig.update_layout(xaxis_title="Thời gian", yaxis_title="Giá đóng cửa")
            st.plotly_chart(fig, use_container_width=True)

            st.subheader(f"📋 Bảng dữ liệu ({num_rows} dòng mới nhất)")
            st.dataframe(
                df.tail(num_rows).reset_index(drop=True), use_container_width=True
            )
