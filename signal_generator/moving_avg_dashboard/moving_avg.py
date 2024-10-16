import datetime as dt

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf
from st_aggrid import AgGrid, GridOptionsBuilder


def read_data(tickers, start_date, end_date=dt.datetime.now().date()):
    return yf.download(tickers, start=start_date, end=end_date)["Adj Close"]


def get_cols_by_substring(df, substring):
    return df.loc[:, [substring in i for i in df.columns]]


def run_ma_analysis(tickers, ma_params, breach_limit_alert, data):

    # Extract the tickers from the data
    tickers = data.columns.tolist()  # Assuming tickers are the column names of `data`

    # Create a main dictionary to store results for each ticker
    results = {}

    # Calculate moving averages and other metrics for each ticker
    for ticker in tickers:
        # Create an empty DataFrame for the current ticker
        ticker_df = pd.DataFrame(index=data.index)

        # Store the closing prices for the ticker
        ticker_df["Ticker"] = ticker
        ticker_df["Price"] = data[ticker]

        # Create an empty DataFrame to store moving averages
        ma_df = pd.DataFrame(index=data.index)

        # Initialize a breach count for the ticker
        breach_count = 0

        # Calculate moving averages using cumulative sum for each window
        for window, threshold in ma_params.items():
            # Compute cumulative sum for the ticker
            cumsum = data[ticker].cumsum()

            # Calculate moving average using the cumulative sum method
            ma_df[f"MA{window}"] = (cumsum - cumsum.shift(window)).div(window)

            # Correct for the first `window` days where rolling can't happen (copy first values)
            ma_df.loc[: data.index[window - 1], f"MA{window}"] = (
                data[ticker].iloc[:window].mean()
            )

            # Add the moving average prices to the ticker DataFrame
            ticker_df[f"MA{window}"] = ma_df[f"MA{window}"]

            # Calculate delta as a percentage of the price
            delta_pct = (
                (data[ticker] - ma_df[f"MA{window}"]) / ma_df[f"MA{window}"]
            ) * 100
            ticker_df[f"Delta_MA{window}_Pct"] = delta_pct

            # Compare the delta percentage with the threshold to check for a breach
            ticker_df[f"MA{window}_Breach"] = np.where(
                delta_pct >= threshold, 1, np.where(delta_pct <= -threshold, -1, 0)
            )  # 1 for upper breach, -1 for lower breach

        # Calculate the total number of breaches for the ticker
        ticker_df["Total_Breach"] = ticker_df.filter(like="_Breach").sum(
            axis=1
        )  # Count total breaches per day
        ticker_df["Signal"] = np.where(
            ticker_df["Total_Breach"] >= breach_limit_alert,
            "SELL",
            np.where(ticker_df["Total_Breach"] <= -breach_limit_alert, "BUY", ""),
        )

        # Add the ticker DataFrame to the results dictionary
        results[ticker] = ticker_df

        results_df = pd.concat(results.values(), ignore_index=False).reset_index()

        results_df[
            [
                "Date",
                "Ticker",
                "Price",
                "MA5_Breach",
                "MA10_Breach",
                "MA15_Breach",
                "MA20_Breach",
                "MA100_Breach",
                "Total_Breach",
                "Signal",
            ]
        ].to_csv(
            "/Users/virensamani/Projects/virenps.github.io/Dashboard/ma_results/ma_full_data_"
            + dt.datetime.today().strftime("%Y-%m-%d")
            + ".csv"
        )

        results_recent = pd.DataFrame()
        for ticker in results:
            results_recent = pd.concat([results_recent, results[ticker].tail(1)])

    return results, results_recent[["Ticker", "Price", "Total_Breach", "Signal"]]


def plot_signals(results, ticker, tolerance=4, no_of_points=100):
    results = results.set_index("Date")

    plot_df = results.loc[(results["Ticker"] == ticker)].tail(no_of_points)

    # Plotting
    plt.figure(figsize=(12, 6))

    # Plotting Price with lines only
    plt.plot(plot_df.index, plot_df["Price"], label="Price", color="blue")

    # Initialize flags for previous breaches
    previous_positive_breach = False
    previous_negative_breach = False

    # Highlighting breach days
    for i in range(len(plot_df)):
        date = plot_df.index[i]
        breach = plot_df["Total_Breach"].iloc[i]

        # Handling +ve signals breaches (> 3) : BUY
        if breach <= -tolerance:
            if (
                previous_positive_breach
            ):  # Check if the previous day also had a positive breach
                plt.scatter(
                    date, plot_df["Price"].iloc[i], color="green", zorder=5, marker="o"
                )  # Circle for second breach
            else:
                plt.scatter(
                    date, plot_df["Price"].iloc[i], color="green", zorder=5, marker="x"
                )  # 'x' for first breach
            previous_positive_breach = True  # Set flag for positive breach
            previous_negative_breach = False  # Reset negative breach flag

        # Handling -ve breaches (< -3) : SELL
        elif breach >= tolerance:
            if (
                previous_negative_breach
            ):  # Check if the previous day also had a negative breach
                plt.scatter(
                    date, plot_df["Price"].iloc[i], color="red", zorder=5, marker="o"
                )  # Circle for second breach
            else:
                plt.scatter(
                    date, plot_df["Price"].iloc[i], color="red", zorder=5, marker="x"
                )  # 'x' for first breach
            previous_negative_breach = True  # Set flag for negative breach
            previous_positive_breach = False  # Reset positive breach flag
        else:
            # Reset flags if there's no breach
            previous_positive_breach = False
            previous_negative_breach = False

    # Adding titles and labels
    plt.title(f"{ticker} Signals", fontsize=16)
    plt.xlabel("Date", fontsize=10)
    plt.ylabel("Price", fontsize=14)
    plt.xticks(rotation=45)
    # plt.locator_params(axis="x", nbins=100)

    plt.legend()
    plt.grid()
    plt.tight_layout()

    # Show the plot
    # plt.show()

    return plt


def run_dashboard(results, final_results):
    st.set_page_config(layout="wide")

    with st.sidebar:
        no_of_points = int(
            st.number_input(
                label="No. of visibile datapoints", placeholder="Tail Legnth", value=100
            )
        )
        tolerance = st.number_input(
            label="Set tolerance level (Positive value)", value=4
        )

    st.title("MA Signals")

    st.subheader("Index Signals across SP100 and Nasdaq 100")

    final_results_signals = (
        final_results.sort_values(
            ["Signal", "Total_Breach_ABS"], ascending=[True, False]
        )
        .loc[
            (final_results["Date"] == final_results["Date"].max())
            & (final_results["Signal"].notnull())
        ]
        .drop(["Unnamed: 0"], axis=1)
        .set_index("Date")
    )[["Ticker", "Price", "Total_Breach", "Signal"]]

    st.subheader("Buy Signals")
    st.dataframe(
        final_results_signals.loc[final_results_signals["Signal"] == "BUY"],
        use_container_width=True,
    )

    st.subheader("Sell Signals")
    st.dataframe(
        final_results_signals.loc[final_results_signals["Signal"] == "SELL"],
        use_container_width=True,
    )

    builder = GridOptionsBuilder.from_dataframe(final_results_signals)
    builder.configure_pagination(enabled=True)
    builder.configure_selection(selection_mode="single", use_checkbox=True)
    grid_options = builder.build()

    # # Display AgGrid
    st.write("AgGrid Demo")
    return_value = AgGrid(final_results_signals, gridOptions=grid_options)
    if return_value["selected_rows"] is None:
        st.write("No row selected")
    else:
        # if not return_value["selected_rows"].empty:
        system_name = return_value["selected_rows"]
        st.session_state.search_1 = system_name.values[0][0]

    with st.sidebar:
        st.subheader("Parameters:")
        ticker = st.selectbox(
            "Select your ticker",
            set(results["Ticker"].values),
            index=None,
            placeholder="Select ticker...",
            key="search_1",
        )

    plot_signals(
        results=results, ticker=ticker, tolerance=tolerance, no_of_points=no_of_points
    )
    st.pyplot(plt.gcf())


if __name__ == "__main__":

    ma_params = {
        5: 1.75,  # 2.5% for the 5-day MA
        10: 2.75,  # 3.0% for the 10-day MA
        15: 3.5,  # 3.5% for the 15-day MA
        20: 4,  # 4.0% for the 20-day MA
        100: 8.0,  # 4.0% for the 20-day MA
    }
    breach_limit_alert = 4
    tickers_index_full = [
        "AAPL",
        "NVDA",
        "MSFT",
        "GOOG",
        "GOOGL",
        "AMZN",
        "META",
        "AVGO",
        "TSLA",
        "COST",
        "ASML",
        "NFLX",
        "AMD",
        "TMUS",
        "AZN",
        "PEP",
        "LIN",
        "ADBE",
        "CSCO",
        "PDD",
        "QCOM",
        "TXN",
        "INTU",
        "AMGN",
        "ISRG",
        "AMAT",
        "CMCSA",
        "ARM",
        "BKNG",
        "HON",
        "VRTX",
        "PANW",
        "MU",
        "ADP",
        "ADI",
        "REGN",
        "KLAC",
        "SBUX",
        "LRCX",
        "GILD",
        "MELI",
        "INTC",
        "MDLZ",
        "ABNB",
        "CTAS",
        "CEG",
        "SNPS",
        "PYPL",
        "CRWD",
        "CDNS",
        "MAR",
        "ORLY",
        "CSX",
        "WDAY",
        "FTNT",
        "MRVL",
        "NXPI",
        "ADSK",
        "DASH",
        "ROP",
        "FANG",
        "TTD",
        "PCAR",
        "CPRT",
        "AEP",
        "PAYX",
        "MNST",
        "KDP",
        "TEAM",
        "CHTR",
        "ROST",
        "DDOG",
        "KHC",
        "ODFL",
        "MCHP",
        "GEHC",
        "FAST",
        "EXC",
        "IDXX",
        "VRSK",
        "EA",
        "BKR",
        "CTSH",
        "CCEP",
        "XEL",
        "LULU",
        "CSGP",
        "ON",
        "ZS",
        "CDW",
        "ANSS",
        "DXCM",
        "BIIB",
        "TTWO",
        "ILMN",
        "GFS",
        "MRNA",
        "MDB",
        "WBD",
        "DLTR",
        "WBA",
        "LLY",
        "WMT",
        "JPM",
        "BRK-B",
        "UNH",
        "ORCL",
        "XOM",
        "V",
        "MA",
        "HD",
        "PG",
        "JNJ",
        "ABBV",
        "BAC",
        "KO",
        "MRK",
        "CVX",
        "ACN",
        "TMO",
        "MCD",
        "IBM",
        "ABT",
        "WFC",
        "AXP",
        "CAT",
        "PM",
        "VZ",
        "MS",
        "PFE",
        "DIS",
        "RTX",
        "GS",
        "T",
        "LOW",
        "UNP",
        "LMT",
        "COP",
        "C",
        "MDT",
        "BMY",
        "NKE",
        "UPS",
        "SO",
        "BA",
        "MO",
        "CVS",
        "CL",
        "GD",
        "MMM",
        "TGT",
        "USB",
        "FCX",
        "FDX",
        "EMR",
        "WMB",
        "MET",
        "COF",
        "NSC",
        "SPG",
        "BK",
        "GM",
        "AIG",
        "F",
        "DOW",
        "HPQ",
        "EBAY",
        "HAL",
        "DVN",
        "BAX",
    ]

    # # # Read data and write to file
    # data = read_data(tickers=tickers_index_full, start_date=dt.date(2020, 1, 1))
    # results, results_summarised = run_ma_analysis(
    #     tickers=tickers_index_full,
    #     ma_params=ma_params,
    #     breach_limit_alert=breach_limit_alert,
    #     data=data,
    # )

    # # Read saved data file - change to read latest file
    results = pd.read_csv(
        "/Users/virensamani/Projects/virenps.github.io/Dashboard/ma_results/ma_full_data_2024-10-16.csv"
    )
    final_results = results.loc[results["Signal"] != ""]
    final_results["Total_Breach_ABS"] = final_results["Total_Breach"].abs()

    final_results.to_csv(
        "/Users/virensamani/Projects/virenps.github.io/Dashboard/ma_results/ma_index_tickers_signals"
        + dt.datetime.today().strftime("%Y-%m-%d")
        + ".csv"
    )

    run_dashboard(results, final_results)
    # plot_signals(final_results, "AAPL")
