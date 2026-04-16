#!/usr/bin/env python3
import sqlite3
import shutil

# Backup der neuen DB erstellen
shutil.copy('lernapp.db', 'lernapp.db.backup')
print("✅ Backup erstellt: lernapp.db.backup")

# Alte und neue DB verbinden
old_db = sqlite3.connect('app/lernapp.db')
new_db = sqlite3.connect('lernapp.db')

# Alle Benutzer aus alter DB in neue kopieren
old_cursor = old_db.cursor()
new_cursor = new_db.cursor()

# Benutzer auslesen
old_cursor.execute('SELECT * FROM users')
users = old_cursor.fetchall()

print(f"\n📋 Gefundene Benutzer in alter DB: {len(users)}")

# Column Names auslesen
old_cursor.execute("PRAGMA table_info(users)")
columns = old_cursor.fetchall()
col_names = [col[1] for col in columns]

print("Spalten:", col_names)

# Benutzer in neue DB einfügen
for user in users:
    try:
        placeholders = ','.join(['?' for _ in col_names])
        query = f"INSERT INTO users ({','.join(col_names)}) VALUES ({placeholders})"
        new_cursor.execute(query, user)
        print(f"  ✓ Benutzer '{user[1]}' (ID {user[0]}) kopiert")
    except sqlite3.IntegrityError as e:
        print(f"  ⚠ Benutzer '{user[1]}' existiert bereits")
    except Exception as e:
        print(f"  ✗ Fehler bei '{user[1]}': {e}")

new_db.commit()

# Überprüfe finale Benutzer in neuer DB
new_cursor.execute('SELECT id, username, home_access_allowed FROM users')
all_users = new_cursor.fetchall()

print(f"\n✅ Finale Benutzer in neuer DB: {len(all_users)}")
for user_id, username, has_access in all_users:
    status = "✓ Home-Zugriff" if has_access else "✗ Kein Home-Zugriff"
    print(f"  ID {user_id}: {username} - {status}")

old_db.close()
new_db.close()
