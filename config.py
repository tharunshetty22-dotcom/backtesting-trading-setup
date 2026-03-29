# ==================== MT5 LOGIN CREDENTIALS ====================
login_credentials = {
    'username': '168049934',
    'password': '@Tharunshetty22',  # ← Replace with YOUR actual MT5 password
    'server': 'XMGlobal-MT5 2',
}

# ==================== BACKTESTING PARAMETERS ====================
BACKTEST_CONFIG = {
    'initial_capital': 1000,
    'position_size': 0.01,
    'risk_per_trade': 0.02,  # 2% risk
}

# ==================== FLASK CONFIGURATION ====================
FLASK_CONFIG = {
    'DEBUG': True,
    'HOST': '127.0.0.1',
    'PORT': 5000,
}

# ==================== API CONFIGURATION ====================
API_CONFIG = {
    'max_symbols': 1533,
    'timeout': 30,
}