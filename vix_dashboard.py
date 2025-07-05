import streamlit as st
import yfinance as yf
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
        "Pairs Trading",
        "VIX Calculator",
)

ticker = st.sidebar.text_input("Ticker Symbol:", "AAPL")

# ----- MAIN CONTENT -----
if tool_type == "VIX Calculator":
    st.header(f"VIX-Style Volatility for {ticker}")
    if st.button("Calculate VIX"):
        try:
            st.write(vix_df.head())
            st.line_chart(vix_df.set_index("Date")["VIX"])
        except Exception as e:
            st.error(f"Error: {e}")

elif tool_type == "Buy and Hold":
    st.header("Buy and Hold Results")
    if st.button("Show Buy & Hold Performance"):
        try:
            # --- Single ticker only: handle MultiIndex or single
            if isinstance(data.columns, pd.MultiIndex):
            if "Close" not in data.columns:
                raise ValueError("Close price column not found!")
            data["Returns"] = data["Close"].pct_change()
            data["Cumulative"] = (1 + data["Returns"].fillna(0)).cumprod()
            st.line_chart(data["Cumulative"])
        except Exception as e:
            st.error(f"Error: {e}")

elif tool_type == "Mean Reversion":
    st.header("Mean Reversion Results")
    if st.button("Run Mean Reversion Strategy"):
        try:
            # Handle if yf.download returns MultiIndex columns (should only happen if multiple tickers)
            if isinstance(data.columns, pd.MultiIndex):
                else:
                    # fallback: just take the first ticker's Close if something weird happens
            if "Close" not in data.columns:
                raise ValueError("Close price column not found!")
            data["zscore"] = (
            data["Signal"] = 0
            data.loc[data["zscore"] > entry_z, "Signal"] = -1
            data.loc[data["zscore"] < -entry_z, "Signal"] = 1
            data.loc[abs(data["zscore"]) < exit_z, "Signal"] = 0
            data["Position"] = data["Signal"].replace(to_replace=0, method="ffill")
            data["Returns"] = data["Close"].pct_change() * data["Position"].shift(1)
            data["Cumulative"] = (1 + data["Returns"].fillna(0)).cumprod()
            st.line_chart(data["Cumulative"])
        except Exception as e:
            st.error(f"Error: {e}")

        try:
            # --- Handle MultiIndex or single
            if isinstance(data.columns, pd.MultiIndex):
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
        except Exception as e:
            st.error(f"Error: {e}")

elif tool_type == "Pairs Trading":
    st.header("Pairs Trading Results")
    ticker2 = st.text_input("Second Ticker Symbol (e.g. MSFT)", "MSFT")
    if st.button("Run Pairs Trading Strategy"):
        try:
            # Download both tickers together for perfect alignment
            close1 = close_df[ticker]
            close2 = close_df[ticker2]
            spread = close1 - close2
            position = pd.Series(0, index=spread.index)
            position[zscore > entry_z] = -1  # Short spread
            position[zscore < -entry_z] = 1  # Long spread
            position[abs(zscore) < exit_z] = 0  # Exit
            position = position.replace(to_replace=0, method="ffill")
            returns = (close1.pct_change() - close2.pct_change()) * position.shift(1)
            cumulative = (1 + returns.fillna(0)).cumprod()
            st.line_chart(cumulative)
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
