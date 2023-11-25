import datetime as dt
import random

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from Tools.streamlit_tools import plot_metric


def run_analysis():
    df = pd.read_csv(
        r"/Users/virensamani/Projects/virenps.github.io/Dashboard/Data/Inflation Data/b58d10ed (1).csv",
        skiprows=3,
    )
    df = df.ffill()

    col_names = list(df.columns)
    col_names_clean = []

    for column_name in df.columns:
        col_names_clean.append(column_name.replace("\n", ""))

    df.columns = col_names_clean
    df["Unnamed: 1"] = df["Unnamed: 1"].str.replace(" ", "")
    df["Date"] = "1 " + df["Unnamed: 1"] + " " + df["Unnamed: 0"]
    df = df[0 : len(df) - 1]

    df["Date"] = pd.to_datetime(df["Date"], format="%d %b %Y")

    print(df.columns)

    df = df[["Date", "CPI 1- month rate", "CPI 12- month rate"]]
    df.columns = ["Date", "CPI 1-Month rate", "CPI 12-Month rate"]
    print(df)
    return df


def run_dashboard():
    st.set_page_config(layout="wide", page_icon="📊")

    st.title("Macro Indicators - UK")
    df = run_analysis()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("CPI 1-Month rate")
        # plot_metric("Inflaiton", 10.2, prefix="", suffix="%")
        fig1 = px.line(
            df,
            x="Date",
            y="CPI 1-Month rate",
            markers=True,
        )
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        st.subheader("CPI 12-Month rate")
        fig2 = px.line(
            df,
            x="Date",
            y="CPI 12-Month rate",
            # color="Blue",
            markers=True,
        )
        st.plotly_chart(fig2, use_container_width=True)

    df_date_str = df[["Date", "CPI 1-Month rate", "CPI 12-Month rate"]]

    st.subheader("CPI Figures")
    with st.expander("Inflation Data"):
        st.dataframe(
            df[["Date", "CPI 1-Month rate", "CPI 12-Month rate"]].sort_index(
                ascending=False
            ),
            column_config={"Date": st.column_config.DateColumn(format="MMM YYYY")},
            hide_index=True,
        )


if __name__ == "__main__":
    run_dashboard()
