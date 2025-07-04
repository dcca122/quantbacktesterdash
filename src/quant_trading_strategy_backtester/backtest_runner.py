"""Utility functions for running backtests and creating strategy instances."""

from typing import Any, List, Union

import polars as pl

from quant_trading_strategy_backtester.backtester import Backtester
from quant_trading_strategy_backtester.strategies.base import (
    TRADING_STRATEGIES,
    BaseStrategy,
)
from quant_trading_strategy_backtester.strategies.buy_and_hold import BuyAndHoldStrategy
from quant_trading_strategy_backtester.strategies.mean_reversion import (
    MeanReversionStrategy,
)
from quant_trading_strategy_backtester.strategies.moving_average_crossover import (
    MovingAverageCrossoverStrategy,
)
from quant_trading_strategy_backtester.strategies.pairs_trading import (
    PairsTradingStrategy,
)


def run_backtest(
    data: pl.DataFrame,
    strategy_type: str,
    strategy_params: dict[str, Any],
    tickers: Union[str, List[str]],
) -> tuple[pl.DataFrame, dict]:
    """Execute the backtest using the given strategy and parameters."""
    strategy = create_strategy(strategy_type, strategy_params)
    backtester = Backtester(data, strategy, tickers=tickers)
    results = backtester.run()
    metrics = backtester.get_performance_metrics()
    assert (
        metrics is not None
    ), "No results available for the selected ticker and date range"
    return results, metrics


def create_strategy(
    strategy_type: str, strategy_params: dict[str, Any]
) -> BaseStrategy:
    """Create a trading strategy instance based on ``strategy_type``."""
    if strategy_type not in TRADING_STRATEGIES:
        raise ValueError("Invalid strategy type")

    match strategy_type:
        case "Buy and Hold":
            return BuyAndHoldStrategy(strategy_params)
        case "Moving Average Crossover":
            return MovingAverageCrossoverStrategy(strategy_params)
        case "Mean Reversion":
            return MeanReversionStrategy(strategy_params)
        case "Pairs Trading":
            return PairsTradingStrategy(strategy_params)
        case _:
            raise ValueError(f"Unexpected strategy type: {strategy_type}")
