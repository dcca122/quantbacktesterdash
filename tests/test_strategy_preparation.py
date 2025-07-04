
"""Tests for backtesting helpers and strategy preparation functions."""

import datetime
from typing import Any

import polars as pl
import pytest
from quant_trading_strategy_backtester.optimiser import (
    optimise_single_ticker_strategy_ticker,
    run_backtest,
)
from quant_trading_strategy_backtester.strategy_preparation import (
    prepare_single_ticker_strategy_with_optimisation,
)


@pytest.mark.parametrize(
    "strategy_type,params,tickers",
    [
        ("Moving Average Crossover", {"short_window": 5, "long_window": 20}, "AAPL"),
        ("Mean Reversion", {"window": 5, "std_dev": 2.0}, "AAPL"),
        (
            "Pairs Trading",
            {"window": 20, "entry_z_score": 2.0, "exit_z_score": 0.5},
            ["AAPL", "GOOGL"],
        ),
    ],
)
def test_run_backtest(
    mock_polars_data: pl.DataFrame,
    strategy_type: str,
    params: dict[str, Any],
    tickers: str | list[str],
) -> None:
    # Ensure mock_polars_data has a Date column
    if "Date" not in mock_polars_data.columns:
        mock_polars_data = mock_polars_data.with_columns(
            pl.date_range(
                start=datetime.date(2020, 1, 1),
                end=datetime.date(2020, 1, 31),
                interval="1d",
            ).alias("Date")
        )

    if strategy_type == "Pairs Trading":
        # Create mock data for two assets
        mock_polars_data = pl.DataFrame(
            {
                "Date": mock_polars_data["Date"],
                "Close_1": mock_polars_data["Close"],
                "Close_2": mock_polars_data["Close"] * 1.1,  # Slightly different prices
            }
        )
    elif "Close" not in mock_polars_data.columns:
        mock_polars_data = mock_polars_data.with_columns(pl.col("Open").alias("Close"))

    results, metrics = run_backtest(mock_polars_data, strategy_type, params, tickers)
    assert isinstance(results, pl.DataFrame)
    assert isinstance(metrics, dict)
    EXPECTED_METRICS = {"Total Return", "Sharpe Ratio", "Max Drawdown"}
    for metric in EXPECTED_METRICS:
        assert metric in metrics


def test_run_backtest_invalid_strategy() -> None:
    with pytest.raises(ValueError, match="Invalid strategy type"):
        run_backtest(pl.DataFrame(), "Invalid Strategy", {}, "AAPL")


def test_optimise_single_ticker_strategy_ticker(monkeypatch):
    # Mock data and functions
    mock_top_companies = [("AAPL", 1000000.0), ("GOOGL", 900000.0), ("MSFT", 800000.0)]
    mock_polars_data = pl.DataFrame(
        {
            "Date": [datetime.date(2020, 1, i) for i in range(1, 32)],
            "Close": [100 + i for i in range(31)],
        }
    )

    def mock_load_data(*args, **kwargs):
        return mock_polars_data

    def mock_run_backtest(*args, **kwargs):
        strategy_type = args[1]
        if strategy_type == "Moving Average Crossover":
            return None, {"Sharpe Ratio": 1.5}
        elif strategy_type == "Mean Reversion":
            return None, {"Sharpe Ratio": 1.2}
        else:
            return None, {"Sharpe Ratio": 1.0}

    monkeypatch.setattr(
        "quant_trading_strategy_backtester.optimiser.load_yfinance_data_one_ticker",
        mock_load_data,
    )
    monkeypatch.setattr(
        "quant_trading_strategy_backtester.optimiser.run_backtest",
        mock_run_backtest,
    )

    start_date = datetime.date(2020, 1, 1)
    end_date = datetime.date(2020, 12, 31)
    strategy_type = "Moving Average Crossover"
    strategy_params = {"short_window": 10, "long_window": 50}

    best_ticker = optimise_single_ticker_strategy_ticker(
        mock_top_companies, start_date, end_date, strategy_type, strategy_params
    )

    assert isinstance(best_ticker, str)
    assert best_ticker in [company[0] for company in mock_top_companies]


def test_prepare_single_ticker_strategy_with_optimisation(monkeypatch):
    # Mock data and functions
    mock_polars_data = pl.DataFrame(
        {
            "Date": [datetime.date(2020, 1, i) for i in range(1, 32)],
            "Close": [100 + i for i in range(31)],
        }
    )
    mock_top_companies = [("AAPL", 1000000.0), ("GOOGL", 900000.0), ("MSFT", 800000.0)]

    def mock_get_top_companies(*args, **kwargs):
        return mock_top_companies

    def mock_optimise_single_ticker(*args, **kwargs):
        return "AAPL"

    def mock_load_data(*args, **kwargs):
        return mock_polars_data

    def mock_optimise_strategy_params(*args, **kwargs):
        return {"short_window": 15, "long_window": 60}, {"Sharpe Ratio": 1.8}

    monkeypatch.setattr(
        "quant_trading_strategy_backtester.strategy_preparation.get_top_sp500_companies",
        mock_get_top_companies,
    )
    monkeypatch.setattr(
        "quant_trading_strategy_backtester.strategy_preparation.optimise_single_ticker_strategy_ticker",
        mock_optimise_single_ticker,
    )
    monkeypatch.setattr(
        "quant_trading_strategy_backtester.strategy_preparation.load_yfinance_data_one_ticker",
        mock_load_data,
    )
    monkeypatch.setattr(
        "quant_trading_strategy_backtester.strategy_preparation.optimise_strategy_params",
        mock_optimise_strategy_params,
    )

    start_date = datetime.date(2020, 1, 1)
    end_date = datetime.date(2020, 12, 31)
    strategy_type = "Moving Average Crossover"
    strategy_params = {
        "short_window": range(5, 30, 5),
        "long_window": range(20, 100, 10),
    }
    optimise = True

    data, ticker_display, optimised_params = (
        prepare_single_ticker_strategy_with_optimisation(
            start_date, end_date, strategy_type, strategy_params, optimise
        )
    )

    assert isinstance(data, pl.DataFrame)
    assert isinstance(ticker_display, str)
    assert ticker_display == "AAPL"
    assert isinstance(optimised_params, dict)
    assert set(optimised_params.keys()) == {"short_window", "long_window"}
    assert optimised_params["short_window"] == 15
    assert optimised_params["long_window"] == 60


def test_prepare_single_ticker_strategy_with_optimisation_no_param_optimisation(
    monkeypatch,
):
    # Mock data and functions
    mock_polars_data = pl.DataFrame(
        {
            "Date": [datetime.date(2020, 1, i) for i in range(1, 32)],
            "Close": [100 + i for i in range(31)],
        }
    )
    mock_top_companies = [("AAPL", 1000000.0), ("GOOGL", 900000.0), ("MSFT", 800000.0)]

    def mock_get_top_companies(*args, **kwargs):
        return mock_top_companies

    def mock_optimise_single_ticker(*args, **kwargs):
        return "AAPL"

    def mock_load_data(*args, **kwargs):
        return mock_polars_data

    def mock_optimise_strategy_params(*args, **kwargs):
        return {"short_window": 15, "long_window": 60}, {"Sharpe Ratio": 1.8}

    monkeypatch.setattr(
        "quant_trading_strategy_backtester.strategy_preparation.get_top_sp500_companies",
        mock_get_top_companies,
    )
    monkeypatch.setattr(
        "quant_trading_strategy_backtester.strategy_preparation.optimise_single_ticker_strategy_ticker",
        mock_optimise_single_ticker,
    )
    monkeypatch.setattr(
        "quant_trading_strategy_backtester.strategy_preparation.load_yfinance_data_one_ticker",
        mock_load_data,
    )

    start_date = datetime.date(2020, 1, 1)
    end_date = datetime.date(2020, 12, 31)
    strategy_type = "Moving Average Crossover"
    strategy_params = {"short_window": 10, "long_window": 50}
    optimise = False

    data, ticker_display, final_params = (
        prepare_single_ticker_strategy_with_optimisation(
            start_date, end_date, strategy_type, strategy_params, optimise
        )
    )

    assert isinstance(data, pl.DataFrame)
    assert isinstance(ticker_display, str)
    assert ticker_display == "AAPL"
    assert isinstance(final_params, dict)
    assert final_params == strategy_params  # Parameters should remain unchanged
