import numpy as np
import pandas as pd
import yfinance as yf

def get_historical_vix(ticker, window=30, start=None, end=None):
    """
    Computes VIX-style (annualized window-day rolling historical volatility) for any ticker.
    Returns: pd.DataFrame with Date and VIX columns.
    """
    df = yf.download(ticker, start=start, end=end, auto_adjust=True)
    df['Return'] = np.log(df['Close'] / df['Close'].shift(1))
    df['RealizedVol'] = df['Return'].rolling(window).std() * np.sqrt(252)  # annualized
    df['VIX'] = df['RealizedVol'] * 100  # convert to percent
    vix_df = df[['VIX']].dropna().reset_index()
    return vix_df
