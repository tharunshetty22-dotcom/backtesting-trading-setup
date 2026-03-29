"""
mt5_connector.py – MetaTrader5 terminal integration.

Provides helpers to:
- Connect / disconnect from the MT5 terminal
- Fetch historical OHLCV data as a pandas DataFrame
- List available trading symbols
- Retrieve account balance and equity

MT5 is a Windows-only library.  On other platforms the module degrades
gracefully so that the rest of the application can still import it – any
attempt to actually use MT5 features will raise a RuntimeError.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

import pandas as pd

try:
    import MetaTrader5 as mt5
    _MT5_AVAILABLE = True
except ImportError:
    mt5 = None  # type: ignore[assignment]
    _MT5_AVAILABLE = False

from config import (
    DEFAULT_BARS,
    MT5_LOGIN,
    MT5_PASSWORD,
    MT5_SERVER,
    TIMEFRAMES,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Connection management
# ---------------------------------------------------------------------------

def connect(
    login: int = MT5_LOGIN,
    password: str = MT5_PASSWORD,
    server: str = MT5_SERVER,
) -> bool:
    """
    Initialise a connection to the MetaTrader5 terminal.

    Returns True on success, False on failure.
    Raises RuntimeError if the MetaTrader5 package is not installed.
    """
    _require_mt5()

    kwargs: dict = {}
    if login:
        kwargs["login"] = login
    if password:
        kwargs["password"] = password
    if server:
        kwargs["server"] = server

    if not mt5.initialize(**kwargs):  # type: ignore[union-attr]
        err = mt5.last_error()  # type: ignore[union-attr]
        logger.error("MT5 initialise failed: %s", err)
        return False

    info = mt5.account_info()  # type: ignore[union-attr]
    if info:
        logger.info(
            "Connected to MT5 – account %s on %s (balance %.2f)",
            info.login,
            info.server,
            info.balance,
        )
    return True


def disconnect() -> None:
    """Shut down the connection to the MT5 terminal."""
    if _MT5_AVAILABLE and mt5 is not None:
        mt5.shutdown()
        logger.info("MT5 connection closed.")


# ---------------------------------------------------------------------------
# Symbol helpers
# ---------------------------------------------------------------------------

def get_symbols(group: str = "") -> list[str]:
    """
    Return a list of symbol names available in the MT5 terminal.

    Parameters
    ----------
    group : str
        Optional wildcard filter, e.g. ``"*USD*"``.  Passed directly to
        ``mt5.symbols_get(group=…)``.

    Returns a sorted list of symbol name strings.
    """
    _require_mt5()
    symbols = mt5.symbols_get(group=group) if group else mt5.symbols_get()  # type: ignore[union-attr]
    if symbols is None:
        return []
    return sorted(s.name for s in symbols)


# ---------------------------------------------------------------------------
# Historical data
# ---------------------------------------------------------------------------

def fetch_ohlcv(
    symbol: str,
    timeframe: str = "H1",
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    bars: int = DEFAULT_BARS,
) -> pd.DataFrame:
    """
    Fetch OHLCV data from the MT5 terminal and return a pandas DataFrame.

    Parameters
    ----------
    symbol    : Trading symbol, e.g. ``"EURUSD"``.
    timeframe : One of the keys in ``config.TIMEFRAMES`` (e.g. ``"H1"``).
    start     : Start of the date range (UTC). If *None*, the most recent
                ``bars`` candles are returned.
    end       : End of the date range (UTC). Defaults to *now* when ``start``
                is provided.
    bars      : Number of bars to fetch when no date range is given.

    Returns
    -------
    pd.DataFrame with columns [Open, High, Low, Close, Volume] and a
    DatetimeIndex in UTC.

    Raises
    ------
    RuntimeError  – MT5 package not installed or not connected.
    ValueError    – Unknown timeframe or no data returned.
    """
    _require_mt5()

    tf_const = _resolve_timeframe(timeframe)

    if start is not None:
        _end = end or datetime.now(tz=timezone.utc)
        # Ensure timezone-aware datetimes
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        if _end.tzinfo is None:
            _end = _end.replace(tzinfo=timezone.utc)
        rates = mt5.copy_rates_range(symbol, tf_const, start, _end)  # type: ignore[union-attr]
    else:
        rates = mt5.copy_rates_from_pos(symbol, tf_const, 0, bars)  # type: ignore[union-attr]

    if rates is None or len(rates) == 0:
        err = mt5.last_error()  # type: ignore[union-attr]
        raise ValueError(
            f"No data returned for {symbol}/{timeframe}. MT5 error: {err}"
        )

    df = pd.DataFrame(rates)
    df["time"] = pd.to_datetime(df["time"], unit="s", utc=True)
    df.set_index("time", inplace=True)
    df.rename(
        columns={
            "open": "Open",
            "high": "High",
            "low": "Low",
            "close": "Close",
            "tick_volume": "Volume",
        },
        inplace=True,
    )
    # Keep only OHLCV columns (drop spread / real_volume if present)
    keep = [c for c in ["Open", "High", "Low", "Close", "Volume"] if c in df.columns]
    return df[keep]


# ---------------------------------------------------------------------------
# Account information
# ---------------------------------------------------------------------------

def get_account_info() -> dict:
    """
    Return a dict with account balance, equity, and server name.

    Returns an empty dict if not connected.
    """
    _require_mt5()
    info = mt5.account_info()  # type: ignore[union-attr]
    if info is None:
        return {}
    return {
        "login": info.login,
        "server": info.server,
        "balance": info.balance,
        "equity": info.equity,
        "currency": info.currency,
    }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _require_mt5() -> None:
    """Raise RuntimeError when the MetaTrader5 package is unavailable."""
    if not _MT5_AVAILABLE or mt5 is None:
        raise RuntimeError(
            "The MetaTrader5 Python package is not installed. "
            "Install it with: pip install MetaTrader5  "
            "(Windows only – requires a running MT5 terminal)."
        )


def _resolve_timeframe(name: str):
    """Return the mt5.TIMEFRAME_* constant for *name*."""
    canonical = name.upper()
    if canonical not in TIMEFRAMES:
        raise ValueError(
            f"Unknown timeframe '{name}'. "
            f"Valid options: {', '.join(TIMEFRAMES)}"
        )
    attr_name = TIMEFRAMES[canonical]   # e.g. "TIMEFRAME_H1"
    const = getattr(mt5, attr_name, None)
    if const is None:
        raise RuntimeError(
            f"MetaTrader5 has no attribute '{attr_name}'. "
            "Ensure the MetaTrader5 package is properly installed."
        )
    return const
