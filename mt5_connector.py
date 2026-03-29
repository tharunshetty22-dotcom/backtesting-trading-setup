"""
mt5_connector.py – MetaTrader5 terminal integration.

Wraps the MetaTrader5 Python library with connection management,
data retrieval and error handling.  Imports are guarded so the rest
of the application degrades gracefully on platforms where the
MetaTrader5 package is not available (e.g. Linux CI environments).
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

import pandas as pd

from config import MT5_LOGIN, MT5_PASSWORD, MT5_PATH, MT5_SERVER, MT5_TIMEOUT, TIMEFRAMES

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional MT5 import – the library is only available on Windows
# ---------------------------------------------------------------------------

try:
    import MetaTrader5 as mt5  # type: ignore[import]
    MT5_AVAILABLE = True
except ImportError:  # pragma: no cover
    mt5 = None  # type: ignore[assignment]
    MT5_AVAILABLE = False
    logger.warning(
        "MetaTrader5 package not found.  MT5 features are unavailable.  "
        "Install it on a Windows machine with:  pip install MetaTrader5"
    )


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

class MT5ConnectionError(RuntimeError):
    """Raised when a connection to the MT5 terminal cannot be established."""


def is_available() -> bool:
    """Return True if the MetaTrader5 library is installed."""
    return MT5_AVAILABLE


def connect() -> bool:
    """
    Initialise and connect to the MT5 terminal.

    Returns True on success.
    Raises MT5ConnectionError on failure.
    """
    if not MT5_AVAILABLE:
        raise MT5ConnectionError(
            "MetaTrader5 package is not installed.  "
            "See README for installation instructions."
        )

    init_kwargs: dict = {"timeout": MT5_TIMEOUT}
    if MT5_PATH:
        init_kwargs["path"] = MT5_PATH
    if MT5_LOGIN:
        init_kwargs["login"] = MT5_LOGIN
    if MT5_PASSWORD:
        init_kwargs["password"] = MT5_PASSWORD
    if MT5_SERVER:
        init_kwargs["server"] = MT5_SERVER

    if not mt5.initialize(**init_kwargs):
        error = mt5.last_error()
        raise MT5ConnectionError(f"MT5 initialisation failed: {error}")

    logger.info("Connected to MetaTrader5 terminal.")
    return True


def disconnect() -> None:
    """Shut down the MT5 connection."""
    if MT5_AVAILABLE:
        mt5.shutdown()
        logger.info("Disconnected from MetaTrader5 terminal.")


def get_connection_status() -> dict:
    """
    Return a dict describing the current MT5 connection state.

    Keys: connected (bool), account (int|None), broker (str|None),
          balance (float|None), equity (float|None), error (str|None)
    """
    if not MT5_AVAILABLE:
        return {
            "connected": False,
            "account": None,
            "broker": None,
            "balance": None,
            "equity": None,
            "error": "MetaTrader5 package not installed.",
        }

    try:
        connect()
        info = mt5.account_info()
        if info is None:
            return {
                "connected": False,
                "account": None,
                "broker": None,
                "balance": None,
                "equity": None,
                "error": str(mt5.last_error()),
            }
        return {
            "connected": True,
            "account": info.login,
            "broker": info.company,
            "balance": round(info.balance, 2),
            "equity": round(info.equity, 2),
            "error": None,
        }
    except MT5ConnectionError as exc:
        return {
            "connected": False,
            "account": None,
            "broker": None,
            "balance": None,
            "equity": None,
            "error": str(exc),
        }


def get_symbols() -> list[str]:
    """
    Return a sorted list of all available trading symbols from MT5.

    Raises MT5ConnectionError if the terminal is unreachable.
    """
    connect()
    symbols = mt5.symbols_get()
    if symbols is None:
        raise MT5ConnectionError(f"Failed to retrieve symbols: {mt5.last_error()}")
    return sorted(s.name for s in symbols)


def get_ohlcv(
    symbol: str,
    timeframe: str,
    start: datetime,
    end: datetime,
) -> pd.DataFrame:
    """
    Fetch OHLCV bars from MT5 for *symbol* between *start* and *end*.

    Parameters
    ----------
    symbol    : MT5 symbol name, e.g. "EURUSD"
    timeframe : Timeframe string matching a key in config.TIMEFRAMES,
                e.g. "H1", "D1"
    start     : Inclusive start datetime (UTC)
    end       : Inclusive end datetime (UTC)

    Returns
    -------
    pd.DataFrame with columns: Open, High, Low, Close, Volume
                 indexed by datetime.

    Raises
    ------
    MT5ConnectionError  – terminal unreachable
    ValueError          – unknown timeframe or no data returned
    """
    connect()

    tf_name = TIMEFRAMES.get(timeframe.upper())
    if tf_name is None:
        raise ValueError(
            f"Unknown timeframe '{timeframe}'.  "
            f"Valid options: {list(TIMEFRAMES.keys())}"
        )

    mt5_tf = getattr(mt5, tf_name)
    rates = mt5.copy_rates_range(symbol, mt5_tf, start, end)

    if rates is None or len(rates) == 0:
        err = mt5.last_error()
        raise ValueError(
            f"No data returned for {symbol} {timeframe} "
            f"({start.date()} – {end.date()}).  MT5 error: {err}"
        )

    df = pd.DataFrame(rates)
    df["time"] = pd.to_datetime(df["time"], unit="s", utc=True)
    df.set_index("time", inplace=True)
    df.rename(
        columns={
            "open":       "Open",
            "high":       "High",
            "low":        "Low",
            "close":      "Close",
            "tick_volume": "Volume",
        },
        inplace=True,
    )
    df = df[["Open", "High", "Low", "Close", "Volume"]]
    return df


def get_account_info() -> Optional[dict]:
    """
    Return basic account information or None if unavailable.
    """
    if not MT5_AVAILABLE:
        return None
    try:
        connect()
        info = mt5.account_info()
        if info is None:
            return None
        return {
            "login":    info.login,
            "name":     info.name,
            "company":  info.company,
            "currency": info.currency,
            "balance":  round(info.balance, 2),
            "equity":   round(info.equity, 2),
            "margin":   round(info.margin, 2),
        }
    except MT5ConnectionError:
        return None
