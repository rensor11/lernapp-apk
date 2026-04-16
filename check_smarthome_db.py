#!/usr/bin/env python3
"""
Überprüfe Smart Home Geräte in der Datenbank
"""
import sqlite3
import json

DB_PATH = r'c:\Users\Administrator\Desktop\Repo clone\lernapp-apk\lernapp.db'

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("=" * 70)
print("SMART HOME GERÄTE - DATENBANK ANALYSE")
print("=" * 70)

# 1. Überprüfe Datenbank-Schema
print("\n[1] DATENBANK TABELLEN")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
for table in tables:
    print(f"    - {table[0]}")

# 2. Smart Home Geräte
print("\n[2] REGISTRIERTE SMART HOME GERÄTE")
try:
    cursor.execute("SELECT * FROM smarthome_devices LIMIT 10")
    devices = cursor.fetchall()
    
    if len(devices) == 0:
        print("    ⚠️ KEINE GERÄTE REGISTRIERT!")
    else:
        print(f"    {len(devices)} Geräte gefunden:")
        for device in devices:
            print(f"\n    ID: {device['id']}")
            print(f"    Name: {device['device_name']}")
            print(f"    Type: {device['device_type']}")
            print(f"    IP: {device.get('ip_address', 'N/A')}")
            print(f"    Port: {device.get('port', 'N/A')}")
            print(f"    User: {device.get('user_id', 'N/A')}")
except Exception as e:
    print(f"    ❌ Fehler: {e}")

# 3. Benutzer und deren Berechtigungen
print("\n[3] BENUTZER UND SMART HOME ZUGRIFF")
try:
    cursor.execute("SELECT id, username, smarthome_access_allowed FROM users")
    users = cursor.fetchall()
    
    for user in users:
        status = "✅" if user['smarthome_access_allowed'] else "❌"
        print(f"    {status} {user['username']} (ID: {user['id']})")
except Exception as e:
    print(f"    ❌ Fehler: {e}")

# 4. Spezifische Geräte-Informationen
print("\n[4] DETAIL-INFORMATIONEN")
try:
    cursor.execute("""
        SELECT d.*, u.username 
        FROM smarthome_devices d
        LEFT JOIN users u ON d.user_id = u.id
        LIMIT 1
    """)
    device = cursor.fetchone()
    
    if device:
        print("    Erstes Gerät (vollständige Info):")
        for key in device.keys():
            print(f"        {key}: {device[key]}")
    else:
        print("    ⚠️ Keine Geräte in Datenbank")
except Exception as e:
    print(f"    ❌ Fehler: {e}")

conn.close()
print("\n" + "=" * 70)
