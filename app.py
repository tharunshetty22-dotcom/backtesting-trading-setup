"""
app.py – Flask REST API for the backtesting platform.

Endpoints
---------
GET  /api/symbols
    Returns available trading symbols from the MT5 terminal.
    Query param: group (optional) – wildcard filter, e.g. "*USD*"

POST /api/backtest
    Accepts a multipart form with:
      - strategy      : Python strategy file (.py)
      - symbol        : Trading symbol, e.g. "EURUSD"
      - timeframe     : Timeframe key, e.g. "H1" (default "H1")
      - start_date    : ISO-8601 start date, e.g. "2023-01-01"
      - end_date      : ISO-8601 end date,   e.g. "2024-01-01"
      - capital       : (optional) starting capital in USD (default 1000)
      - position_size : (optional) % of capital per trade (default 100)

GET /
    Serves the frontend HTML file.
"""

import logging
import os
from datetime import datetime, timezone

from flask import Flask, jsonify, request, send_from_directory

logger = logging.getLogger(__name__)
from flask_cors import CORS

from backtester import run_backtest
from config import DEFAULT_CAPITAL, DEFAULT_POSITION_SIZE, DEFAULT_TIMEFRAME
from mt5_connector import connect, disconnect, fetch_ohlcv, get_account_info, get_symbols
from strategy_validator import StrategyValidationError, validate_strategy

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")
CORS(app)

ALLOWED_EXTENSIONS = {"py"}
MAX_CONTENT_LENGTH = 1 * 1024 * 1024  # 1 MB
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/api/symbols", methods=["GET"])
def symbols():
    """Return available symbols from the MT5 terminal."""
    group = request.args.get("group", "").strip()
    try:
        if not connect():
            return jsonify({"error": "Could not connect to MT5 terminal."}), 503
        symbol_list = get_symbols(group=group)
        return jsonify({"symbols": symbol_list})
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 503
    finally:
        disconnect()


@app.route("/api/backtest", methods=["POST"])
def backtest():
    # ---- strategy file ------------------------------------------------
    if "strategy" not in request.files:
        return jsonify({"error": "No strategy file uploaded."}), 400

    strategy_file = request.files["strategy"]
    if not strategy_file.filename or not _allowed_file(strategy_file.filename):
        return jsonify({"error": "Strategy must be a .py file."}), 400

    strategy_source = strategy_file.read().decode("utf-8")

    # ---- validate strategy -------------------------------------------
    try:
        validate_strategy(strategy_source)
    except StrategyValidationError as exc:
        return jsonify({"error": str(exc)}), 422

    # ---- MT5 parameters ---------------------------------------------
    symbol = request.form.get("symbol", "").strip().upper()
    timeframe = request.form.get("timeframe", DEFAULT_TIMEFRAME).strip().upper()
    start_date_str = request.form.get("start_date", "").strip()
    end_date_str = request.form.get("end_date", "").strip()

    if not symbol:
        return jsonify({"error": "A trading symbol is required (e.g. 'EURUSD')."}), 400

    start_date = _parse_date(start_date_str)
    end_date = _parse_date(end_date_str)

    # ---- backtest parameters -----------------------------------------
    try:
        capital = float(request.form.get("capital", DEFAULT_CAPITAL))
        position_size = float(request.form.get("position_size", DEFAULT_POSITION_SIZE))
        if capital <= 0:
            raise ValueError("Starting capital must be positive.")
        if not (1 <= position_size <= 100):
            raise ValueError("Position size must be between 1 and 100.")
    except (TypeError, ValueError) as exc:
        return jsonify({"error": str(exc)}), 400

    # ---- connect to MT5 and fetch data --------------------------------
    try:
        if not connect():
            return jsonify({"error": "Could not connect to MT5 terminal."}), 503

        try:
            df = fetch_ohlcv(
                symbol=symbol,
                timeframe=timeframe,
                start=start_date,
                end=end_date,
            )
        except (ValueError, RuntimeError) as exc:
            return jsonify({"error": str(exc)}), 400
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 503
    finally:
        disconnect()

    # ---- run backtest ------------------------------------------------
    try:
        results = run_backtest(
            strategy_source=strategy_source,
            df=df,
            starting_capital=capital,
            position_size_pct=position_size,
        )
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": f"Backtest error: {exc}"}), 500

    # Add context to results
    results["symbol"] = symbol
    results["timeframe"] = timeframe

    # Serialise the rating tuples to plain dicts for JSON
    rating = results.get("rating", {})
    results["rating"] = {
        k: {"icon": v[0], "label": v[1]} for k, v in rating.items()
    }

    return jsonify(results)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def _parse_date(date_str: str):
    """Parse an ISO-8601 date string and return a timezone-aware datetime or None."""
    if not date_str:
        return None
    try:
        dt = datetime.fromisoformat(date_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        logger.warning("Could not parse date string %r; ignoring.", date_str)
        return None


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True, port=5000)
