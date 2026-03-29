"""
config.py – Configuration settings for the backtesting platform.

Edit the MT5_* variables to match your MetaTrader5 terminal credentials.
"""

# ---------------------------------------------------------------------------
# MetaTrader5 connection settings
# ---------------------------------------------------------------------------

MT5_LOGIN = 0           # MT5 account number (0 = use currently logged-in account)
MT5_PASSWORD = ""       # MT5 account password (leave empty to use terminal session)
MT5_SERVER = ""         # Broker server name (leave empty to use terminal default)
MT5_PATH = ""           # Path to terminal64.exe (leave empty for auto-detect)
MT5_TIMEOUT = 60_000    # Connection timeout in milliseconds

# ---------------------------------------------------------------------------
# Default backtest parameters
# ---------------------------------------------------------------------------

DEFAULT_INITIAL_CAPITAL = 1_000.0   # USD
DEFAULT_POSITION_SIZE_PCT = 100.0   # % of capital per trade
DEFAULT_TIMEFRAME = "H1"
DEFAULT_SYMBOL = "EURUSD"

# ---------------------------------------------------------------------------
# Supported timeframes  (display label → MT5 constant name)
# ---------------------------------------------------------------------------

TIMEFRAMES = {
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

# ---------------------------------------------------------------------------
# Risk management defaults
# ---------------------------------------------------------------------------

MAX_POSITION_SIZE_PCT = 100.0   # Hard cap – never risk more than this per trade
MIN_POSITION_SIZE_PCT = 1.0     # Hard floor

# ---------------------------------------------------------------------------
# Flask settings
# ---------------------------------------------------------------------------

FLASK_HOST = "0.0.0.0"
FLASK_PORT = 5000
FLASK_DEBUG = False
