"""
metrics.py – Performance metrics calculation module.
Computes Sharpe ratio, max drawdown, win rate and P&L statistics.
"""

import math


def calculate_metrics(trades: list, starting_capital: float) -> dict:
    """
    Compute full performance metrics from a list of closed trades.

    Each trade dict must contain:
        pnl  : float  – profit/loss of the trade (positive = win)
        entry_price : float
        exit_price  : float
    """
    if not trades:
        return _empty_metrics(starting_capital)

    total_trades = len(trades)
    wins = sum(1 for t in trades if t["pnl"] > 0)
    losses = total_trades - wins
    win_rate = (wins / total_trades) * 100 if total_trades else 0.0

    net_pnl = sum(t["pnl"] for t in trades)
    final_value = starting_capital + net_pnl
    total_return = (net_pnl / starting_capital) * 100 if starting_capital else 0.0

    sharpe = _sharpe_ratio([t["pnl"] for t in trades], starting_capital)
    max_dd = _max_drawdown(trades, starting_capital)

    return {
        "total_trades": total_trades,
        "wins": wins,
        "losses": losses,
        "win_rate": round(win_rate, 1),
        "starting_capital": round(starting_capital, 2),
        "final_value": round(final_value, 2),
        "net_pnl": round(net_pnl, 2),
        "total_return": round(total_return, 2),
        "sharpe_ratio": round(sharpe, 2),
        "max_drawdown": round(max_dd, 2),
        "rating": _rate_strategy(total_return, win_rate, max_dd, sharpe),
    }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _sharpe_ratio(pnls: list, starting_capital: float) -> float:
    """Annualised Sharpe ratio (assumes daily trades, 252 trading days)."""
    if len(pnls) < 2 or starting_capital <= 0:
        return 0.0
    returns = [p / starting_capital for p in pnls]
    mean_r = sum(returns) / len(returns)
    variance = sum((r - mean_r) ** 2 for r in returns) / (len(returns) - 1)
    std_r = math.sqrt(variance) if variance > 0 else 0.0
    if std_r == 0:
        return 0.0
    return (mean_r / std_r) * math.sqrt(252)


def _max_drawdown(trades: list, starting_capital: float) -> float:
    """Maximum drawdown as a positive percentage."""
    equity = starting_capital
    peak = equity
    max_dd = 0.0
    for trade in trades:
        equity += trade["pnl"]
        if equity > peak:
            peak = equity
        drawdown = (peak - equity) / peak * 100 if peak > 0 else 0.0
        if drawdown > max_dd:
            max_dd = drawdown
    return max_dd


def _rate_strategy(total_return: float, win_rate: float, max_drawdown: float, sharpe: float) -> dict:
    """Return a rating dict with pass/fail labels for each metric."""
    def rate_return(r):
        if r >= 20:
            return ("✓", "Excellent")
        if r >= 5:
            return ("✓", "Good")
        return ("✗", "Needs work")

    def rate_win_rate(w):
        if w >= 55:
            return ("✓", "Excellent")
        if w >= 45:
            return ("✓", "Good")
        return ("✗", "Needs work")

    def rate_drawdown(d):
        if d <= 10:
            return ("✓", "Excellent")
        if d <= 20:
            return ("✓", "Acceptable")
        return ("✗", "Too high")

    def rate_sharpe(s):
        if s >= 1.5:
            return ("✓", "Excellent")
        if s >= 0.5:
            return ("✓", "Good")
        return ("✗", "Needs work")

    return {
        "return": rate_return(total_return),
        "win_rate": rate_win_rate(win_rate),
        "drawdown": rate_drawdown(max_drawdown),
        "sharpe": rate_sharpe(sharpe),
    }


def _empty_metrics(starting_capital: float) -> dict:
    return {
        "total_trades": 0,
        "wins": 0,
        "losses": 0,
        "win_rate": 0.0,
        "starting_capital": round(starting_capital, 2),
        "final_value": round(starting_capital, 2),
        "net_pnl": 0.0,
        "total_return": 0.0,
        "sharpe_ratio": 0.0,
        "max_drawdown": 0.0,
        "rating": {
            "return": ("✗", "Needs work"),
            "win_rate": ("✗", "Needs work"),
            "drawdown": ("✗", "Too high"),
            "sharpe": ("✗", "Needs work"),
        },
    }
