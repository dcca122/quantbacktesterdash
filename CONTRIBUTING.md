# Contributing

Thank you for taking the time to contribute to this project!

## Getting Started

1. **Clone the repository** and switch into the project directory.
2. **Install Python 3.10+** if it is not already available.
3. **Install `uv` and project dependencies**:

   ```bash
   pip install uv
   uv sync --all-extras --dev
   ```

   Alternatively you can install the dependencies with `pip`:

   ```bash
   pip install -r requirements.txt
   pip install -e .
 ```

## Running Tests

Execute the test suite from the project root using [pytest](https://docs.pytest.org/):

```bash
uv run -m pytest -v
```

This will run all unit tests and display verbose output.

## Troubleshooting

* **Module Not Found Errors**: Ensure the project package is installed in
  editable mode with `pip install -e .` so that tests can import
  `quant_trading_strategy_backtester`.
* **Missing Dependencies**: Re-run `uv sync --all-extras --dev` or
  `pip install -r requirements.txt` if imports fail.

## Running the Application

Launch the Streamlit dashboard from the project root with:

```bash
uv run python -m quant_trading_strategy_backtester.app
```

## Formatting, Linting and Type Checking

Use the provided `Makefile` targets before submitting a pull request:

```bash
make fmt       # apply Black and Ruff fixes
make lint      # run Ruff lint checks
make typecheck # run mypy type checks
```
