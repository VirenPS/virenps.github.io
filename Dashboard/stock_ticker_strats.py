### Moving Average Dashboard
import datetime as dt

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf


def test():
    print("works")


def read_data(ticker):
    return yf.download(
        ticker, start="2010-01-01", end=dt.datetime.now().date() + dt.timedelta(days=1)
    )


def run_dashboard():
    # Parameters required
    

    # Create a text element and let the reader know the data is loading.

    # Notify the reader that the data was successfully loaded.
    # data_load_state = st.text("Loading data...")
    # data_load_state.text("Done! (using st.cache_data)")

    df = read_data(ticker)

    # Run Analysis
    df = df.sort_index(inplace=False)
    last_price = round(df.tail(1)["Adj Close"].values[0], 2)
    last_date = str(df.tail(1).index.values[0])[0:10]

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

    df["Monthly_Day_change_pc"] = (df["Adj Close"] - df["Adj Close"].shift(30)) / df[
        "Adj Close"
    ].shift(30)

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
        (df["buy_signal"] >= signal_tolerance) | (df["sell_signal"] >= signal_tolerance)
    ]

    df_big_moves["combined_signal_t_1"] = df_big_moves["combined_signal"].shift(1)
    df_big_moves["combined_signal_t_2"] = df_big_moves["combined_signal"].shift(2)

    df_big_moves_sell = df.loc[df["sell_signal"] >= signal_tolerance]
    df_big_moves_buy = df.loc[df["buy_signal"] >= signal_tolerance]

    df.to_excel("output.xlsx", sheet_name="Sheet1")

    # st.subheader("Stock Movements")
    # st.line_chart(df[["Adj Close", "MA_5", "MA_30", "MA_90", "MA_180"]])
    # st.scatter_chart(df_big_moves_neg["Adj Close"])

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
    st.subheader(f"Price: {last_price} (as of {last_date})")

    st.subheader(
        "Last Signal: "
        + last_signal_dir
        + " @ "
        + str(round(last_signal_price, 2))
        + " (as of "
        + last_signal_date
        + ")"
    )
    st.pyplot(fig)

    # Print Underlying Data for Recent Big moves.
    st.subheader("Signal data")
    st.write(cleaned_df)

    st.subheader("Underlying Stock data")
    st.write(df.sort_index(ascending=False))
