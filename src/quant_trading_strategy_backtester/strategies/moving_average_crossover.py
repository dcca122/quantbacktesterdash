"""Triple EMA (TEMO) crossover strategy implementation."""

from typing import Any

import polars as pl

from quant_trading_strategy_backtester.strategies.base import BaseStrategy


class MovingAverageCrossoverStrategy(BaseStrategy):
    """Triple EMA (TEMO) crossover strategy.

    The strategy enters long when the 10-period EMA crosses above the
    80-period EMA and both the ADX and Chande Momentum Oscillator (CMO)
    confirm strong momentum. Short entries use the opposite conditions.
    Position size defaults to 3% of capital per trade.
    """

    def __init__(self, params: dict[str, Any]):
        super().__init__(params)
        self.position_size = float(params.get("position_size", 0.03))
        self.adx_period = int(params.get("adx_period", 14))
        self.cmo_period = int(params.get("cmo_period", 14))
        self.atr_period = int(params.get("atr_period", 14))

    def _calculate_indicators(self, df: pl.DataFrame) -> pl.DataFrame:
        df = df.with_columns(
            [
                pl.col("Close").ewm_mean(span=10).alias("ema_10"),
                pl.col("Close").ewm_mean(span=80).alias("ema_80"),
                pl.col("Close").ewm_mean(span=20).alias("ema_20"),
                pl.col("Close").ewm_mean(span=70).alias("ema_70"),
            ]
        )

        true_range = pl.max_horizontal(
            [
                pl.col("High") - pl.col("Low"),
                (pl.col("High") - pl.col("Close").shift(1)).abs(),
                (pl.col("Low") - pl.col("Close").shift(1)).abs(),
            ]
        )
        df = df.with_columns(true_range.alias("tr"))
        df = df.with_columns(
            pl.col("tr")
            .rolling_mean(self.atr_period, min_periods=self.atr_period)
            .alias("atr")
        )

        up_move = pl.col("High") - pl.col("High").shift(1)
        down_move = pl.col("Low").shift(1) - pl.col("Low")
        plus_dm = (
            pl.when((up_move > down_move) & (up_move > 0)).then(up_move).otherwise(0)
        )
        minus_dm = (
            pl.when((down_move > up_move) & (down_move > 0))
            .then(down_move)
            .otherwise(0)
        )
        df = df.with_columns([plus_dm.alias("plus_dm"), minus_dm.alias("minus_dm")])
        df = df.with_columns(
            [
                pl.col("plus_dm").rolling_sum(self.adx_period).alias("plus_dm_sum"),
                pl.col("minus_dm").rolling_sum(self.adx_period).alias("minus_dm_sum"),
            ]
        )
        df = df.with_columns(
            [
                (100 * pl.col("plus_dm_sum") / pl.col("atr")).alias("plus_di"),
                (100 * pl.col("minus_dm_sum") / pl.col("atr")).alias("minus_di"),
            ]
        )
        df = df.with_columns(
            (
                (
                    (pl.col("plus_di") - pl.col("minus_di")).abs()
                    / (pl.col("plus_di") + pl.col("minus_di"))
                )
                * 100
            ).alias("dx")
        )
        df = df.with_columns(
            pl.col("dx")
            .rolling_mean(self.adx_period, min_periods=self.adx_period)
            .alias("adx")
        )

        delta = pl.col("Close") - pl.col("Close").shift(1)
        gains = pl.when(delta > 0).then(delta).otherwise(0)
        losses = pl.when(delta < 0).then(-delta).otherwise(0)
        df = df.with_columns([gains.alias("gain"), losses.alias("loss")])
        df = df.with_columns(
            [
                pl.col("gain").rolling_sum(self.cmo_period).alias("gain_sum"),
                pl.col("loss").rolling_sum(self.cmo_period).alias("loss_sum"),
            ]
        )
        df = df.with_columns(
            (
                100
                * (pl.col("gain_sum") - pl.col("loss_sum"))
                / (pl.col("gain_sum") + pl.col("loss_sum"))
            ).alias("cmo")
        )
        return df

    def generate_signals(self, data: pl.DataFrame) -> pl.DataFrame:
        """Generate trading signals based on TEMO crossover rules."""
        if data.is_empty():
            return pl.DataFrame(
                schema=[
                    ("Date", pl.Date),
                    ("Close", pl.Float64),
                    ("signal", pl.Float64),
                    ("positions", pl.Float64),
                ]
            )

        df = self._calculate_indicators(data)

        long_cond = (
            (pl.col("ema_10") > pl.col("ema_80"))
            & (pl.col("adx") > 40)
            & (pl.col("cmo") > 40)
        )
        short_cond = (
            (pl.col("ema_10") < pl.col("ema_80"))
            & (pl.col("adx") > 40)
            & (pl.col("cmo") < -40)
        )

        df = df.with_columns(
            pl.when(long_cond)
            .then(1.0)
            .when(short_cond)
            .then(-1.0)
            .otherwise(0.0)
            .alias("signal")
        )
        df = df.with_columns(pl.col("signal").diff().fill_null(0.0).alias("positions"))
        df = df.with_columns(pl.lit(self.position_size).alias("position_size"))

        return df.select(
            [
                "Date",
                "Close",
                "ema_10",
                "ema_80",
                "ema_20",
                "ema_70",
                "atr",
                "adx",
                "cmo",
                "signal",
                "positions",
                "position_size",
            ]
        )
