import streamlit as st
from st_aggrid import AgGrid
import json
import pandas as pd
import sys
sys.path.insert(0, './scripts/Strategy')
sys.path.insert(0, './scripts')

# Streamlit Configuration
st.set_page_config(
    page_title="Statistical Arbitrage",
    page_icon="💱",
    layout="centered",
)

"""
# 💱 Statistical Arbitrage Analysis
---
## Step 1: Get Tradeable Symbols 📩

"""

with st.expander("Details 👇"):
    """
    Press update to query the [bybit](http://bybit.com) exchange for all possible futures trading pairs as well as their price history and store it as json.

    This step can take a while but only needs to be run once.

    """


col1_a, col2_a = st.columns(2)

with col1_a:
    from helper_functions import replace_timeframe
    available_intervals = [1, 3, 5, 15, 30, 60, 120, 240]
    st.selectbox(
        "Select time interval [in minutes] of data points",
        available_intervals,
        key="timeframe",
        on_change=replace_timeframe)

with col2_a:
    st.text("   ")
    st.text("   ")
    with st.spinner('Downloading price data. This can take a while...'):
        if st.button("Update Price Data"):
            from func_get_symbols import get_tradeable_symbols
            from func_prices_json import store_price_history
            sym_response = get_tradeable_symbols(rebate=False)
            # output will be huge json, may be laggy
            st.json(sym_response)
            if len(sym_response) > 0:
                store_price_history(sym_response)
                st.text(
                    f"Price history of {len(sym_response)} tradeable pairs stored")


"""
---
## Step 2: Find Cointegrated Pairs 🧾

"""

with st.expander("Details 👇"):
    """
    This takes the json output of step 1 and calculates cointegration between all possible combinations.

May take several minutes to compute. Output will be displayed as table.

To find potential opportunities:
- Focus on pairs with most zero crossings -> More trading opportunities.
- P-value should be lower than 0.05 for pair to be considered cointegrated.
- Check their trading volume on the exchange, for exotic pairs with low liquidity it may be hard to get limit orders filled.

    """

with st.spinner('Please wait. This can take a while...'):
    if st.button("Calculate Cointegration"):
        from func_cointegration import get_cointegrated_pairs
        with open("1_price_list.json") as json_file:
            price_data = json.load(json_file)
            if len(price_data) > 0:
                coint_pairs = get_cointegrated_pairs(price_data)

if st.button("Show Results"):
    try:
        coint_pairs = pd.read_csv("2_cointegrated_pairs.csv")
        AgGrid(coint_pairs)
    except:
        st.text("No data found. Press button Calculate Cointegration")

"""
---
## Step 3: Examine pair 🔎
"""

with st.expander("Details 👇"):
    """
    Enter the symbols of interesting trading pairs identified in step 2.

    Trends will be plotted and .csv file generated for backtesting.
    """

col1, col2 = st.columns(2)

with col1:
    symbol_1 = st.text_input("Pair 1:", value="BTCUSD")
with col2:
    symbol_2 = st.text_input("Pair 2:", value="ETHUSDT")

if st.button("Analyze"):
    from func_plot_trends import plot_trends
    with open("1_price_list.json") as json_file:
        price_data = json.load(json_file)
        if len(price_data) > 0:
            fig = plot_trends(symbol_1, symbol_2, price_data)
            st.pyplot(fig)
    st.text("Output '3_backtest_file.csv' generated.")


"""
---
## Step 4: Backtesting 💹
"""
with st.expander("Details 👇"):
    """
    Enter a z-score threshold to show performance over historical data.

    Will plot two subgraphs:

        - price curves (in percent change) for the two symbols

            - red markers: opening short order
            - green markers: opening long order
            - black markers: closing all positions

        - profit over time (total, and for each of the symbols)
    """

col11, col22 = st.columns(2)

with col11:
    threshold = st.text_input("Z-Score threshold:", value="1.1")

if st.button("Run Backtest"):
    from backtesting import run_backtest
    fig, df, best_threshold = run_backtest(float(threshold))
    st.pyplot(fig)

    st.text(
        f"Capital {df.columns[0]}: {round((df['profit_sym1'].iloc[-1] / 500 ) * 100, 1)} %")
    st.text(
        f"Capital {df.columns[1]}: {round((df['profit_sym2'].iloc[-1] / 500 ) * 100, 1)} %")
    st.text(
        f"Total Capital: {round((df['Capital'].iloc[-1] / 1000) * 100, 1)} %")
    st.text(
        f"Best z-score threshold: {best_threshold}")
