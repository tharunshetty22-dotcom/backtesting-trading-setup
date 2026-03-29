"""
config.py – Configuration for the backtesting platform and MT5 connection.

Edit the MT5_ACCOUNT, MT5_PASSWORD, and MT5_SERVER values to match your
MetaTrader5 broker account before running the application.
"""

# ---------------------------------------------------------------------------
# MT5 connection credentials
# These values can be overridden via environment variables:
#   MT5_LOGIN, MT5_PASSWORD, MT5_SERVER
# ---------------------------------------------------------------------------
import os

MT5_LOGIN: int = int(os.environ.get("MT5_LOGIN", 0))          # account number
MT5_PASSWORD: str = os.environ.get("MT5_PASSWORD", "")        # account password
MT5_SERVER: str = os.environ.get("MT5_SERVER", "")            # broker server name

# ---------------------------------------------------------------------------
# Supported timeframes
# Key  → label shown in the UI
# Value→ MetaTrader5 TIMEFRAME_* constant name
# ---------------------------------------------------------------------------
TIMEFRAMES: dict = {
    "M1":  "TIMEFRAME_M1",
    "M5":  "TIMEFRAME_M5",
    "M15": "TIMEFRAME_M15",
    "M30": "TIMEFRAME_M30",
    "H1":  "TIMEFRAME_H1",
    "H4":  "TIMEFRAME_H4",
    "D1":  "TIMEFRAME_D1",
    "W1":  "TIMEFRAME_W1",
    "MN":  "TIMEFRAME_MN1",
}

DEFAULT_TIMEFRAME: str = "H1"

# ---------------------------------------------------------------------------
# Data fetch settings
# ---------------------------------------------------------------------------
DEFAULT_BARS: int = 5000          # max bars to fetch when no date range given
DEFAULT_SYMBOL: str = "EURUSD"

# ---------------------------------------------------------------------------
# Backtest defaults
# ---------------------------------------------------------------------------
DEFAULT_CAPITAL: float = 1_000.0
DEFAULT_POSITION_SIZE: float = 100.0   # % of capital per trade
