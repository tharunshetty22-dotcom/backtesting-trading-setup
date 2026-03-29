"""
app.py – Flask REST API for the backtesting platform.

Endpoints
---------
GET  /
    Serves the frontend HTML file.

GET  /api/status
    Returns MT5 connection status.

GET  /api/symbols
    Returns a list of available MT5 trading symbols.

POST /api/backtest
    Runs a backtest.  Accepts a multipart form with:
      - strategy      : Python strategy file (.py)
      - symbol        : MT5 symbol, e.g. "EURUSD"
      - timeframe     : Timeframe string, e.g. "H1"
      - start_date    : ISO date string, e.g. "2024-01-01"
      - end_date      : ISO date string, e.g. "2024-12-31"
      - initial_capital : Starting capital in USD (default 1000)
      - position_size : % of capital per trade (default 100)
"""

import os

from datetime import datetime, timezone

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

import mt5_connector
from backtester import run_backtest
from config import (
    DEFAULT_INITIAL_CAPITAL,
    DEFAULT_POSITION_SIZE_PCT,
    DEFAULT_SYMBOL,
    DEFAULT_TIMEFRAME,
    FLASK_DEBUG,
    FLASK_HOST,
    FLASK_PORT,
)
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


@app.route("/api/status", methods=["GET"])
def status():
    """Return MT5 connection status and account info."""
    return jsonify(mt5_connector.get_connection_status())


@app.route("/api/symbols", methods=["GET"])
def symbols():
    """Return list of available trading symbols from MT5."""
    try:
        symbol_list = mt5_connector.get_symbols()
        return jsonify({"symbols": symbol_list})
    except mt5_connector.MT5ConnectionError as exc:
        return jsonify({"error": str(exc)}), 503


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

    # ---- parameters --------------------------------------------------
    symbol = request.form.get("symbol", DEFAULT_SYMBOL).strip().upper()
    timeframe = request.form.get("timeframe", DEFAULT_TIMEFRAME).strip().upper()
    start_date_str = request.form.get("start_date", "").strip()
    end_date_str = request.form.get("end_date", "").strip()

    try:
        capital = float(request.form.get("initial_capital", DEFAULT_INITIAL_CAPITAL))
        position_size = float(request.form.get("position_size", DEFAULT_POSITION_SIZE_PCT))
        if capital <= 0:
            raise ValueError("Starting capital must be positive.")
        if not (1 <= position_size <= 100):
            raise ValueError("Position size must be between 1 and 100.")
    except (TypeError, ValueError) as exc:
        return jsonify({"error": str(exc)}), 400

    try:
        start_dt = _parse_date(start_date_str) if start_date_str else datetime(2024, 1, 1, tzinfo=timezone.utc)
        end_dt = _parse_date(end_date_str) if end_date_str else datetime.now(tz=timezone.utc)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    if start_dt >= end_dt:
        return jsonify({"error": "start_date must be before end_date."}), 400

    # ---- fetch MT5 data ----------------------------------------------
    try:
        df = mt5_connector.get_ohlcv(symbol, timeframe, start_dt, end_dt)
    except mt5_connector.MT5ConnectionError as exc:
        return jsonify({"error": f"MT5 connection error: {exc}"}), 503
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

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

    # Attach request context to results
    results["symbol"] = symbol
    results["timeframe"] = timeframe
    results["start_date"] = start_dt.date().isoformat()
    results["end_date"] = end_dt.date().isoformat()

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


def _parse_date(date_str: str) -> datetime:
    """Parse an ISO date string (YYYY-MM-DD) and return a UTC datetime."""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        raise ValueError(f"Invalid date format '{date_str}'.  Use YYYY-MM-DD.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=FLASK_DEBUG, host=FLASK_HOST, port=FLASK_PORT)
