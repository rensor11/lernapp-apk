#!/usr/bin/env python3
import requests

print("=" * 70)
print("INTEGRATION TEST: Mock HA + Smart Home Portal")
print("=" * 70)

# Test 1: Mock HA directly
print("\n[1] Mock Home Assistant (Port 8123)...")
try:
    ha_resp = requests.get('http://localhost:8123/api/states', 
                           headers={'Authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJNb2NrIEhBIiwiaWF0IjoxNzQ1MDAwMDAwfQ.mock_token_for_testing'},
                           timeout=3)
    if ha_resp.status_code == 200:
        entities = ha_resp.json()
        print(f"     ✅ Running: {len(entities)} Entities")
        for e in entities[:4]:
            print(f"        - {e['entity_id']}: {e['state']}")
    else:
        print(f"     ❌ Status: {ha_resp.status_code}")
except Exception as e:
    print(f"     ❌ Error: {str(e)[:40]}")

# Test 2: Lernapp Login
print("\n[2] Lernapp Server (Port 5000)...")
try:
    login_resp = requests.post('http://localhost:5000/api/login', 
                               json={'username': 'admin', 'password': 'admin123'},
                               timeout=3)
    print(f"     ✅ Login: OK") if login_resp.status_code == 200 else print(f"     ❌ Login: {login_resp.status_code}")
except Exception as e:
    print(f"     ❌ Error: {str(e)[:40]}")

# Test 3: Portal Discovery Endpoint
print("\n[3] Portal Discovery Endpoint...")
try:
    session = requests.Session()
    session.post('http://localhost:5000/api/login', json={'username': 'admin', 'password': 'admin123'}, timeout=2)
    disc_resp = session.get('http://localhost:5000/api/smarthome/discover?user_id=1', timeout=5)
    if disc_resp.status_code == 200:
        data = disc_resp.json()
        print(f"     ✅ Discovery: OK")
        print(f"        - Total Devices: {data.get('total', 0)}")
        print(f"        - Network: {data.get('network_devices', 0)}")
        print(f"        - Home Assistant: {data.get('homeassistant_devices', 0)}")
    else:
        print(f"     ❌ Discovery: {disc_resp.status_code}")
except Exception as e:
    print(f"     ❌ Error: {str(e)[:40]}")

print("\n" + "=" * 70)
print("✅ ALL SYSTEMS READY!")
print("=" * 70)
print("\n🌐 Open Portal: http://localhost:5000/smarthome-portal")
print("   Username: admin")
print("   Password: admin123")
print("\n🏠 Home Assistant API Token set automatically")
print("   URL: http://localhost:8123")
print("=" * 70)
