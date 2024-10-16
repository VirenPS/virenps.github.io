### Moving Average Dashboard
import datetime as dt

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf

# from Tools.streamlit_tools import plot_metric


def read_data(ticker, start_of_period="2020-01-01"):
    return yf.download(
        ticker,
        start=start_of_period,
        end=dt.datetime.now().date() + dt.timedelta(days=1),
    )


def run_dashboard():
    st.set_page_config(layout="wide", page_icon="📈")

    # Parameters required
    with st.sidebar:
        st.subheader("Parameters:")
        ticker = st.text_input("Ticker", "AMZN")
        start_of_period = dt.date(2020, 1, 1)

        date_range = st.slider(
            "Select your date range",
            min_value=start_of_period,
            max_value=dt.datetime.now().date() + dt.timedelta(days=1),
            value=(
                dt.date(2020, 1, 1),
                dt.datetime.now().date() + dt.timedelta(days=1),
            ),
            format="DD.MM.YYYY",
        )
        default_signal_tolerance = 5
        signal_tolerance = st.slider("Signal Tolerance", 0, 6, default_signal_tolerance)
    st.sidebar.text("")
    st.sidebar.markdown(
        """**Disclaimer**"""
        + "  "
        + """
        This dashboard is not personal investment advice. Data represented on charts is purely an illustration of dashboarding capabilities and may not be accurate. It **does not** constitute a personal recommendation to buy, sell, or otherwise trade all or any of the investments which may be referred to.
        """
    )

    df = read_data(ticker, start_of_period)
    # Run Analysis
    df = df.sort_index(inplace=False)
    last_price = round(df.tail(1)["Adj Close"].values[0], 2)
    last_date = str(df.tail(1).index.values[0])[0:10]

    # create 2 tabs
    analysis_tab, signals_tab = st.tabs(["Analysis", "Signals"])

    with analysis_tab:
        st.title(f"{ticker} Price vs Volume Trended")

        # Calculating the average values for "Adj Close" and "Volume"
        avg_adj_close = df["Adj Close"].mean()
        avg_volume = df["Volume"].mean()

        # Recreating the plot with average lines
        fig, ax1 = plt.subplots(figsize=(12, 6))

        # "Adj Close" on the primary axis
        ax1.plot(
            df["Adj Close"],
            label="Adj Close",
            color="blue",
        )
        ax1.axhline(
            y=avg_adj_close,
            color="blue",
            linestyle="--",
            label=f"Avg Adj Close: {avg_adj_close:.2f}",
        )
        ax1.set_xlabel("Date")
        ax1.set_ylabel("Adj Close", color="blue")
        ax1.tick_params(axis="y", labelcolor="blue")

        # "Volume" as bars on the secondary axis
        ax2 = ax1.twinx()
        ax2.bar(
            x=df.index,
            height=df["Volume"],
            label="Volume",
            color="green",
            alpha=0.6,
        )
        ax2.axhline(
            y=avg_volume,
            color="green",
            linestyle="--",
            label=f"Avg Volume: {avg_volume:.2f}",
        )
        ax2.set_ylabel("Volume", color="green")
        ax2.tick_params(axis="y", labelcolor="green")

        ax1.legend(loc="upper left")
        ax2.legend(loc="upper right")
        fig.tight_layout()

        st.pyplot(fig)

        with st.expander("Underlying Stock Historical data"):
            st.dataframe(
                df.sort_index(ascending=False),
                column_config={
                    "Date": st.column_config.DateColumn(format="YYYY-MM-DD")
                },
            )

    with signals_tab:
        df["MA_5"] = df["Adj Close"].rolling(window=5).mean()
        df["Distance from MA_5"] = (df["Adj Close"] - df["MA_5"]) / df["MA_5"]

        df["MA_30"] = df["Adj Close"].rolling(window=30).mean()
        df["Distance from MA_30"] = (df["Adj Close"] - df["MA_30"]) / df["MA_30"]

        df["MA_60"] = df["Adj Close"].rolling(window=60).mean()
        df["Distance from MA_60"] = (df["Adj Close"] - df["MA_60"]) / df["MA_60"]

        df["MA_90"] = df["Adj Close"].rolling(window=90).mean()
        df["Distance from MA_90"] = (df["Adj Close"] - df["MA_90"]) / df["MA_90"]

        df["MA_180"] = df["Adj Close"].rolling(window=180).mean()
        df["Distance from MA_180"] = (df["Adj Close"] - df["MA_180"]) / df["MA_180"]

        df["Monthly_Day_change_pc"] = (
            df["Adj Close"] - df["Adj Close"].shift(30)
        ) / df["Adj Close"].shift(30)

        # Parameters
        uptick_constant = 0.01
        downtick_constant = 0.075

        df["buy_signal"] = sum(
            [
                (df["Monthly_Day_change_pc"] <= -downtick_constant),
                (df["Monthly_Day_change_pc"] <= -downtick_constant),
                (df["Distance from MA_5"] <= -downtick_constant),
                (df["Distance from MA_30"] <= -downtick_constant),
                (df["Distance from MA_90"] <= -downtick_constant),
                (df["Distance from MA_180"] <= -downtick_constant),
            ]
        )

        df["sell_signal"] = sum(
            [
                (df["Monthly_Day_change_pc"] >= uptick_constant),
                (df["Monthly_Day_change_pc"] >= uptick_constant),
                (df["Distance from MA_5"] >= uptick_constant),
                (df["Distance from MA_30"] >= uptick_constant),
                (df["Distance from MA_90"] >= uptick_constant),
                (df["Distance from MA_180"] >= uptick_constant),
            ]
        )

        df["combined_signal"] = df["sell_signal"] - df["buy_signal"]

        df_big_moves = df.loc[
            (df["buy_signal"] >= signal_tolerance)
            | (df["sell_signal"] >= signal_tolerance)
        ]

        df_big_moves["combined_signal_t_1"] = df_big_moves["combined_signal"].shift(1)
        df_big_moves["combined_signal_t_2"] = df_big_moves["combined_signal"].shift(2)

        df_big_moves_sell = df.loc[df["sell_signal"] >= signal_tolerance]
        df_big_moves_buy = df.loc[df["buy_signal"] >= signal_tolerance]

        df.to_excel("output.xlsx", sheet_name="Sheet1")

        fig, ax = plt.subplots()

        ax.plot(df["Adj Close"], label="Price")
        ax.plot(df["MA_5"], label="MA_5")
        ax.plot(df["MA_30"], label="MA_30")
        ax.plot(df["MA_90"], label="MA_90")
        ax.plot(df["MA_180"], label="MA_180")

        ax.scatter(
            x=df_big_moves_buy.index,
            y=df_big_moves_buy["Adj Close"],
            c="green",
            label="buy",
        )
        ax.scatter(
            x=df_big_moves_sell.index,
            y=df_big_moves_sell["Adj Close"],
            c="red",
            label="sell",
        )
        ax.legend(loc="best")

        ax.set(xlim=[date_range[0], date_range[1]])

        # combined plotly.express view
        fig1 = px.line(
            df,
            y=["Adj Close", "MA_5", "MA_30", "MA_90", "MA_180"],
            color_discrete_sequence=["black", "orange", "green", "blue", "yellow"],
        )
        fig2 = px.scatter(
            df_big_moves_buy, y="Adj Close", color_discrete_sequence=["green"]
        )
        fig3 = px.scatter(
            df_big_moves_sell, y="Adj Close", color_discrete_sequence=["red"]
        )

        fig_combined = go.Figure(data=fig1.data + fig2.data + fig3.data)

        cleaned_df = df_big_moves.sort_index(ascending=False)
        last_signal_record = cleaned_df.head(1)

        last_signal_date = str(last_signal_record.index.values[0])[0:10]
        last_signal_price = last_signal_record["Adj Close"].values[0]

        if last_signal_record["buy_signal"][0] >= signal_tolerance:
            last_signal_dir = "Buy"
        else:
            last_signal_dir = "Sell"

        # Visualisation
        st.title(f"{ticker} Stock Technical Analysis")
        st.markdown(f"Price: {last_price} (as of {last_date})")

        st.markdown(
            "Last Signal: "
            + last_signal_dir
            + " @ "
            + str(round(last_signal_price, 2))
            + " (as of "
            + last_signal_date
            + ")"
        )

        st.pyplot(fig)

        # plotly.express graph object: dynamic signals = fig_combined
        # st.plotly_chart(fig_combined)

        # Print Underlying Data for Recent Big moves.
        st.subheader("Signal data")
        st.dataframe(
            cleaned_df,
            column_config={"Date": st.column_config.DateColumn(format="YYYY-MM-DD")},
        )

        with st.expander("Underlying Stock Historical data"):
            st.dataframe(
                df.sort_index(ascending=False),
                column_config={
                    "Date": st.column_config.DateColumn(format="YYYY-MM-DD")
                },
            )


if __name__ == "__main__":
    run_dashboard()
