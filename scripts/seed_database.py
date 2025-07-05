"""Seed the database with example data."""

from __future__ import annotations

import json
from datetime import date

from quant_trading_strategy_backtester.models import Session, StrategyModel


def seed() -> None:
    session = Session()
    if session.query(StrategyModel).first():
        print("Database already seeded.")
        session.close()
        return

    example = StrategyModel(
        name="DemoStrategy",
        parameters=json.dumps({"example_param": 1}),
        total_return=0.1,
        sharpe_ratio=1.2,
        max_drawdown=-0.05,
        tickers=json.dumps(["AAPL"]),
        start_date=date(2020, 1, 1),
        end_date=date(2020, 12, 31),
    )
    session.add(example)
    session.commit()
    session.close()
    print("Seed data inserted.")


if __name__ == "__main__":
    seed()
