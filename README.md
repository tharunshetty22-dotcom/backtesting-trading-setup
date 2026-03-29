# MT5 Backtesting Platform

A production-ready backtesting platform that connects to a live **MetaTrader5** terminal,
fetches real OHLCV data and executes Python trading strategies, returning comprehensive
performance metrics.

---

## Table of Contents

1. [Project Structure](#project-structure)
2. [Requirements](#requirements)
3. [Installation](#installation)
4. [MT5 Setup](#mt5-setup)
5. [Running the Server](#running-the-server)
6. [Writing Custom Strategies](#writing-custom-strategies)
7. [API Reference](#api-reference)
8. [Results Format](#results-format)
9. [Troubleshooting](#troubleshooting)

---

## Project Structure

```
backtesting-trading-setup/
├── app.py                  # Flask REST API
├── backtester.py           # Core backtesting engine
├── metrics.py              # Performance metrics calculator
├── mt5_connector.py        # MetaTrader5 integration
├── strategy_validator.py   # Strategy code safety validation
├── config.py               # Configuration (MT5 credentials, defaults)
├── sample_strategy.py      # Example strategy template
├── requirements.txt        # Python dependencies
├── README.md
└── frontend/
    ├── index.html          # Main UI
    ├── style.css           # Styles
    └── script.js           # Frontend logic
```

---

## Requirements

- **Python 3.10+** (Windows recommended for MT5)
- **MetaTrader5 terminal** installed and running
- MT5 Python integration enabled (see [MT5 Setup](#mt5-setup))

---

## Installation

```bash
# 1. Clone the repository
git clone https://github.com/tharunshetty22-dotcom/backtesting-trading-setup.git
cd backtesting-trading-setup

# 2. Create and activate a virtual environment (recommended)
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux (MT5 won't work, but API will still start)

# 3. Install dependencies
pip install -r requirements.txt
```

> **Note:** The `MetaTrader5` package only works on **Windows**.  On other platforms the
> server starts normally but MT5 endpoints return a clear error message.

---

## MT5 Setup

### 1. Install MetaTrader5

Download and install MetaTrader5 from your broker or from
[metatrader5.com](https://www.metatrader5.com/).

### 2. Enable the Python integration (AlgoTrading)

1. Open **MetaTrader5**.
2. Go to **Tools → Options → Expert Advisors**.
3. Check **"Allow algorithmic trading"**.
4. Check **"Allow DLL imports"** (if prompted by your broker).
5. Restart the terminal.

### 3. Log in to your account

Make sure you are logged in to a live or demo account in the terminal.

### 4. (Optional) Set credentials in config.py

For fully automated connections without an open terminal session, set:

```python
# config.py
MT5_LOGIN    = 12345678          # Your account number
MT5_PASSWORD = "your_password"
MT5_SERVER   = "BrokerName-Demo"
MT5_PATH     = r"C:\Program Files\MetaTrader 5\terminal64.exe"
```

Leave them blank to connect to the already-open terminal session.

---

## Running the Server

```bash
python app.py
```

Open your browser at **http://localhost:5000**.

The status bar at the top of the page shows the MT5 connection state.

---

## Writing Custom Strategies

Every strategy must be a `.py` file that defines a `generate_signals(df)` function.

```python
import pandas as pd
import numpy as np

STRATEGY_NAME = "My Strategy"   # optional

def generate_signals(df: pd.DataFrame) -> pd.DataFrame:
    """
    df contains columns: Open, High, Low, Close, Volume
    Add a 'signal' column and return df.
      signal =  1  →  BUY
      signal = -1  →  SELL
      signal =  0  →  HOLD
    """
    df = df.copy()
    df["signal"] = 0

    # Example: buy when close crosses above 20-day SMA
    df["sma"] = df["Close"].rolling(20).mean()
    df.loc[df["Close"] > df["sma"], "signal"] = 1
    df.loc[df["Close"] < df["sma"], "signal"] = -1

    return df
```

See `sample_strategy.py` for a complete SMA crossover example.

**Allowed imports:** `pandas`, `numpy`  
**Blocked imports:** `os`, `sys`, `subprocess`, `socket`, `requests`, and other
network/filesystem modules.

---

## API Reference

### `GET /api/status`

Returns the current MT5 connection status.

**Response**
```json
{
  "connected": true,
  "account":   12345678,
  "broker":    "BrokerName",
  "balance":   10000.00,
  "equity":    10123.45,
  "error":     null
}
```

---

### `GET /api/symbols`

Returns all available trading symbols from the connected MT5 terminal.

**Response**
```json
{
  "symbols": ["AUDCAD", "AUDCHF", "AUDJPY", "AUDUSD", "EURUSD", "..."]
}
```

---

### `POST /api/backtest`

Run a backtest on MT5 historical data.

**Form fields**

| Field            | Type   | Required | Default    | Description                            |
|------------------|--------|----------|------------|----------------------------------------|
| `strategy`       | file   | ✓        | –          | `.py` strategy file                    |
| `symbol`         | string | ✓        | EURUSD     | MT5 symbol, e.g. `EURUSD`             |
| `timeframe`      | string | ✓        | H1         | Timeframe: M1 M5 M15 M30 H1 H4 D1 W1 MN |
| `start_date`     | string | ✓        | –          | ISO date `YYYY-MM-DD`                  |
| `end_date`       | string | ✓        | –          | ISO date `YYYY-MM-DD`                  |
| `initial_capital`| float  | –        | 1000       | Starting capital in USD                |
| `position_size`  | float  | –        | 100        | % of capital per trade (1–100)         |

**Response**
```json
{
  "symbol":          "EURUSD",
  "timeframe":       "H1",
  "start_date":      "2024-01-01",
  "end_date":        "2024-12-31",
  "starting_capital": 1000.00,
  "final_value":      729.79,
  "net_pnl":         -270.21,
  "total_return":    -27.02,
  "total_trades":    30,
  "wins":            11,
  "losses":          19,
  "win_rate":        36.7,
  "sharpe_ratio":    -0.81,
  "max_drawdown":    39.00,
  "rating": {
    "return":   { "icon": "✗", "label": "Needs work" },
    "win_rate": { "icon": "✗", "label": "Needs work" },
    "drawdown": { "icon": "✗", "label": "Too high"   },
    "sharpe":   { "icon": "✗", "label": "Needs work" }
  }
}
```

---

## Results Format

```
====================================================
           BACKTEST RESULTS
====================================================
  Starting capital : $  1,000.00
  Final value      : $    729.79
  Net P&L          : $   -270.21
  Total return     :    -27.02%
  Total trades     :         30
  Won / Lost       : 11 / 19
  Win rate         :      36.7%
  Sharpe ratio     :     -0.81
  Max drawdown     :    39.00%
====================================================

  Strategy rating:
  Return  : ✗ Needs work
  Win rate: ✗ Needs work
  Drawdown: ✗ Too high
  Sharpe  : ✗ Needs work
```

### Rating thresholds

| Metric       | Excellent       | Good            | Needs work / Too high |
|-------------|-----------------|-----------------|----------------------|
| Return       | ≥ 20%           | ≥ 5%            | < 5%                 |
| Win rate     | ≥ 55%           | ≥ 45%           | < 45%                |
| Max drawdown | ≤ 10%           | ≤ 20%           | > 20%                |
| Sharpe ratio | ≥ 1.5           | ≥ 0.5           | < 0.5                |

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "MetaTrader5 package not installed" | Run `pip install MetaTrader5` on a Windows machine |
| "MT5 initialisation failed" | Ensure the MetaTrader5 terminal is open and logged in |
| "No data returned" | Check the symbol name, timeframe and date range are valid for your broker |
| Strategy validation error | Make sure your `.py` file defines `generate_signals(df)` |
| Browser shows blank page | Ensure Flask is running on port 5000 |

---

*Backtest results are for educational purposes only and do not constitute financial advice.*
