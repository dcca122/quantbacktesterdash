"""
Tests for the base strategy class.
"""

from typing import Any

import polars as pl
import pytest

from quant_trading_strategy_backtester.strategies.base import BaseStrategy
from quant_trading_strategy_backtester.strategies.mean_reversion import (
    MeanReversionStrategy,
)
from quant_trading_strategy_backtester.strategies.moving_average_crossover import (
    MovingAverageCrossoverStrategy,
)
from quant_trading_strategy_backtester.strategies.pairs_trading import (
    PairsTradingStrategy,
)


@pytest.mark.parametrize(
    "strategy_class,params",
    [
        (MovingAverageCrossoverStrategy, {}),
        (MeanReversionStrategy, {"window": 5, "std_dev": 2.0}),
        (
            PairsTradingStrategy,
            {"window": 20, "entry_z_score": 2.0, "exit_z_score": 0.5},
        ),
    ],
)
def test_strategy_with_empty_data(
    strategy_class: BaseStrategy, params: dict[str, Any]
) -> None:
    empty_data = pl.DataFrame(
        schema=(
            [("Close", pl.Float64)]
            if strategy_class != PairsTradingStrategy
            else [("Close_1", pl.Float64), ("Close_2", pl.Float64)]
        )
    )
    strategy = strategy_class(params)  # type: ignore
    signals = strategy.generate_signals(empty_data)

    assert isinstance(signals, pl.DataFrame)
    assert "Date" in signals.columns
    assert "signal" in signals.columns
    assert "positions" in signals.columns
    assert signals.is_empty()
    assert signals.is_empty()
