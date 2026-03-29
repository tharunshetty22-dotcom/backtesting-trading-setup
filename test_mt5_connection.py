import MetaTrader5 as mt5

print("Testing MT5 Connection...\n")

# Try to initialize
if mt5.initialize():
    print("✅ MT5 initialized successfully!")
    
    # Get account info
    account_info = mt5.account_info()
    if account_info:
        print(f"✅ Connected to MT5!")
        print(f"   Account: {account_info.login}")
        print(f"   Server: {account_info.server}")
        print(f"   Balance: {account_info.balance}")
    else:
        print("❌ Cannot get account info")
        print(f"   Error: {mt5.last_error()}")
    
    mt5.shutdown()
else:
    print("❌ MT5 initialization FAILED!")
    print(f"   Error: {mt5.last_error()}")
    print("\n   Possible reasons:")
    print("   1. MT5 not running")
    print("   2. MT5 port blocked")
    print("   3. Firewall blocking")
    