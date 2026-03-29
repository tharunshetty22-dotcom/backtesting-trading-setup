"""
backtester.py – Core backtesting engine.

Executes a user-provided strategy against a DataFrame of OHLCV data and
returns a list of closed trades plus final metrics.
"""

import types
import pandas as pd
import numpy as np

from metrics import calculate_metrics


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def run_backtest(
    strategy_source: str,
    df: pd.DataFrame,
    starting_capital: float = 1_000.0,
    position_size_pct: float = 100.0,
) -> dict:
    """
    Execute *strategy_source* against *df* and return metrics.

    Parameters
    ----------
    strategy_source : str
        Python source code of the strategy.  Must expose
        ``generate_signals(df) -> pd.DataFrame`` that adds a
        ``signal`` column with values 1 (buy), -1 (sell), 0 (hold).
    df : pd.DataFrame
        OHLCV data with at least a ``Close`` column.
    starting_capital : float
        Initial portfolio value in USD.
    position_size_pct : float
        Percentage of available capital to use per trade (1–100).

    Returns
    -------
    dict  – metrics dict from ``metrics.calculate_metrics``
    """
    df = _prepare_dataframe(df)
    strategy_module = _load_strategy(strategy_source)
    df = strategy_module.generate_signals(df)

    if "signal" not in df.columns:
        raise ValueError("generate_signals() must add a 'signal' column to the DataFrame.")

    trades = _simulate_trades(df, starting_capital, position_size_pct / 100.0)
    return calculate_metrics(trades, starting_capital)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _prepare_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Normalise column names and ensure required columns exist."""
    df = df.copy()
    df.columns = [c.strip().title() for c in df.columns]

    required = {"Close"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Data is missing required columns: {missing}")

    df.sort_index(inplace=True)
    df.dropna(subset=["Close"], inplace=True)
    return df


def _load_strategy(source: str) -> types.ModuleType:
    """Compile and execute strategy source, returning it as a module."""
    module = types.ModuleType("user_strategy")
    module.__dict__.update({"pd": pd, "np": np})
    exec(compile(source, "<strategy>", "exec"), module.__dict__)  # noqa: S102
    return module


def _simulate_trades(
    df: pd.DataFrame,
    starting_capital: float,
    size_fraction: float,
) -> list:
    """
    Walk through *df* row by row and simulate trades.

    Rules:
    - Signal  1: BUY  – open a long position if none is open.
    - Signal -1: SELL – close the open long position.
    - Signal  0: HOLD – do nothing.
    """
    trades = []
    capital = starting_capital
    position = None  # dict with keys: shares, entry_price, entry_capital

    for _idx, row in df.iterrows():
        signal = int(row.get("signal", 0))
        price = float(row["Close"])

        if signal == 1 and position is None and price > 0:
            invest = capital * size_fraction
            shares = invest / price
            position = {
                "shares": shares,
                "entry_price": price,
                "entry_capital": invest,
            }

        elif signal == -1 and position is not None:
            exit_value = position["shares"] * price
            pnl = exit_value - position["entry_capital"]
            trades.append({
                "entry_price": position["entry_price"],
                "exit_price": price,
                "pnl": pnl,
                "shares": position["shares"],
            })
            capital += pnl
            position = None

    # Force-close any open position at the last available price
    if position is not None:
        last_price = float(df["Close"].iloc[-1])
        exit_value = position["shares"] * last_price
        pnl = exit_value - position["entry_capital"]
        trades.append({
            "entry_price": position["entry_price"],
            "exit_price": last_price,
            "pnl": pnl,
            "shares": position["shares"],
        })

    return trades
