"""Utility functions for preparing strategy data and running optional optimisations."""

from __future__ import annotations

import datetime
import time
from typing import Any, cast

import polars as pl
import streamlit as st

from quant_trading_strategy_backtester.data import (
    get_top_sp500_companies,
    load_yfinance_data_one_ticker,
    load_yfinance_data_two_tickers,
)
from quant_trading_strategy_backtester.optimiser import (
    optimise_buy_and_hold_ticker,
    optimise_pairs_trading_tickers,
    optimise_single_ticker_strategy_ticker,
    optimise_strategy_params,
    run_optimisation,
)
from quant_trading_strategy_backtester.utils import (
    NUM_TOP_COMPANIES_ONE_TICKER,
    NUM_TOP_COMPANIES_TWO_TICKERS,
)


def prepare_buy_and_hold_strategy_with_optimisation(
    start_date: datetime.date,
    end_date: datetime.date,
) -> tuple[pl.DataFrame, str, dict[str, Any]]:
    """Select the best S&P 500 ticker for a Buy and Hold strategy."""
    st.info(
        f"Selecting the best ticker from the top {NUM_TOP_COMPANIES_ONE_TICKER} S&P 500 "
        "companies. This may take a while..."
    )

    start_time = time.time()
    with st.spinner("Fetching top S&P 500 companies..."):
        top_companies = get_top_sp500_companies(NUM_TOP_COMPANIES_ONE_TICKER)

    best_ticker, _, _ = optimise_buy_and_hold_ticker(
        top_companies, start_date, end_date
    )

    end_time = time.time()
    st.success(f"Optimisation complete! Time taken: {end_time - start_time:.4f} seconds")

    st.header("Optimal Ticker")
    st.write(f"Best performing ticker: {best_ticker}")

    data = load_yfinance_data_one_ticker(best_ticker, start_date, end_date)
    return data, best_ticker, {}


def prepare_single_ticker_strategy_with_optimisation(
    start_date: datetime.date,
    end_date: datetime.date,
    strategy_type: str,
    strategy_params: dict[str, Any],
    optimise: bool,
) -> tuple[pl.DataFrame, str, dict[str, Any]]:
    """Auto-select the best ticker for single ticker strategies and optionally optimise parameters."""
    st.info(
        f"Selecting the best ticker from the top {NUM_TOP_COMPANIES_ONE_TICKER} S&P 500 "
        "companies. This may take a while..."
    )

    start_time = time.time()
    with st.spinner("Fetching top S&P 500 companies..."):
        top_companies = get_top_sp500_companies(NUM_TOP_COMPANIES_ONE_TICKER)

    best_ticker = optimise_single_ticker_strategy_ticker(
        top_companies, start_date, end_date, strategy_type, strategy_params
    )

    data = load_yfinance_data_one_ticker(best_ticker, start_date, end_date)

    if optimise:
        best_params, _ = optimise_strategy_params(
            data,
            strategy_type,
            cast(dict[str, range | list[int | float]], strategy_params),
            best_ticker,
        )
    else:
        best_params = {
            k: v[0] if isinstance(v, (list, range)) else v
            for k, v in strategy_params.items()
        }

    end_time = time.time()
    st.success(f"Optimisation complete! Time taken: {end_time - start_time:.4f} seconds")

    st.header("Optimal Ticker and Parameters")
    result = {"ticker": best_ticker} | (best_params if optimise else {})
    st.write(result)

    return data, best_ticker, best_params


def prepare_pairs_trading_strategy_with_optimisation(
    start_date: datetime.date,
    end_date: datetime.date,
    strategy_params: dict[str, Any],
    optimise: bool,
) -> tuple[pl.DataFrame, str, dict[str, int | float]]:
    """Find the best ticker pair for a pairs trading strategy and optionally optimise."""
    st.info(
        f"Selecting the best pair from the top {NUM_TOP_COMPANIES_TWO_TICKERS} S&P 500 "
        "companies. This may take a while..."
    )

    start_time = time.time()
    with st.spinner("Fetching top S&P 500 companies..."):
        top_companies = get_top_sp500_companies(NUM_TOP_COMPANIES_TWO_TICKERS)

    ticker, strategy_params, _ = optimise_pairs_trading_tickers(
        top_companies, start_date, end_date, strategy_params, optimise
    )
    ticker1, ticker2 = ticker

    end_time = time.time()
    st.success(f"Optimisation complete! Time taken: {end_time - start_time:.4f} seconds")

    st.header("Optimal Tickers and Parameters")
    st.write({"ticker1": ticker1, "ticker2": ticker2} | strategy_params)

    data = load_yfinance_data_two_tickers(ticker1, ticker2, start_date, end_date)
    ticker_display = f"{ticker1} vs. {ticker2}"

    if optimise:
        strategy_params, _ = run_optimisation(
            data,
            "Pairs Trading",
            strategy_params,
            start_date,
            end_date,
            [ticker1, ticker2],
        )

    return data, ticker_display, strategy_params


def prepare_pairs_trading_strategy_without_optimisation(
    ticker: tuple[str, str],
    start_date: datetime.date,
    end_date: datetime.date,
    strategy_params: dict[str, Any],
    optimise: bool,
) -> tuple[pl.DataFrame, str, dict[str, Any]]:
    """Handle a user-specified pair without auto-selection."""
    ticker1, ticker2 = ticker
    data = load_yfinance_data_two_tickers(ticker1, ticker2, start_date, end_date)
    ticker_display = f"{ticker1} vs. {ticker2}"

    if optimise:
        strategy_params, _ = run_optimisation(
            data,
            "Pairs Trading",
            strategy_params,
            start_date,
            end_date,
            [ticker1, ticker2],
        )

    return data, ticker_display, strategy_params


def prepare_single_ticker_strategy(
    ticker: str,
    start_date: datetime.date,
    end_date: datetime.date,
    strategy_type: str,
    strategy_params: dict[str, Any],
    optimise: bool,
) -> tuple[pl.DataFrame, str, dict[str, Any]]:
    """Load data for a single ticker and optionally optimise parameters."""
    data = load_yfinance_data_one_ticker(ticker, start_date, end_date)
    ticker_display = ticker

    if optimise and strategy_type != "Buy and Hold":
        strategy_params, _ = run_optimisation(
            data, strategy_type, strategy_params, start_date, end_date, ticker
        )
    elif optimise and strategy_type == "Buy and Hold":
        top_companies = get_top_sp500_companies(NUM_TOP_COMPANIES_ONE_TICKER)
        best_ticker, strategy_params, _ = optimise_buy_and_hold_ticker(
            top_companies, start_date, end_date
        )
        ticker = best_ticker
        ticker_display = best_ticker
        data = load_yfinance_data_one_ticker(ticker, start_date, end_date)

    return data, ticker_display, strategy_params
