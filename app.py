"""
app.py – Flask REST API for the backtesting platform.

Endpoints
---------
POST /api/backtest
    Accepts a multipart form with:
      - strategy  : Python strategy file (.py)
      - csv_file  : (optional) CSV file with OHLCV data
      - ticker    : (optional) ticker symbol to download via yfinance
      - period    : (optional) yfinance period, e.g. "1y" (default "1y")
      - capital   : (optional) starting capital in USD (default 1000)
      - position_size : (optional) % of capital per trade (default 100)

GET /
    Serves the frontend HTML file.
"""

import io
import os

import pandas as pd
import yfinance as yf
from flask import Flask, jsonify, render_template_static, request, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename

from backtester import run_backtest
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

    # ---- load historical data ----------------------------------------
    try:
        df = _load_data(request)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    # ---- parameters --------------------------------------------------
    try:
        capital = float(request.form.get("capital", 1_000))
        position_size = float(request.form.get("position_size", 100))
        if capital <= 0:
            raise ValueError("Starting capital must be positive.")
        if not (1 <= position_size <= 100):
            raise ValueError("Position size must be between 1 and 100.")
    except (TypeError, ValueError) as exc:
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


def _load_data(req) -> pd.DataFrame:
    """Return a DataFrame from either an uploaded CSV or a yfinance download."""
    csv_file = req.files.get("csv_file")
    ticker = req.form.get("ticker", "").strip().upper()
    period = req.form.get("period", "1y").strip()

    if csv_file and csv_file.filename:
        content = csv_file.read().decode("utf-8")
        df = pd.read_csv(io.StringIO(content), index_col=0, parse_dates=True)
        if df.empty:
            raise ValueError("Uploaded CSV is empty.")
        return df

    if ticker:
        df = yf.download(ticker, period=period, progress=False, auto_adjust=True)
        if df is None or df.empty:
            raise ValueError(f"No data returned for ticker '{ticker}'.")
        return df

    raise ValueError("Provide either a CSV file or a ticker symbol.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True, port=5000)
