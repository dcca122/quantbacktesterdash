"""Example script demonstrating usage of ``get_historical_vix``."""

from .vix_calculator import get_historical_vix

# Optional: direct script test (does nothing unless run as script)
if __name__ == "__main__":
    vix_df = get_historical_vix('AAPL', window=30, start='2022-01-01', end='2024-01-01')
    print(vix_df.head())
