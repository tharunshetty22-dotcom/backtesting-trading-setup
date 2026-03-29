# MT5 Configuration Settings

# Login Credentials Template
login_credentials = {
    'username': 'your_username',  # Replace with your MT5 username
    'password': 'your_password',  # Replace with your MT5 password
    'server': 'your_server',      # Replace with your MT5 server
}

# Timeframes Mapping
# Mapping of timeframes to their respective string identifiers in MT5
timeframes_mapping = {
    'M1': 1,   # 1 minute
    'M5': 5,   # 5 minutes
    'M15': 15, # 15 minutes
    'H1': 60,  # 1 hour
    'H4': 240, # 4 hours
    'D1': 1440,# 1 day
    'W1': 10080,# 1 week
    'MN': 43200 # 1 month
}

# Risk Management Parameters
risk_management = {
    'max_drawdown': 0.1,  # Maximum drawdown (10%)
    'risk_per_trade': 0.02, # Risk 2% per trade
    'reward_to_risk_ratio': 2.0 # Reward to risk ratio
}
