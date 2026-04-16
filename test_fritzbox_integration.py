#!/usr/bin/env python3
"""
Test Fritz!Box Proxy Integration
"""
import requests
import json
import time

BASE_URL = "http://localhost:5000"

print("\n" + "="*70)
print("TESTING FRITZ!BOX PROXY INTEGRATION")
print("="*70 + "\n")

# 1. Login
print("[1] Login as admin...")
login_data = {'username': 'admin', 'password': 'admin123'}
r = requests.post(f"{BASE_URL}/api/login", json=login_data)

if r.status_code != 200:
    print(f"    ❌ Login failed: {r.status_code}")
    exit(1)

print(f"    ✅ Login successful")

# Create session
session = requests.Session()
session.post(f"{BASE_URL}/api/login", json=login_data)

# 2. Get Router Status
print("\n[2] Get Router Status...")
r = session.get(f"{BASE_URL}/api/smarthome/router/status")
print(f"    Status: {r.status_code}")

if r.status_code == 200:
    data = r.json()
    if data.get('success'):
        print(f"    ✅ Router status retrieved")
        print(f"       Internet: {data['router'].get('internet', {}).get('internet')}")
        print(f"       Router: {data['router'].get('internet', {}).get('router')}")
    else:
        print(f"    ⚠️  {data.get('message')}")
else:
    print(f"    ❌ Error: {r.status_code}")
    print(f"       {r.text}")

# 3. Get Connected Devices
print("\n[3] Get Connected Devices...")
r = session.get(f"{BASE_URL}/api/smarthome/router/devices")
print(f"    Status: {r.status_code}")

if r.status_code == 200:
    data = r.json()
    if data.get('success'):
        devices = data.get('devices', [])
        print(f"    ✅ Found {len(devices)} devices")
        
        for device in devices[:5]:
            print(f"       - {device.get('hostname'):20s} ({device.get('ip')})")
        
        if len(devices) > 5:
            print(f"       ... and {len(devices)-5} more devices")
    else:
        print(f"    ⚠️  {data.get('message')}")
else:
    print(f"    ❌ Error: {r.status_code}")
    print(f"       {r.text[:200]}")

# 4. Test Router Control (Reboot - without auth, should fail gracefully)
print("\n[4] Test Router Control (Reboot)...")
r = session.post(f"{BASE_URL}/api/smarthome/router/control", 
                  json={'action': 'reboot'})
print(f"    Status: {r.status_code}")

if r.status_code == 200:
    data = r.json()
    print(f"    Response: {data.get('message', data.get('result', {}).get('reason'))}")
else:
    print(f"    Error: {r.status_code}")

# 5. Test WiFi Control
print("\n[5] Test WiFi Control...")
r = session.post(f"{BASE_URL}/api/smarthome/router/wifi",
                  json={'state': 'toggle'})
print(f"    Status: {r.status_code}")

if r.status_code in [200, 501]:
    data = r.json()
    print(f"    Response: {data.get('message')}")
else:
    print(f"    Error: {r.status_code}")

print("\n" + "="*70)
print("✅ ALL TESTS COMPLETED")
print("="*70 + "\n")
