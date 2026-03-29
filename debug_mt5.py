import MetaTrader5 as mt5
import sys

print("=" * 60)
print("DEBUGGING MT5 CONNECTION")
print("=" * 60)

# Test 1: Direct initialization
print("\n1. Testing direct MT5 initialization...")
if mt5.initialize():
    print("   ✅ MT5 initialized!")
    
    # Get account info
    account = mt5.account_info()
    print(f"   ✅ Account: {account.login}")
    print(f"   ✅ Server: {account.server}")
    print(f"   ✅ Balance: {account.balance}")
    
    mt5.shutdown()
else:
    print(f"   ❌ Failed: {mt5.last_error()}")

# Test 2: With login credentials
print("\n2. Testing with explicit credentials...")
try:
    from config import login_credentials
    
    print(f"   Username: {login_credentials['username']}")
    print(f"   Server: {login_credentials['server']}")
    print(f"   Password: {'*' * len(login_credentials['password'])}")
    
    if mt5.initialize(
        path=None,
        login=int(login_credentials['username']),
        password=login_credentials['password'],
        server=login_credentials['server']
    ):
        print("   ✅ Connected with credentials!")
        account = mt5.account_info()
        print(f"   ✅ Balance: {account.balance}")
        mt5.shutdown()
    else:
        print(f"   ❌ Failed: {mt5.last_error()}")
        
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "=" * 60)