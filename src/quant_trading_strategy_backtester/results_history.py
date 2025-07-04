"""Display previously run strategy results."""

from __future__ import annotations

import json

import streamlit as st

from quant_trading_strategy_backtester.backtester import is_running_locally
from quant_trading_strategy_backtester.models import Session, StrategyModel


def display_historical_results() -> None:
    """Render historical strategy results stored locally or in session state."""
    if is_running_locally():
        session = Session()
        strategies = (
            session.query(StrategyModel)
            .order_by(StrategyModel.date_created.desc())
            .all()
        )
        session.close()
    else:
        strategies = (
            sorted(st.session_state.strategy_results, key=lambda x: x["date_created"], reverse=True)
            if "strategy_results" in st.session_state
            else []
        )

    if not strategies:
        st.info("No historical strategy results available.")
        return

    if not is_running_locally():
        st.info(
            """
            📝 **Note about Results History:**
            - Strategy results are saved within your current session
            - Results will be available as long as you keep this tab open
            - Results are reset when you refresh the page or start a new session
            """
        )

    st.header("Historical Strategy Results")

    for strategy in strategies:
        if is_running_locally():
            strategy_name = strategy.name
            date_created = strategy.date_created
            try:
                tickers = json.loads(str(strategy.tickers))
            except (json.JSONDecodeError, TypeError):
                tickers = strategy.tickers
            try:
                params = json.loads(str(strategy.parameters))
            except (json.JSONDecodeError, TypeError):
                params = strategy.parameters  # type: ignore
            total_return = strategy.total_return
            sharpe_ratio = strategy.sharpe_ratio  # type: ignore
            max_drawdown = strategy.max_drawdown
            start_date = strategy.start_date
            end_date = strategy.end_date
        else:
            strategy_name = strategy["name"]
            date_created = strategy["date_created"]
            tickers = strategy["tickers"]
            params = strategy["parameters"]
            total_return = strategy["total_return"]
            sharpe_ratio = strategy["sharpe_ratio"]  # type: ignore
            max_drawdown = strategy["max_drawdown"]
            start_date = strategy["start_date"]
            end_date = strategy["end_date"]

        ticker_display = " vs. ".join(tickers) if isinstance(tickers, list) else tickers

        with st.expander(
            f"{strategy_name} - {ticker_display} - {date_created.strftime('%Y-%m-%d %H:%M:%S')}"
        ):
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Strategy Details")
                st.write(f"**Strategy Type:** {strategy_name}")
                st.write(f"**Ticker(s):** {ticker_display}")
                st.write(f"**Date Created:** {date_created.strftime('%Y-%m-%d %H:%M:%S')}")
                st.write(f"**Start Date:** {start_date}")
                st.write(f"**End Date:** {end_date}")

                st.subheader("Parameters")
                for key, value in (params or {}).items():
                    st.write(f"**{key}:** {value}")

            with col2:
                st.subheader("Performance Metrics")
                st.write(f"**Total Return:** {total_return:.2%}")
                st.write(f"**Sharpe Ratio:** {sharpe_ratio:.2f}" if sharpe_ratio else "**Sharpe Ratio:** N/A")
                st.write(f"**Max Drawdown:** {max_drawdown:.2%}")

            st.write("---")
