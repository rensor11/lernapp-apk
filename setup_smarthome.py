#!/usr/bin/env python3
"""
Smart Home Setup - Aktiviere Zugriff & Füge Test-Geräte hinzu
"""
import sqlite3
from datetime import datetime

DB_PATH = r'c:\Users\Administrator\Desktop\Repo clone\lernapp-apk\lernapp.db'

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("=" * 70)
print("SMART HOME SETUP")
print("=" * 70)

# 1. Aktiviere Smart Home für alle Benutzer
print("\n[1] AKTIVIERE SMART HOME ZUGRIFF FÜR ALLE BENUTZER")
try:
    cursor.execute("UPDATE users SET smarthome_access_allowed = 1")
    conn.commit()
    cursor.execute("SELECT COUNT(*) FROM users WHERE smarthome_access_allowed = 1")
    count = cursor.fetchone()[0]
    print(f"    ✅ Smart Home aktiviert für {count} Benutzer")
except Exception as e:
    print(f"    ❌ Fehler: {e}")

# 2. Füge Test-Geräte hinzu
print("\n[2] FÜGE TEST-GERÄTE HINZU")
devices = [
    {
        'name': 'Wohnzimmer Licht',
        'type': 'Light',
        'ip': '192.168.178.20',  # Aus ARP Scan
        'port': 8080,
        'protocol': 'http'
    },
    {
        'name': 'Schlafzimmer Thermostat',
        'type': 'Thermostat',
        'ip': '192.168.178.22',
        'port': 8080,
        'protocol': 'http'
    },
    {
        'name': 'Tür Lock',
        'type': 'Lock',
        'ip': '192.168.178.23',
        'port': 443,
        'protocol': 'https'
    },
    {
        'name': 'Kamera Haustüre',
        'type': 'Camera',
        'ip': '192.168.178.29',
        'port': 8080,
        'protocol': 'http'
    }
]

admin_id = 1
now = datetime.utcnow().isoformat()

try:
    for device in devices:
        cursor.execute("""
            INSERT INTO smarthome_devices 
            (user_id, device_name, device_type, ip_address, port, protocol, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, 'unknown', ?)
        """, (admin_id, device['name'], device['type'], device['ip'], device['port'], device['protocol'], now))
    
    conn.commit()
    cursor.execute("SELECT COUNT(*) FROM smarthome_devices")
    total = cursor.fetchone()[0]
    print(f"    ✅ {len(devices)} Test-Geräte hinzugefügt (Total: {total})")
    
    # Zeige hinzugefügte Geräte
    cursor.execute("SELECT id, device_name, device_type FROM smarthome_devices ORDER BY id DESC LIMIT ?", (len(devices),))
    for device in cursor.fetchall():
        print(f"       - {device[1]} ({device[2]}) [ID: {device[0]}]")
        
except Exception as e:
    print(f"    ❌ Fehler: {e}")

# 3. Überprüfung
print("\n[3] ÜBERPRÜFUNG")
try:
    cursor.execute("SELECT COUNT(*) FROM users WHERE smarthome_access_allowed = 1")
    users_with_access = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM smarthome_devices")
    total_devices = cursor.fetchone()[0]
    
    print(f"    ✅ Benutzer mit Smart Home Zugriff: {users_with_access}")
    print(f"    ✅ Total Geräte registriert: {total_devices}")
    
except Exception as e:
    print(f"    ❌ Fehler: {e}")

conn.close()
print("\n" + "=" * 70)
print("SETUP FERTIG!")
print("=" * 70)
