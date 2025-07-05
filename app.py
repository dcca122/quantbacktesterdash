from __future__ import annotations

import datetime
import os
import sys

import numpy as np
import pandas as pd
import streamlit as st

# Ensure src is on the path when running this file directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

from quant_desk_tools.black_scholes import black_scholes_price
from quant_desk_tools.utils import get_historical_vix
from quant_trading_strategy_backtester.backtest_runner import run_backtest
from quant_trading_strategy_backtester.data import get_full_company_name
from quant_trading_strategy_backtester.results_history import display_historical_results
from quant_trading_strategy_backtester.strategy_preparation import (
    prepare_pairs_trading_strategy_with_optimisation,
    prepare_pairs_trading_strategy_without_optimisation,
    prepare_single_ticker_strategy,
    prepare_single_ticker_strategy_with_optimisation,
)
from quant_trading_strategy_backtester.streamlit_ui import (
    get_user_inputs_for_strategy_params,
)
from quant_trading_strategy_backtester.utils import (
    NUM_TOP_COMPANIES_ONE_TICKER,
    NUM_TOP_COMPANIES_TWO_TICKERS,
)
from quant_trading_strategy_backtester.visualisation import (
    display_performance_metrics,
    display_returns_by_month,
    plot_equity_curve,
    plot_strategy_returns,
)

STRATEGY_OPTIONS = [
    "Pairs Trading",
    "Buy and Hold",
    "Mean Reversion",
    "VIX Calculator",
    "Black-Scholes Option Pricing",
]


def get_trading_strategy_inputs(strategy_type: str):
    """Return ticker info and date range for trading strategies."""
    auto_select = False
    if strategy_type == "Pairs Trading":
        auto_select = st.sidebar.checkbox(
            f"Optimise Ticker Pair From Top {NUM_TOP_COMPANIES_TWO_TICKERS} S&P 500 Companies"
        )
        if auto_select:
            ticker = None
        else:
            ticker1 = st.sidebar.text_input("Ticker Symbol 1", value="AAPL").upper()
            ticker2 = st.sidebar.text_input("Ticker Symbol 2", value="GOOGL").upper()
            ticker = (ticker1, ticker2)
    else:
        auto_select = st.sidebar.checkbox(
            f"Optimise Ticker From Top {NUM_TOP_COMPANIES_ONE_TICKER} S&P 500 Companies"
        )
        if auto_select:
            ticker = None
        else:
            ticker = st.sidebar.text_input("Ticker Symbol", value="AAPL").upper()

    start_date = st.sidebar.date_input("Start Date", value=datetime.date(2020, 1, 1))
    end_date = st.sidebar.date_input("End Date", value=datetime.date(2023, 12, 31))
    return ticker, start_date, end_date, auto_select


def main() -> None:
    """Run the Streamlit dashboard."""
    st.set_page_config(page_title="Quant Trading Strategy Backtester", layout="wide")
    st.title("Quant Trading Strategy Backtester")

    strategy_type = st.sidebar.selectbox("Strategy Type", STRATEGY_OPTIONS, index=0)

    if strategy_type == "VIX Calculator":
        ticker = st.sidebar.text_input("Ticker Symbol", value="AAPL").upper()
        start_date = st.sidebar.date_input(
            "Start Date", value=datetime.date(2020, 1, 1)
        )
        end_date = st.sidebar.date_input("End Date", value=datetime.date.today())
        if st.sidebar.button("Calculate VIX"):
            try:
                vix_df = get_historical_vix(
                    ticker,
                    start=start_date.strftime("%Y-%m-%d"),
                    end=end_date.strftime("%Y-%m-%d"),
                )
                st.subheader(f"VIX-Style Volatility for {ticker}")
                st.dataframe(vix_df.head(), use_container_width=True, hide_index=True)
                st.line_chart(vix_df.set_index("Date")["VIX"])
            except Exception as e:  # pragma: no cover - visual output only
                st.error(f"Error: {e}")
        return

    if strategy_type == "Black-Scholes Option Pricing":
        spot = st.sidebar.number_input("Spot Price (S)", value=100.0)
        strike = st.sidebar.number_input("Strike Price (K)", value=100.0)
        ttm = st.sidebar.number_input("Time to Expiration (years)", value=1.0)
        rate = st.sidebar.number_input("Risk-Free Rate (%)", value=2.0) / 100
        vol = st.sidebar.number_input("Volatility (%)", value=20.0) / 100
        option_type = st.sidebar.selectbox("Option Type", ["call", "put"])
        if st.sidebar.button("Calculate Option Price"):
            try:
                results = black_scholes_price(spot, strike, ttm, rate, vol, option_type)
                st.subheader("Results")
                st.write(f"**Option Price:** ${results['price']:.2f}")
                st.write(f"Delta:  {results['delta']:.4f}")
                st.write(f"Gamma:  {results.get('gamma', 0):.4f}")
                st.write(f"Vega:   {results.get('vega', 0):.4f}")
                st.write(f"Theta:  {results['theta']:.4f}")
                st.write(f"Rho:    {results['rho']:.4f}")
                prices = np.linspace(spot * 0.5, spot * 1.5, 100)
                payoff = (
                    np.maximum(prices - strike, 0)
                    if option_type == "call"
                    else np.maximum(strike - prices, 0)
                )
                payoff_df = pd.DataFrame({"Price": prices, "Payoff": payoff})
                st.line_chart(payoff_df.set_index("Price"))
            except Exception as e:  # pragma: no cover - visual output only
                st.error(f"Error calculating Black-Scholes: {e}")
        return

    # ----- Trading strategies -----
    ticker, start_date, end_date, auto_select_tickers = get_trading_strategy_inputs(
        strategy_type
    )
    optimise, strategy_params = get_user_inputs_for_strategy_params(strategy_type)

    company_name1: str | None = None
    company_name2: str | None = None

    if strategy_type == "Pairs Trading" and auto_select_tickers:
        data, ticker_display, strategy_params = (
            prepare_pairs_trading_strategy_with_optimisation(
                start_date, end_date, strategy_params, optimise
            )
        )
        ticker1, ticker2 = ticker_display.split(" vs. ")
        company_name1 = get_full_company_name(ticker1)
        company_name2 = get_full_company_name(ticker2)
    elif strategy_type == "Pairs Trading":
        assert isinstance(ticker, tuple)
        data, ticker_display, strategy_params = (
            prepare_pairs_trading_strategy_without_optimisation(
                ticker,
                start_date,
                end_date,
                strategy_params,
                optimise,
            )
        )
        ticker1, ticker2 = ticker
        company_name1 = get_full_company_name(ticker1)
        company_name2 = get_full_company_name(ticker2)
    elif strategy_type in ["Buy and Hold", "Mean Reversion"] and auto_select_tickers:
        data, ticker_display, strategy_params = (
            prepare_single_ticker_strategy_with_optimisation(
                start_date, end_date, strategy_type, strategy_params, optimise
            )
        )
        company_name1 = get_full_company_name(ticker_display)
    else:
        assert isinstance(ticker, str)
        data, ticker_display, strategy_params = prepare_single_ticker_strategy(
            ticker, start_date, end_date, strategy_type, strategy_params, optimise
        )
        company_name1 = get_full_company_name(ticker_display)

    if data is None or data.is_empty():
        st.write("No data available for the selected ticker and date range")
        return

    company_display = (
        f"{company_name1} vs. {company_name2}" if company_name2 else company_name1
    )
    tickers: str | list[str] = (
        ticker_display.split(" vs. ")
        if strategy_type == "Pairs Trading"
        else ticker_display
    )

    results, metrics = run_backtest(data, strategy_type, strategy_params, tickers)

    display_performance_metrics(metrics, company_display)
    plot_equity_curve(results, ticker_display, company_display)
    plot_strategy_returns(results, ticker_display, company_display)
    display_returns_by_month(results)

    st.header(f"Raw Data for {company_display}")
    st.dataframe(data.to_pandas(), use_container_width=True, hide_index=True)

    display_historical_results()


if __name__ == "__main__":
    main()
