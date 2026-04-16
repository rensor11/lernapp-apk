#!/usr/bin/env python3
"""
Stelle ursprüngliche Sicherheits-Einstellungen wieder her
Nur Admin soll Smart Home Zugriff haben
"""
import sqlite3

DB_PATH = r'c:\Users\Administrator\Desktop\Repo clone\lernapp-apk\lernapp.db'

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("=" * 70)
print("SICHERHEITS-EINSTELLUNGEN WIEDERHERSTELLEN")
print("=" * 70)

# 1. Setze alle Benutzer auf kein Smart Home (außer Admin)
print("\n[1] BERECHTIGUNGEN ZURÜCKSETZEN")
try:
    # Alle Benutzer: kein Smart Home Access
    cursor.execute("UPDATE users SET smarthome_access_allowed = 0")
    conn.commit()
    
    # Admin: Smart Home Access
    cursor.execute("UPDATE users SET smarthome_access_allowed = 1 WHERE username = 'admin'")
    conn.commit()
    
    cursor.execute("SELECT username, smarthome_access_allowed FROM users")
    users = cursor.fetchall()
    
    print("    Berechtigungen:")
    for username, smarthome_access in users:
        status = "✅ CAN DUE" if smarthome_access else "❌ NO ACCESS"
        print(f"    {status} - {username}")
        
except Exception as e:
    print(f"    ❌ Fehler: {e}")

# 2. Nachricht
print("\n[2] GERÄTE STATUS")
try:
    cursor.execute("SELECT COUNT(*) FROM smarthome_devices")
    count = cursor.fetchone()[0]
    print(f"    ✅ {count} Geräte registriert (alle Geräte verfügbar für Admin)")
except Exception as e:
    print(f"    ❌ Fehler: {e}")

conn.close()
print("\n" + "=" * 70)
print("✅ SICHERHEITS-EINSTELLUNGEN WIEDERHERGESTELLT")
print("=" * 70)
