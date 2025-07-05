from __future__ import annotations

"""Streamlit application for running and visualising trading strategy backtests."""

# ruff: noqa: E402

import os
import sys
from typing import cast

import streamlit as st
import streamlit.web.cli as stcli

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

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
    get_user_inputs_except_strategy_params,
    get_user_inputs_for_strategy_params,
)
from quant_trading_strategy_backtester.visualisation import (
    display_performance_metrics,
    display_returns_by_month,
    plot_equity_curve,
    plot_strategy_returns,
)


def main() -> None:
    """Run the Streamlit app."""
    st.title("Quant Trading Strategy Backtester")

    ticker, start_date, end_date, strategy_type, auto_select_tickers = (
        get_user_inputs_except_strategy_params()
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
        data, ticker_display, strategy_params = (
            prepare_pairs_trading_strategy_without_optimisation(
                cast(tuple[str, str], ticker),
                start_date,
                end_date,
                strategy_params,
                optimise,
            )
        )
        ticker1, ticker2 = cast(tuple[str, str], ticker)
        company_name1 = get_full_company_name(ticker1)
        company_name2 = get_full_company_name(ticker2)
    elif (
        strategy_type
        in ["Buy and Hold", "Mean Reversion", "Triple EMA Crossover (TEMO)"]
        and auto_select_tickers
    ):
        data, ticker_display, strategy_params = (
            prepare_single_ticker_strategy_with_optimisation(
                start_date, end_date, strategy_type, strategy_params, optimise
            )
        )
        company_name1 = get_full_company_name(ticker_display)
    else:
        data, ticker_display, strategy_params = prepare_single_ticker_strategy(
            cast(str, ticker),
            start_date,
            end_date,
            strategy_type,
            strategy_params,
            optimise,
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
    sys.argv = ["streamlit", "run", os.path.abspath(__file__)]
    sys.exit(stcli.main())
