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

## Running Tests

Execute the test suite from the project root using [pytest](https://docs.pytest.org/):

```bash
uv run -m pytest -v
```

This will run all unit tests and display verbose output.
