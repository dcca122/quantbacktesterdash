"""
Contains functions related to optimisation and backtesting for strategy
parameters and ticker pairs.
"""

import datetime
import time
from typing import Any, cast

import polars as pl
import streamlit as st

import quant_trading_strategy_backtester.optimiser_core as optimiser_core
from quant_trading_strategy_backtester.backtest_runner import (
    create_strategy,
    run_backtest,
)
from quant_trading_strategy_backtester.data import get_top_sp500_companies
from quant_trading_strategy_backtester.optimiser_core import (
    optimise_buy_and_hold_ticker,
    optimise_pairs_trading_tickers,
    optimise_single_ticker_strategy_ticker,
    optimise_strategy_params,
)
from quant_trading_strategy_backtester.utils import NUM_TOP_COMPANIES_ONE_TICKER


def run_optimisation(
    data: pl.DataFrame,
    strategy_type: str,
    strategy_params: dict[str, Any],
    start_date: datetime.date,
    end_date: datetime.date,
    tickers: str | list[str],
) -> tuple[dict[str, Any], dict[str, float]]:
    """
    Runs the optimisation process for strategy parameters or ticker selection.

    Args:
        data: Historical price data.
        strategy_type: The type of strategy being optimised.
        strategy_params: Initial strategy parameters or parameter ranges.
        start_date: Start date for historical data.
        end_date: End date for historical data.
        tickers: The ticker or tickers used in the backtest.

    Returns:
        A tuple containing:
            - Optimised strategy parameters or selected ticker.
            - Performance metrics for the optimised strategy.
    """
    st.info("Optimising strategy. This may take a while...")
    start_time = time.time()

    if strategy_type == "Buy and Hold":
        top_companies = get_top_sp500_companies(NUM_TOP_COMPANIES_ONE_TICKER)
        best_ticker, strategy_params, metrics = optimise_buy_and_hold_ticker(
            top_companies, start_date, end_date
        )
        st.success(f"Best ticker for Buy and Hold: {best_ticker}")
    else:
        strategy_params, metrics = optimiser_core.optimise_strategy_params(
            data,
            strategy_type,
            cast(dict[str, range | list[int | float]], strategy_params),
            tickers,
        )

    end_time = time.time()
    duration = end_time - start_time
    st.success(f"Optimisation complete! Time taken: {duration:.4f} seconds")

    st.header("Optimal Parameters")
    st.write(strategy_params)

    return strategy_params, metrics


__all__ = [
    "run_optimisation",
    "optimise_buy_and_hold_ticker",
    "optimise_single_ticker_strategy_ticker",
    "optimise_strategy_params",
    "optimise_pairs_trading_tickers",
    "run_backtest",
    "create_strategy",
]
