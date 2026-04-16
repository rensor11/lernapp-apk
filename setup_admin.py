#!/usr/bin/env python3
"""Set admin password to 'admin123' and create admin user if not exists"""
import sqlite3
from werkzeug.security import generate_password_hash
from datetime import datetime, timezone
import os

db_path = 'lernapp.db'
db = sqlite3.connect(db_path)
db.row_factory = sqlite3.Row
cur = db.cursor()

print("🔍 Prüfe Datenbankstruktur...")

# Prüfe und erstelle fehlende Spalten
user_columns = [row[1] for row in cur.execute("PRAGMA table_info(users)")]

if 'home_access_allowed' not in user_columns:
    print("➕ Füge 'home_access_allowed' Spalte hinzu")
    cur.execute('ALTER TABLE users ADD COLUMN home_access_allowed INTEGER DEFAULT 0')
    db.commit()

if 'smarthome_access_allowed' not in user_columns:
    print("➕ Füge 'smarthome_access_allowed' Spalte hinzu")
    cur.execute('ALTER TABLE users ADD COLUMN smarthome_access_allowed INTEGER DEFAULT 0')
    db.commit()

if 'lernapp_access_allowed' not in user_columns:
    print("➕ Füge 'lernapp_access_allowed' Spalte hinzu")
    cur.execute('ALTER TABLE users ADD COLUMN lernapp_access_allowed INTEGER DEFAULT 0')
    db.commit()

print("✅ Datenbankstruktur OK\n")

# Generate hash for "admin123"
password_hash = generate_password_hash("admin123")
print(f"💾 Setze Admin-Passwort auf 'admin123'")

# Check if admin user exists
cur.execute('SELECT id, username FROM users WHERE username = ?', ('admin',))
admin_user = cur.fetchone()

if admin_user:
    print(f"✅ Admin-Benutzer existiert bereits (ID: {admin_user[0]})")
    # Update password
    cur.execute(
        'UPDATE users SET password_hash = ? WHERE username = ?',
        (password_hash, 'admin')
    )
    admin_id = admin_user[0]
else:
    print(f"➕ Erstelle neuen Admin-Benutzer")
    # Create admin user with all permissions enabled
    cur.execute(
        'INSERT INTO users (username, password_hash, created_at, home_access_allowed, smarthome_access_allowed, lernapp_access_allowed) VALUES (?, ?, ?, ?, ?, ?)',
        ('admin', password_hash, datetime.now(timezone.utc).isoformat(), 1, 1, 1)
    )
    admin_id = cur.lastrowid
    print(f"✅ Admin-Benutzer erstellt (ID: {admin_id})")

db.commit()

# Verify
cur.execute('SELECT id, username, home_access_allowed, smarthome_access_allowed, lernapp_access_allowed FROM users WHERE id = ?', (admin_id,))
admin_data = cur.fetchone()
print(f"\n✅ Admin-Benutzer Konfiguration:")
print(f"  ID: {admin_data['id']}")
print(f"  Username: {admin_data['username']}")
print(f"  Home Cloud: {'✓' if admin_data['home_access_allowed'] else '✗'}")
print(f"  Smart Home: {'✓' if admin_data['smarthome_access_allowed'] else '✗'}")
print(f"  Lernapp: {'✓' if admin_data['lernapp_access_allowed'] else '✗'}")

db.close()
print("\n✅ Admin-Setup abgeschlossen!")
