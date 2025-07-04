"""Utility functions for the quant_desk_tools package."""

from __future__ import annotations

import numpy as np
import pandas as pd
import yfinance as yf


def get_historical_vix(ticker: str, window: int = 30, start: str | None = None, end: str | None = None) -> pd.DataFrame:
    """Return VIX-style historical volatility for a ticker.

    Parameters
    ----------
    ticker : str
        The symbol to download data for.
    window : int, default 30
        Rolling window used to calculate volatility.
    start, end : str | None, optional
        Start and end dates in ``YYYY-MM-DD`` format.

    Returns
    -------
    pandas.DataFrame
        DataFrame containing ``Date`` and ``VIX`` columns.
    """
    df = yf.download(ticker, start=start, end=end, auto_adjust=True)
    df["Return"] = np.log(df["Close"] / df["Close"].shift(1))
    df["RealizedVol"] = df["Return"].rolling(window).std() * np.sqrt(252)
    df["VIX"] = df["RealizedVol"] * 100
    return df[["VIX"]].dropna().reset_index()
