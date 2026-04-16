#!/usr/bin/env python3
"""
Smart Home Ende-zu-Ende Test nach Reparatur
"""
import requests
import json

BASE_URL = 'http://localhost:5000'
session = requests.Session()

print("=" * 70)
print("SMART HOME E2E TEST - Nach Setup")
print("=" * 70)

# 1. LOGIN
print("\n[1] LOGIN")
r = session.post(f'{BASE_URL}/api/login', json={'username': 'admin', 'password': 'admin123'})
if r.status_code == 200:
    print("    ✅ Angemeldet als admin")
else:
    print(f"    ❌ Login fehlgeschlagen: {r.status_code}")
    exit(1)

# 2. GERÄTE ABRUFEN
print("\n[2] ALLE SMART HOME GERÄTE ABRUFEN")
r = session.get(f'{BASE_URL}/api/smarthome/devices')
if r.status_code == 200:
    data = r.json()
    if data.get('success'):
        devices = data.get('devices', [])
        print(f"    ✅ {len(devices)} Geräte gefunden:")
        for device in devices:
            print(f"       - {device['device_name']} ({device['device_type']})")
            print(f"         IP: {device['ip_address']}:{device.get('port', 'N/A')}")
    else:
        print(f"    ⚠️ {data.get('message')}")
else:
    print(f"    ❌ HTTP {r.status_code}")

# 3. GERÄT STATUS ABRUFEN
print("\n[3] GERÄT STATUS ABRUFEN")
r = session.get(f'{BASE_URL}/api/smarthome/device/1/status')
if r.status_code == 200:
    data = r.json()
    if data.get('success'):
        print(f"    ✅ Fritz!Box Status:")
        print(f"       Status: {data.get('device_status', {}).get('status', 'N/A')}")
    else:
        print(f"    ⚠️ {data.get('message')}")
else:
    print(f"    ❌ HTTP {r.status_code}")

# 4. NETZWERK SCAN
print("\n[4] NETZWERK SCAN")
r = session.get(f'{BASE_URL}/api/smarthome/scan')
if r.status_code == 200:
    data = r.json()
    if data.get('success'):
        devices = data.get('devices', [])
        print(f"    ✅ Netzwerk-Scan erfolgreich: {len(devices)} Geräte gefunden")
        for device in devices[:5]:
            print(f"       - {device['ip']} ({device.get('hostname', 'unknown')})")
    else:
        print(f"    ⚠️ {data.get('message')}")
else:
    print(f"    ❌ HTTP {r.status_code}")

# 5. FIRMWARE CHECK
print("\n[5] FRITZ!BOX VERBINDUNGS-TEST")
try:
    import subprocess
    result = subprocess.run(
        'ping -n 1 192.168.178.1',
        capture_output=True,
        text=True,
        timeout=3
    )
    if result.returncode == 0:
        print("    ✅ Fritz!Box Router ist erreichbar")
    else:
        print("    ⚠️ Fritz!Box nicht erreichbar")
except Exception as e:
    print(f"    ❌ Fehler: {e}")

# 6. BENUTZER-BERECHTIGUNGEN
print("\n[6] ANDERE BENUTZER - SMART HOME ZUGRIFF TEST")
# Logout
session.cookies.clear()

# Login als anderer Benutzer
r = session.post(f'{BASE_URL}/api/login', json={'username': 'renas', 'password': 'renas'})
if r.status_code == 200:
    print("    ✅ Angemeldet als renas")
    
    # Try to get devices
    r = session.get(f'{BASE_URL}/api/smarthome/devices')
    if r.status_code == 200:
        data = r.json()
        if data.get('success'):
            devices = data.get('devices', [])
            print(f"    ✅ renas kann {len(devices)} Geräte sehen")
        else:
            print(f"    ⚠️ {data.get('message')}")
    else:
        print(f"    ⚠️ HTTP {r.status_code}")
else:
    print(f"    ⚠️ Login als renas fehlgeschlagen (Standard-Passwort?)")

print("\n" + "=" * 70)
print("✅ SMART HOME TESTS FERTIG")
print("=" * 70)
