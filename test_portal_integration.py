#!/usr/bin/env python3
"""
Test Smart Home Portal Integration
"""
import requests
import json

BASE_URL = "http://localhost:5000"

print("\n" + "="*70)
print("TESTING SMART HOME PORTAL INTEGRATION")
print("="*70 + "\n")

# 1. Login
print("[1] Login as admin...")
login_data = {'username': 'admin', 'password': 'admin123'}
r = requests.post(f"{BASE_URL}/api/login", json=login_data)

if r.status_code != 200:
    print(f"    ❌ Login failed: {r.status_code}")
    exit(1)

session = requests.Session()
session.post(f"{BASE_URL}/api/login", json=login_data)
print(f"    ✅ Login successful")

# 2. Test Device Discovery
print("\n[2] Test Device Discovery (/api/smarthome/discover)...")
r = session.get(f"{BASE_URL}/api/smarthome/discover")
print(f"    Status: {r.status_code}")

if r.status_code == 200:
    data = r.json()
    if data.get('success'):
        total = data.get('total', 0)
        network = data.get('network_devices', 0)
        ha = data.get('homeassistant_devices', 0)
        
        print(f"    ✅ Discovery successful")
        print(f"       Total devices: {total}")
        print(f"       Network devices: {network}")
        print(f"       Home Assistant: {ha}")
        
        if total > 0 and 'devices' in data:
            print(f"\n       Sample devices:")
            for device in data['devices'][:3]:
                print(f"       - {device.get('name'):20s} ({device.get('type'):15s}) {device.get('domain')}")
    else:
        print(f"    ⚠️  {data.get('message')}")
else:
    print(f"    ❌ Error: {r.status_code}")

# 3. Test HTML Pages
print("\n[3] Check HTML Pages...")
for page in ['smarthome-portal', 'smarthome-settings']:
    r = session.get(f"{BASE_URL}/{page}")
    status = "✅" if r.status_code == 200 else "❌"
    print(f"    {status} /{page}: HTTP {r.status_code}")

print("\n" + "="*70)
print("✅ ALL TESTS COMPLETED")
print("="*70 + "\n")

print("Access Smart Home Portal:")
print("  http://localhost:5000/smarthome-portal")
print("\nAccess Settings:")
print("  http://localhost:5000/smarthome-settings")
