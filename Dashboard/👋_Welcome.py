import streamlit as st
from stock_ticker_strats import run_dashboard, test

st.set_page_config(
    page_title="Hello",
    page_icon="👋",
    menu_items={
        "Get Help": "https://www.virensamani.com/",
        "About": "# This dashboard if for testing purposes only. The data may not be accurate.",
    },
)

st.write("# 👋 Welcome to my Dashboard!")
st.subheader("By Viren Samani")

st.sidebar.success("Select a demo above.")
st.sidebar.markdown(
    """**Disclaimer**
    This dashboard is not personal investment advice. Data represented on charts is purely an illustration of dashboarding capabilities and may not be accurate. It **does not** constitute a personal recommendation to buy, sell, or otherwise trade all or any of the investments which may be referred to.
    """
)
