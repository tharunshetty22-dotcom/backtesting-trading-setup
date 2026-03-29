# Backtesting Trading Platform (MT5)

A user-friendly backtesting platform that fetches historical OHLCV data
directly from a **MetaTrader5** terminal and executes user-defined Python
trading strategies.

---

## Features

- **MT5 data source** – historical candle data for any MT5 symbol and timeframe
- **Strategy upload** – write strategies in plain Python; just implement
  `generate_signals(df)`
- **Full metrics** – Sharpe ratio, max drawdown, win rate, P&L, total return
- **Strategy rating** – automatic pass/fail assessment per metric
- **Clean web UI** – symbol selector, timeframe picker, date-range picker,
  MT5 connection status

---

## Prerequisites

| Requirement | Notes |
|---|---|
| Python 3.10+ | |
| MetaTrader5 terminal | Windows only; download from your broker |
| MT5 Python API | Installed via `pip install MetaTrader5` |

> **Windows only**: The `MetaTrader5` Python package only works on Windows
> because it communicates with the native MT5 terminal process.

---

## MetaTrader5 Setup

1. **Install** the MetaTrader5 terminal from your broker's website.
2. **Open the terminal** and log in to your trading account.
3. Enable Python integration:
   - Go to **Tools → Options → Expert Advisors**
   - Check **Allow DLL imports**
4. Keep the terminal **running in the background** while using this platform.

---

## Installation

```bash
git clone https://github.com/tharunshetty22-dotcom/backtesting-trading-setup.git
cd backtesting-trading-setup
pip install -r requirements.txt
```

### Configure credentials (optional)

If your MT5 account requires login details set them via environment variables:

```bash
export MT5_LOGIN=12345678       # account number
export MT5_PASSWORD=YourPass    # account password
export MT5_SERVER=BrokerName-Demo  # broker server
```

Or edit `config.py` directly.

---

## Running the application

```bash
python app.py
```

Then open **http://localhost:5000** in your browser.

---

## Usage

1. Make sure the MT5 terminal is running – the status badge in the UI turns
   green when connected.
2. **Upload** your Python strategy file.
3. **Select** a trading symbol (e.g. `EURUSD`).
4. **Choose** a timeframe (e.g. `H1`).
5. **Set** the date range for historical data.
6. Click **Run Backtest**.
7. View the comprehensive results with metrics and strategy rating.

---

## Writing a strategy

Your strategy file must define a single function:

```python
import pandas as pd

def generate_signals(df: pd.DataFrame) -> pd.DataFrame:
    """
    Receive an OHLCV DataFrame and return it with a 'signal' column added.
    signal =  1 → BUY
    signal = -1 → SELL
    signal =  0 → HOLD
    """
    df = df.copy()
    # --- your logic here ---
    df["signal"] = 0
    return df
```

See `sample_strategy.py` for a complete SMA-crossover example.

---

## Project structure

```
backtesting-trading-setup/
├── app.py                  # Flask REST API
├── backtester.py           # Core backtesting engine
├── metrics.py              # Performance metrics calculator
├── mt5_connector.py        # MetaTrader5 integration
├── config.py               # Configuration & MT5 credentials
├── strategy_validator.py   # Strategy safety checks
├── sample_strategy.py      # Example strategy template
├── requirements.txt        # Python dependencies
└── frontend/
    └── index.html          # Web UI
```

---

## API Endpoints

### `GET /api/symbols`

Returns available trading symbols from the MT5 terminal.

Query parameters:
- `group` (optional) – wildcard filter, e.g. `*USD*`

### `POST /api/backtest`

Run a backtest. Form fields:

| Field | Required | Description |
|---|---|---|
| `strategy` | ✓ | `.py` strategy file |
| `symbol` | ✓ | e.g. `EURUSD` |
| `timeframe` | | e.g. `H1` (default `H1`) |
| `start_date` | | ISO-8601 e.g. `2023-01-01` |
| `end_date` | | ISO-8601 e.g. `2024-01-01` |
| `capital` | | Starting capital, default `1000` |
| `position_size` | | % of capital per trade, default `100` |

---

## Troubleshooting MT5 connection

| Problem | Solution |
|---|---|
| `RuntimeError: MetaTrader5 package not installed` | Run `pip install MetaTrader5` |
| `Could not connect to MT5 terminal` | Ensure MT5 terminal is open and logged in |
| `No data returned for symbol` | Check the symbol name matches exactly (e.g. `EURUSD` not `EUR/USD`) |
| MT5 only works on Windows | Run the application on a Windows machine |

---

## Disclaimer

Backtest results are for educational purposes only and do not constitute
financial advice.

