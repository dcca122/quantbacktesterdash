"""Core optimisation routines used by the Streamlit app and preparation helpers."""

from __future__ import annotations

import datetime
import itertools
import time
from typing import Any, List, Tuple, Union

import polars as pl
import streamlit as st

from quant_trading_strategy_backtester.backtest_runner import run_backtest
from quant_trading_strategy_backtester.data import (
    is_same_company,
    load_yfinance_data_one_ticker,
    load_yfinance_data_two_tickers,
)


def optimise_buy_and_hold_ticker(
    top_companies: List[Tuple[str, float]],
    start_date: datetime.date,
    end_date: datetime.date,
) -> tuple[str, dict[str, Any], dict[str, float]]:
    """Return the best ticker for the Buy and Hold strategy."""
    best_ticker = None
    best_metrics = None
    best_total_return = float("-inf")

    total_tickers = len(top_companies)
    progress_bar = st.progress(0)
    status_text = st.empty()

    for i, (ticker, _) in enumerate(top_companies):
        status_text.text(f"Evaluating ticker {i + 1} / {total_tickers}: {ticker}")
        progress_bar.progress((i + 1) / total_tickers)

        data = load_yfinance_data_one_ticker(ticker, start_date, end_date)
        if data is None or data.is_empty():
            continue

        backtester = run_backtest(data, "Buy and Hold", {}, ticker)
        # run_backtest returns (results, metrics)
        _, metrics = backtester

        if metrics and metrics["Total Return"] > best_total_return:
            best_total_return = metrics["Total Return"]
            best_ticker = ticker
            best_metrics = metrics

    progress_bar.empty()
    status_text.empty()

    if not best_ticker or not best_metrics:
        raise ValueError("Buy and Hold optimisation failed")

    return best_ticker, {}, best_metrics


def optimise_single_ticker_strategy_ticker(
    top_companies: List[Tuple[str, float]],
    start_date: datetime.date,
    end_date: datetime.date,
    strategy_type: str,
    strategy_params: dict[str, Any],
) -> str:
    """Find the best ticker for single ticker strategies."""
    best_ticker = None
    best_sharpe_ratio = float("-inf")

    total_tickers = len(top_companies)
    progress_bar = st.progress(0)
    status_text = st.empty()

    fixed_params = {
        k: v[0] if isinstance(v, (list, range)) else v
        for k, v in strategy_params.items()
    }

    for i, (ticker, _) in enumerate(top_companies):
        status_text.text(f"Evaluating ticker {i + 1} / {total_tickers}: {ticker}")
        progress_bar.progress((i + 1) / total_tickers)

        data = load_yfinance_data_one_ticker(ticker, start_date, end_date)
        if data is None or data.is_empty():
            continue

        _, current_metrics = run_backtest(data, strategy_type, fixed_params, ticker)

        if current_metrics["Sharpe Ratio"] > best_sharpe_ratio:
            best_sharpe_ratio = current_metrics["Sharpe Ratio"]
            best_ticker = ticker

    progress_bar.empty()
    status_text.empty()

    if not best_ticker:
        raise ValueError("Single ticker strategy ticker optimisation failed")

    return best_ticker


def optimise_strategy_params(
    data: pl.DataFrame,
    strategy_type: str,
    parameter_ranges: dict[str, Union[range, list[int | float]]],
    tickers: Union[str, List[str]],
) -> tuple[dict[str, int | float], dict[str, float]]:
    """Search parameter ranges and return the best parameter set."""
    best_params = None
    best_metrics = None
    best_sharpe_ratio = float("-inf")

    param_names = list(parameter_ranges.keys())
    param_values = [
        list(value) if isinstance(value, range) else value
        for value in parameter_ranges.values()
    ]

    param_combinations = list(itertools.product(*param_values))
    total_combinations = len(param_combinations)
    progress_bar = st.progress(0)
    status_text = st.empty()

    for i, params in enumerate(param_combinations):
        status_text.text(
            f"Evaluating parameter combination {i + 1} / {total_combinations}"
        )
        progress_bar.progress((i + 1) / total_combinations)

        current_params = dict(zip(param_names, params))
        _, metrics = run_backtest(data, strategy_type, current_params, tickers)

        if metrics["Sharpe Ratio"] > best_sharpe_ratio:
            best_sharpe_ratio = metrics["Sharpe Ratio"]
            best_params = current_params
            best_metrics = metrics

    progress_bar.empty()
    status_text.empty()
    if not best_params or not best_metrics:
        raise ValueError("Parameter optimisation failed")

    return best_params, best_metrics


def optimise_pairs_trading_tickers(
    top_companies: List[Tuple[str, float]],
    start_date: datetime.date,
    end_date: datetime.date,
    strategy_params: dict[str, Any],
    optimise: bool,
) -> tuple[tuple[str, str], dict[str, Any], dict[str, float]]:
    """Search for the best ticker pair for pairs trading."""
    best_pair = None
    best_params = None
    best_metrics = None
    best_sharpe_ratio = float("-inf")

    ticker_pairs = list(
        itertools.combinations([company[0] for company in top_companies], 2)
    )
    ticker_pairs = [
        pair for pair in ticker_pairs if not is_same_company(pair[0], pair[1])
    ]
    total_combinations = len(ticker_pairs)
    progress_bar = st.progress(0)
    status_text = st.empty()
    prev_pair_processing_time = 0.0

    for i, (ticker1, ticker2) in enumerate(ticker_pairs):
        start_time = time.time()
        status_text.text(
            f"Evaluating pair {i + 1} / {total_combinations}: {ticker1} vs. {ticker2} "
            f"(prev. pair processing time: {prev_pair_processing_time:.4f} seconds)"
        )
        progress_bar.progress((i + 1) / total_combinations)

        data = load_yfinance_data_two_tickers(ticker1, ticker2, start_date, end_date)
        if data is None or data.is_empty():
            continue

        if optimise:
            param_ranges = {
                k: [v] if isinstance(v, (int, float)) else v
                for k, v in strategy_params.items()
            }
            current_params, current_metrics = optimise_strategy_params(
                data, "Pairs Trading", param_ranges, [ticker1, ticker2]
            )
        else:
            _, current_metrics = run_backtest(
                data, "Pairs Trading", strategy_params, [ticker1, ticker2]
            )
            current_params = strategy_params

        if current_metrics["Sharpe Ratio"] > best_sharpe_ratio:
            best_sharpe_ratio = current_metrics["Sharpe Ratio"]
            best_pair = (ticker1, ticker2)
            best_params = current_params
            best_metrics = current_metrics

        end_time = time.time()
        prev_pair_processing_time = end_time - start_time

    progress_bar.empty()
    status_text.empty()
    if not best_pair or not best_params or not best_metrics:
        raise ValueError("Pairs trading optimisation failed")

    return best_pair, best_params, best_metrics
