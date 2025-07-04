"""
Contains tests for optimisation functions.
"""

import datetime

import polars as pl

from quant_trading_strategy_backtester.optimiser import (
    optimise_buy_and_hold_ticker,
    optimise_pairs_trading_tickers,
    run_optimisation,
)
from quant_trading_strategy_backtester.strategy_preparation import (
    prepare_buy_and_hold_strategy_with_optimisation,
    prepare_pairs_trading_strategy_with_optimisation,
)


def test_optimise_buy_and_hold_ticker(monkeypatch):
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
        return None, {"Total Return": 0.3, "Sharpe Ratio": 1.5, "Max Drawdown": -0.1}

    monkeypatch.setattr(
        "quant_trading_strategy_backtester.optimiser_core.load_yfinance_data_one_ticker",
        mock_load_data,
    )
    monkeypatch.setattr(
        "quant_trading_strategy_backtester.optimiser_core.run_backtest",
        mock_run_backtest,
    )

    start_date = datetime.date(2020, 1, 1)
    end_date = datetime.date(2020, 12, 31)

    best_ticker, params, metrics = optimise_buy_and_hold_ticker(
        mock_top_companies, start_date, end_date
    )

    assert isinstance(best_ticker, str)
    assert best_ticker in [company[0] for company in mock_top_companies]
    assert isinstance(params, dict)
    assert len(params) == 0  # Buy and Hold has no parameters
    assert isinstance(metrics, dict)
    assert "Total Return" in metrics
    assert "Sharpe Ratio" in metrics
    assert "Max Drawdown" in metrics


def test_run_optimisation_buy_and_hold(monkeypatch):
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

    def mock_optimise_buy_and_hold(*args, **kwargs):
        return (
            "AAPL",
            {},
            {"Total Return": 0.3, "Sharpe Ratio": 1.5, "Max Drawdown": -0.1},
        )

    monkeypatch.setattr(
        "quant_trading_strategy_backtester.optimiser.get_top_sp500_companies",
        mock_get_top_companies,
    )
    monkeypatch.setattr(
        "quant_trading_strategy_backtester.optimiser.optimise_buy_and_hold_ticker",
        mock_optimise_buy_and_hold,
    )

    strategy_type = "Buy and Hold"
    initial_params: dict[str, float] = {}  # Buy and Hold has no parameters
    start_date = datetime.date(2020, 1, 1)
    end_date = datetime.date(2020, 12, 31)

    optimised_params, metrics = run_optimisation(
        mock_polars_data, strategy_type, initial_params, start_date, end_date, "AAPL"
    )

    assert isinstance(optimised_params, dict)
    assert len(optimised_params) == 0  # Buy and Hold has no parameters
    assert isinstance(metrics, dict)
    assert "Total Return" in metrics
    assert "Sharpe Ratio" in metrics
    assert "Max Drawdown" in metrics


def test_prepare_buy_and_hold_strategy_with_optimisation(monkeypatch):
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

    def mock_optimise_buy_and_hold(*args, **kwargs):
        return (
            "AAPL",
            {},
            {"Total Return": 0.3, "Sharpe Ratio": 1.5, "Max Drawdown": -0.1},
        )

    def mock_load_data(*args, **kwargs):
        return mock_polars_data

    monkeypatch.setattr(
        "quant_trading_strategy_backtester.strategy_preparation.get_top_sp500_companies",
        mock_get_top_companies,
    )
    monkeypatch.setattr(
        "quant_trading_strategy_backtester.strategy_preparation.optimise_buy_and_hold_ticker",
        mock_optimise_buy_and_hold,
    )
    monkeypatch.setattr(
        "quant_trading_strategy_backtester.strategy_preparation.load_yfinance_data_one_ticker",
        mock_load_data,
    )

    start_date = datetime.date(2020, 1, 1)
    end_date = datetime.date(2020, 12, 31)
    data, ticker_display, strategy_params = (
        prepare_buy_and_hold_strategy_with_optimisation(start_date, end_date)
    )

    assert isinstance(data, pl.DataFrame)
    assert isinstance(ticker_display, str)
    assert ticker_display == "AAPL"
    assert isinstance(strategy_params, dict)
    assert len(strategy_params) == 0  # Buy and Hold has no parameters


def test_optimise_pairs_trading_tickers(monkeypatch):
    # Mock data and functions
    mock_top_companies = [("AAPL", 1000000.0), ("GOOGL", 900000.0), ("MSFT", 800000.0)]
    mock_polars_data = pl.DataFrame(
        {"Close_1": [100, 101, 102], "Close_2": [200, 202, 204]}
    )

    def mock_load_data(*args, **kwargs):
        return mock_polars_data

    def mock_run_backtest(*args, **kwargs):
        return None, {"Sharpe Ratio": 1.5}

    def mock_optimise_strategy_params(*args, **kwargs):
        return {"window": 25, "entry_z_score": 2.5, "exit_z_score": 0.6}, {
            "Sharpe Ratio": 1.8
        }

    monkeypatch.setattr(
        "quant_trading_strategy_backtester.optimiser_core.load_yfinance_data_two_tickers",
        mock_load_data,
    )
    monkeypatch.setattr(
        "quant_trading_strategy_backtester.optimiser_core.run_backtest",
        mock_run_backtest,
    )
    monkeypatch.setattr(
        "quant_trading_strategy_backtester.optimiser.optimise_strategy_params",
        mock_optimise_strategy_params,
    )
    monkeypatch.setattr(
        "quant_trading_strategy_backtester.optimiser_core.optimise_strategy_params",
        mock_optimise_strategy_params,
    )
    monkeypatch.setattr(
        "quant_trading_strategy_backtester.optimiser.optimise_strategy_params",
        mock_optimise_strategy_params,
    )
    monkeypatch.setattr(
        "quant_trading_strategy_backtester.optimiser.optimise_strategy_params",
        mock_optimise_strategy_params,
    )

    start_date = datetime.date(2020, 1, 1)
    end_date = datetime.date(2020, 12, 31)
    strategy_params = {"window": 20, "entry_z_score": 2.0, "exit_z_score": 0.5}
    # Test with optimisation
    best_pair, best_params, _ = optimise_pairs_trading_tickers(
        mock_top_companies, start_date, end_date, strategy_params, True
    )

    assert isinstance(best_pair, tuple)
    assert len(best_pair) == 2
    assert all(
        ticker in [company[0] for company in mock_top_companies] for ticker in best_pair
    )
    assert isinstance(best_params, dict)
    assert set(best_params.keys()) == set(strategy_params.keys())
    assert best_params["window"] == 25  # Optimised value

    # Test without optimisation
    best_pair, best_params, _ = optimise_pairs_trading_tickers(
        mock_top_companies, start_date, end_date, strategy_params, False
    )

    assert isinstance(best_pair, tuple)
    assert len(best_pair) == 2
    assert all(
        ticker in [company[0] for company in mock_top_companies] for ticker in best_pair
    )
    assert isinstance(best_params, dict)
    # Should be the same as input when not optimising
    assert best_params == strategy_params


def test_handle_pairs_trading_optimisation(monkeypatch):
    # Mock data and functions
    mock_polars_data = pl.DataFrame(
        {"Close_1": [100, 101, 102], "Close_2": [200, 202, 204]}
    )
    mock_top_companies = [("AAPL", 1000000), ("GOOGL", 900000), ("MSFT", 800000)]

    def mock_get_top_companies(*args, **kwargs):
        return mock_top_companies

    def mock_optimise_pairs(*args, **kwargs):
        return (
            ("AAPL", "GOOGL"),
            {"window": 20, "entry_z_score": 2.0, "exit_z_score": 0.5},
            None,
        )

    def mock_load_data(*args, **kwargs):
        return mock_polars_data

    def mock_run_optimisation(*args, **kwargs):
        return (
            {"window": 20, "entry_z_score": 2.0, "exit_z_score": 0.5},
            {"Sharpe Ratio": 1.5, "Total Return": 0.2, "Max Drawdown": -0.1},
        )

    monkeypatch.setattr(
        "quant_trading_strategy_backtester.strategy_preparation.get_top_sp500_companies",
        mock_get_top_companies,
    )
    monkeypatch.setattr(
        "quant_trading_strategy_backtester.strategy_preparation.optimise_pairs_trading_tickers",
        mock_optimise_pairs,
    )
    monkeypatch.setattr(
        "quant_trading_strategy_backtester.strategy_preparation.load_yfinance_data_two_tickers",
        mock_load_data,
    )
    monkeypatch.setattr(
        "quant_trading_strategy_backtester.strategy_preparation.run_optimisation",
        mock_run_optimisation,
    )

    start_date = datetime.date(2020, 1, 1)
    end_date = datetime.date(2020, 12, 31)
    strategy_params = {
        "window": range(10, 31),
        "entry_z_score": [1.5, 2.0, 2.5],
        "exit_z_score": [0.3, 0.5, 0.7],
    }

    data, ticker_display, optimised_params = (
        prepare_pairs_trading_strategy_with_optimisation(
            start_date, end_date, strategy_params, True
        )
    )

    assert isinstance(data, pl.DataFrame)
    assert ticker_display == "AAPL vs. GOOGL"
    assert isinstance(optimised_params, dict)
    assert set(optimised_params.keys()) == set(strategy_params.keys())
    assert optimised_params["window"] == 20
    assert optimised_params["entry_z_score"] == 2.0
    assert optimised_params["exit_z_score"] == 0.5


def test_run_optimisation(monkeypatch):
    # Mock data and functions
    mock_polars_data = pl.DataFrame({"Close": [100, 101, 102]})

    def mock_optimise_strategy_params(*args, **kwargs):
        return {"window": 25, "std_dev": 2.5}, {"Sharpe Ratio": 1.8}

    monkeypatch.setattr(
        "quant_trading_strategy_backtester.optimiser_core.optimise_strategy_params",
        mock_optimise_strategy_params,
    )

    strategy_type = "Mean Reversion"
    initial_params = {"window": 20, "std_dev": 2.0}
    start_date = datetime.date(2020, 1, 1)
    end_date = datetime.date(2020, 12, 31)
    ticker = "AAPL"

    optimised_params, metrics = run_optimisation(
        mock_polars_data,
        strategy_type,
        initial_params,
        start_date,
        end_date,
        ticker,
    )

    assert isinstance(optimised_params, dict)
    assert set(optimised_params.keys()) == set(initial_params.keys())
    assert isinstance(metrics, dict)
    assert "Sharpe Ratio" in metrics
