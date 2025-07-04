# Quant Trading Strategy Backtester

[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Test](https://github.com/IsaacCheng9/quant-trading-strategy-backtester/actions/workflows/test.yml/badge.svg)](https://github.com/IsaacCheng9/quant-trading-strategy-backtester/actions/workflows/test.yml)

A quantitative trading strategy backtester with an interactive dashboard.
Enables users to implement, test, and visualise trading strategies using
historical market data, featuring customisable parameters and key performance
metrics. Developed with Python.

_Try the deployed app
[here!](https://quant-trading-strategy-backtester.streamlit.app/)_

## Screenshots

![Pairs Trading without Optimisation 1](./resources/screenshots/pairs_trading_no_optimisation_1.png)
![Pairs Trading without Optimisation 2](./resources/screenshots/pairs_trading_no_optimisation_2.png)

<!-- markdownlint-disable-next-line MD033 -->
<details>
<!-- markdownlint-disable-next-line MD033 -->
<summary>Pairs Trading with Strategy Parameter Optimisation</summary>

![Pairs Trading ](./resources/screenshots/pairs_trading_optimised_strategy_parameters.png)

</details>

## Trading Strategies Supported

- Buy and Hold
- Mean Reversion
- Moving Average Crossover
- Pairs Trading

## Key Features

- Interactive web-based dashboard using Streamlit
- Efficient data processing using Polars for improved performance
- Support for multiple trading strategies with customisable parameters
- Real-time data fetching from Yahoo Finance
- Automatic optimisation of strategy parameters and stock selection from S&P 500
- Visualisation of equity curves and strategy returns
- Performance metrics including Total Return, Sharpe Ratio, and Max Drawdown
- Monthly performance table with rolling returns

## Performance Benchmark of pandas vs. Polars Implementation

I originally implemented the backtester and optimiser using
[pandas](https://pandas.pydata.org/), but I wanted to explore the performance
benefits of using [Polars](https://pola.rs/).

After refactoring the code to use Polars, I manually benchmarked the two
implementations on my local machine (Apple M1 Max with 10 CPU cores and 32 GPU
cores, 32 GB unified memory) and on the deployed Streamlit instance. Each run
was a backtest from 2020/01/01 to 2023/12/31 for the pairs trading strategy,
with ticker-pair optimisation amongst the top 20 S&P 500 stocks and parameter
optimisation enabled.

**Polars was faster by 2.1x on average compared to pandas on my local**
**machine, and faster by 1.8x on average on the Streamlit instance.**

![M1 Max Benchmark Results](./resources/m1_max_benchmark_results.png)

![Streamlit Benchmark Results](./resources/streamlit_benchmark_results.png)

The full benchmark results can be found in the CSV files in the
[resources folder](./resources).

## Usage

### Installing Dependencies

This project requires **Python 3.10 or higher**. To install the required
packages locally:

1. Install `uv` if you do not already have it:

   ```bash
   pip install uv
   ```

2. From the [project root](./) directory, install all dependencies (including
   development packages) with:

   ```bash
   uv sync --all-extras --dev
   ```

All dependencies are managed in [pyproject.toml](./pyproject.toml). To regenerate
`requirements.txt` from this file, run:

```bash
uv pip compile pyproject.toml > requirements.txt
```
The `requirements.txt` file is generated automatically from the project
configuration; edit `pyproject.toml` when adding or removing dependencies.

### Running the Application Locally

Run the following command from the [project root](./) directory:

```bash
uv run python -m quant_trading_strategy_backtester.app
```

### Database Setup

Database results are stored in a local `strategies.db` SQLite file. Schema
changes are handled with [Alembic](https://alembic.sqlalchemy.org/).

1. Initialise or upgrade the database schema:

   ```bash
   alembic upgrade head
   ```

2. To clear all tables for a clean state:

   ```bash
   uv run python -m quant_trading_strategy_backtester.utils
   ```

3. (Optional) seed the database with example data:

   ```bash
   uv run python scripts/seed_database.py
   ```

Tests use an in-memory database automatically, so no additional setup is
required.

### Running Tests

After installing the dependencies you can run the unit tests with
[pytest](https://docs.pytest.org/). Execute the following from the project root:

```bash
uv run -m pytest -v
```

If you do not wish to use `uv`, you can instead install dependencies with
`pip`:

```bash
pip install -r requirements.txt
pip install -e .  # ensure the package itself is available
pytest -v
```

### Formatting, Linting and Type Checking

Use the provided `Makefile` to keep the codebase consistent. After installing
the dependencies run:

```bash
make fmt       # format code with Black and apply Ruff fixes
make lint      # run Ruff linting
make typecheck # run mypy type checks
```

These checks run in CI, so ensure they pass before submitting changes.

### Rate Limiting Issues with Yahoo Finance

Note that you may encounter rate limiting issues with Yahoo Finance resulting in
slow data fetches in the app – unfortunately this is out of my control. You
could work around this by using a VPN, or wait for a while before trying again.
Sometimes upgrading the `yfinance` package to the latest version can also help.
