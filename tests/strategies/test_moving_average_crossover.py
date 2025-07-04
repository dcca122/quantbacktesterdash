"""
Tests for the Moving Average Crossover strategy class.
"""

from datetime import date, timedelta

import polars as pl

from quant_trading_strategy_backtester.strategies.moving_average_crossover import (
    MovingAverageCrossoverStrategy,
)


def test_moving_average_crossover_strategy_initialisation() -> None:
    params = {"position_size": 0.05}
    strategy = MovingAverageCrossoverStrategy(params)
    assert strategy.position_size == 0.05


def test_moving_average_crossover_strategy_generate_signals(
    mock_polars_data: pl.DataFrame,
) -> None:
    params: dict[str, float] = {}
    strategy = MovingAverageCrossoverStrategy(params)
    signals = strategy.generate_signals(mock_polars_data)
    assert isinstance(signals, pl.DataFrame)
    EXPECTED_COLS = {"signal", "positions", "ema_10", "ema_80", "atr", "adx", "cmo"}
    for col in EXPECTED_COLS:
        assert col in signals.columns
    assert signals["signal"].is_in([-1.0, 0.0, 1.0]).all()


def test_moving_average_crossover_strategy_with_mock_polars_data():
    # Create mock data
    start_date = date(2023, 1, 1)
    dates = [start_date + timedelta(days=i) for i in range(100)]

    # Create a price series with a clear trend change
    prices = [100 + i for i in range(50)] + [  # Uptrend
        150 - i for i in range(50)
    ]  # Downtrend

    mock_polars_data = pl.DataFrame(
        {
            "Date": dates,
            "Open": prices,
            "High": [p + 1 for p in prices],
            "Low": [p - 1 for p in prices],
            "Close": prices,
        }
    )

    # Strategy parameters
    params = {}
    strategy = MovingAverageCrossoverStrategy(params)

    # Generate signals
    signals = strategy.generate_signals(mock_polars_data)

    # Ensure signals produce trades
    assert signals["signal"].abs().sum() > 0, "No trading signals generated"
    non_zero_positions = signals.filter(pl.col("positions") != 0)
    assert len(non_zero_positions) > 0, "No position changes"
