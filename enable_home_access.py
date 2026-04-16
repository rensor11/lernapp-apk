#!/usr/bin/env python3
import sqlite3

db = sqlite3.connect('lernapp.db')
cursor = db.cursor()

# Alle Benutzer auf home_access_allowed = 1 setzen
cursor.execute('UPDATE users SET home_access_allowed = 1')
db.commit()

# Zeige alle Benutzer mit neuem Status
cursor.execute('SELECT id, username, home_access_allowed FROM users')
users = cursor.fetchall()

print("✅ Alle Benutzer haben jetzt Home-Zugriff:")
print()
for user_id, username, has_access in users:
    status = "✓ Zugriff" if has_access else "✗ Kein Zugriff"
    print(f"  ID {user_id}: {username} - {status}")

db.close()
