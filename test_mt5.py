import MetaTrader5 as mt5

# Initialize MT5
if not mt5.initialize():
    print("❌ MT5 initialization failed")
    print(f"Error: {mt5.last_error()}")
else:
    print("✅ MT5 initialized successfully!")
    
    # Get account info
    account_info = mt5.account_info()
    if account_info:
        print(f"✅ Account connected!")
        print(f"   Account number: {account_info.login}")
        print(f"   Balance: {account_info.balance}")
        print(f"   Equity: {account_info.equity}")
    else:
        print("❌ Could not get account info")
    
    # Get symbols
    symbols = mt5.symbols_get()
    if symbols:
        print(f"✅ MT5 has {len(symbols)} symbols available")
        print(f"   First 5 symbols: {[s.name for s in symbols[:5]]}")
    else:
        print("❌ Could not get symbols")
    
    mt5.shutdown()