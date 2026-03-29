"""
sample_strategy.py – Template strategy for the backtesting platform.

HOW TO USE
----------
1. Copy this file and rename it (e.g. my_strategy.py).
2. Edit the logic inside ``generate_signals``.
3. Upload the file through the web UI and run the backtest.

RULES
-----
- The strategy file MUST define a function named ``generate_signals(df)``.
- ``df`` is a pandas DataFrame with OHLCV columns (Open, High, Low, Close, Volume).
- The function MUST add a ``signal`` column and return the modified DataFrame.
  - signal =  1  →  BUY
  - signal = -1  →  SELL
  - signal =  0  →  HOLD
- You may import: pandas, numpy.
- You may NOT import: os, sys, subprocess, socket, requests, etc.
"""

import pandas as pd
import numpy as np

STRATEGY_NAME = "SMA Crossover (20 / 50)"


def generate_signals(df: pd.DataFrame) -> pd.DataFrame:
    """
    Simple Moving Average crossover strategy.

    BUY  when the 20-day SMA crosses above the 50-day SMA.
    SELL when the 20-day SMA crosses below the 50-day SMA.
    """
    df = df.copy()

    # Compute moving averages
    df["sma_fast"] = df["Close"].rolling(window=20).mean()
    df["sma_slow"] = df["Close"].rolling(window=50).mean()

    # Default: hold
    df["signal"] = 0

    # Fast crosses above slow  → BUY
    df.loc[
        (df["sma_fast"] > df["sma_slow"]) &
        (df["sma_fast"].shift(1) <= df["sma_slow"].shift(1)),
        "signal",
    ] = 1

    # Fast crosses below slow  → SELL
    df.loc[
        (df["sma_fast"] < df["sma_slow"]) &
        (df["sma_fast"].shift(1) >= df["sma_slow"].shift(1)),
        "signal",
    ] = -1

    return df
