"""Streamlit dashboard for viewing implied and historical volatility."""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from quant_desk_tools import get_historical_vix
from quant_desk_tools.black_scholes import black_scholes_price

def assign_single_column(df, column_name, data):
    # If it's a DataFrame, pick the first column
    if isinstance(data, pd.DataFrame):
        data = data.iloc[:, 0]
    df[column_name] = data

# ----- SIDEBAR -----
st.sidebar.title("Strategy & Analysis Dashboard")
tool_type = st.sidebar.selectbox(
    "Analysis Type",
    [
        "Buy and Hold",
        "Mean Reversion",
        "Moving Average Crossover",
        "Pairs Trading",
        "VIX Calculator",
        "Black-Scholes Option Pricing"
    ]
)

ticker = st.sidebar.text_input("Ticker Symbol:", "AAPL")
start_date = st.sidebar.date_input('Start Date', value=pd.to_datetime("2020-01-01"))
end_date = st.sidebar.date_input('End Date', value=pd.to_datetime("2025-07-01"))

# Download historical data using user input
df = yf.download(
    ticker,
    start=start_date,
    end=end_date,
    auto_adjust=True
)
st.write(f"Showing historical data for {ticker} from {start_date} to {end_date}:")
st.dataframe(df.head())

# ----- MAIN CONTENT -----
if tool_type == "VIX Calculator":
    st.header(f"VIX-Style Volatility for {ticker}")
    window = st.number_input("Rolling window (days):", min_value=5, max_value=90, value=30, step=1)
    if st.button("Calculate VIX"):
        try:
            vix_df = get_historical_vix(ticker, window=window, start=str(start_date), end=str(end_date))
            st.write(vix_df.head())
            st.line_chart(vix_df.set_index("Date")["VIX"])
        except Exception as e:
            st.error(f"Error: {e}")

elif tool_type == "Buy and Hold":
    st.header("Buy and Hold Results")
    if st.button("Show Buy & Hold Performance"):
        try:
            data = yf.download(ticker, start=str(start_date), end=str(end_date), auto_adjust=True)
            # --- Single ticker only: handle MultiIndex or single
            if isinstance(data.columns, pd.MultiIndex):
                data = data['Close'].iloc[:, 0].to_frame('Close')
            if "Close" not in data.columns:
                raise ValueError("Close price column not found!")
            data["Returns"] = data["Close"].pct_change()
            data["Cumulative"] = (1 + data["Returns"].fillna(0)).cumprod()
            st.line_chart(data["Cumulative"])
            st.write(data.tail())
            st.metric("Total Return (%)", f"{100*(data['Cumulative'].iloc[-1] - 1):.2f}")
        except Exception as e:
            st.error(f"Error: {e}")

elif tool_type == "Mean Reversion":
    st.header("Mean Reversion Results")
    window = st.number_input("Rolling Window (Days)", min_value=2, max_value=30, value=14, step=1)
    entry_z = st.slider("Entry Z-Score", min_value=0.5, max_value=3.0, value=2.0, step=0.1)
    exit_z = st.slider("Exit Z-Score", min_value=0.0, max_value=2.0, value=0.5, step=0.1)
    if st.button("Run Mean Reversion Strategy"):
        try:
            data = yf.download(ticker, start=str(start_date), end=str(end_date), auto_adjust=True)
            # Handle if yf.download returns MultiIndex columns (should only happen if multiple tickers)
            if isinstance(data.columns, pd.MultiIndex):
                if 'Close' in data.columns.levels[0] and ticker in data['Close']:
                    data = data['Close'][ticker].to_frame('Close')
                else:
                    # fallback: just take the first ticker's Close if something weird happens
                    data = data['Close'].iloc[:, 0].to_frame('Close')
            if "Close" not in data.columns:
                raise ValueError("Close price column not found!")
            data["zscore"] = (
                (data["Close"] - data["Close"].rolling(window).mean()) /
                data["Close"].rolling(window).std()
            )
            data["Signal"] = 0
            data.loc[data["zscore"] > entry_z, "Signal"] = -1
            data.loc[data["zscore"] < -entry_z, "Signal"] = 1
            data.loc[abs(data["zscore"]) < exit_z, "Signal"] = 0
            data["Position"] = data["Signal"].replace(to_replace=0, method="ffill")
            data["Returns"] = data["Close"].pct_change() * data["Position"].shift(1)
            data["Cumulative"] = (1 + data["Returns"].fillna(0)).cumprod()
            st.line_chart(data["Cumulative"])
            st.write(data[["Close", "zscore", "Signal", "Position", "Returns", "Cumulative"]].tail())
            st.metric("Total Return (%)", f"{100*(data['Cumulative'].iloc[-1] - 1):.2f}")
        except Exception as e:
            st.error(f"Error: {e}")

elif tool_type == "Moving Average Crossover":
    st.header("Moving Average Crossover Results")
    short_window = st.number_input("Short MA Window", min_value=2, max_value=100, value=20, step=1)
    long_window = st.number_input("Long MA Window", min_value=10, max_value=200, value=50, step=1)
    if st.button("Run Moving Average Crossover"):
        try:
            data = yf.download(ticker, start=str(start_date), end=str(end_date), auto_adjust=True)
            # --- Handle MultiIndex or single
            if isinstance(data.columns, pd.MultiIndex):
                data = data['Close'].iloc[:, 0].to_frame('Close')
            if "Close" not in data.columns:
                raise ValueError("Close price column not found!")
            data["SMA_short"] = data["Close"].rolling(window=short_window).mean()
            data["SMA_long"] = data["Close"].rolling(window=long_window).mean()
            data["Signal"] = 0
            data.loc[data["SMA_short"] > data["SMA_long"], "Signal"] = 1
            data.loc[data["SMA_short"] < data["SMA_long"], "Signal"] = -1
            data["Position"] = data["Signal"].replace(to_replace=0, method="ffill")
            data["Returns"] = data["Close"].pct_change() * data["Position"].shift(1)
            data["Cumulative"] = (1 + data["Returns"].fillna(0)).cumprod()
            st.line_chart(data["Cumulative"])
            st.write(data[["Close", "SMA_short", "SMA_long", "Signal", "Position", "Returns", "Cumulative"]].tail())
            st.metric("Total Return (%)", f"{100*(data['Cumulative'].iloc[-1] - 1):.2f}")
        except Exception as e:
            st.error(f"Error: {e}")

elif tool_type == "Pairs Trading":
    st.header("Pairs Trading Results")
    ticker2 = st.text_input("Second Ticker Symbol (e.g. MSFT)", "MSFT")
    lookback = st.number_input("Z-Score Lookback Window", min_value=2, max_value=60, value=20, step=1)
    entry_z = st.slider("Entry Z-Score", min_value=0.5, max_value=3.0, value=2.0, step=0.1)
    exit_z = st.slider("Exit Z-Score", min_value=0.0, max_value=2.0, value=0.5, step=0.1)
    if st.button("Run Pairs Trading Strategy"):
        try:
            # Download both tickers together for perfect alignment
            df = yf.download([ticker, ticker2], start=str(start_date), end=str(end_date), auto_adjust=True)
            close_df = df['Close'].dropna()
            close1 = close_df[ticker]
            close2 = close_df[ticker2]
            spread = close1 - close2
            zscore = (spread - spread.rolling(lookback).mean()) / spread.rolling(lookback).std()
            position = pd.Series(0, index=spread.index)
            position[zscore > entry_z] = -1  # Short spread
            position[zscore < -entry_z] = 1  # Long spread
            position[abs(zscore) < exit_z] = 0  # Exit
            position = position.replace(to_replace=0, method="ffill")
            returns = (close1.pct_change() - close2.pct_change()) * position.shift(1)
            cumulative = (1 + returns.fillna(0)).cumprod()
            st.line_chart(cumulative)
            st.write(pd.DataFrame({"Spread": spread, "Z-Score": zscore, "Position": position}).tail())
            st.metric("Total Return (%)", f"{100*(cumulative.iloc[-1] - 1):.2f}")
        except Exception as e:
            st.error(f"Error: {e}")

if tool_type == "Black-Scholes Option Pricing":
    st.header("Black-Scholes Option Pricing")
    spot = st.number_input("Spot Price (S)", value=100.0)
    strike = st.number_input("Strike Price (K)", value=100.0)
    ttm = st.number_input("Time to Expiration (years)", value=1.0)
    rate = st.number_input("Risk-Free Rate (%)", value=2.0) / 100
    vol = st.number_input("Volatility (%)", value=20.0) / 100
    option_type = st.selectbox("Option Type", ["call", "put"])
    if st.button("Calculate Option Price"):
        try:
            results = black_scholes_price(spot, strike, ttm, rate, vol, option_type)
            st.subheader("Results")
            st.write(f"**Option Price:** ${results['price']:.2f}")
            st.write(f"Delta:  {results['delta']:.4f}")
            st.write(f"Gamma:  {results.get('gamma', 0):.4f}")
            st.write(f"Vega:   {results.get('vega', 0):.4f}")
            st.write(f"Theta:  {results['theta']:.4f}")
            st.write(f"Rho:    {results['rho']:.4f}")
            # --- Payoff Chart ---
            prices = np.linspace(spot * 0.5, spot * 1.5, 100)
            if option_type == "call":
                payoff = np.maximum(prices - strike, 0)
            else:
                payoff = np.maximum(strike - prices, 0)
            payoff_df = pd.DataFrame({"Price": prices, "Payoff": payoff})
            st.line_chart(payoff_df.set_index("Price"))
        except Exception as e:
            st.error(f"Error calculating Black-Scholes: {e}")
