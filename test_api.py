import requests

print("Testing Flask API...\n")

try:
    # Test 1: Check server status
    response = requests.get('http://localhost:5000/api/status')
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}\n")
    
except requests.exceptions.ConnectionError:
    print("❌ CANNOT CONNECT TO FLASK SERVER")
    print("   Make sure Flask is running: python app.py")
    
except Exception as e:
    print(f"❌ Error: {e}")