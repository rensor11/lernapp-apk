import sqlite3
import hashlib
import os
from pathlib import Path

path = Path('C:/Users/Administrator/Desktop/Repo clone/data/lernapp.db')
if not path.exists():
    raise SystemExit('Database not found: ' + str(path))

username = 'admin'
password = 'Admin@123'

salt = os.urandom(16).hex()
password_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000).hex()

con = sqlite3.connect(str(path))
cur = con.cursor()
cur.execute('SELECT id FROM users WHERE LOWER(username) = LOWER(?)', (username,))
row = cur.fetchone()
if row:
    cur.execute('UPDATE users SET password_hash = ?, salt = ? WHERE id = ?', (password_hash, salt, row[0]))
    print(f'Updated admin user with password {password}')
else:
    cur.execute('INSERT INTO users (username, password_hash, salt, created_at) VALUES (?, ?, ?, datetime("now"))', (username, password_hash, salt))
    print(f'Created admin user with username "{username}" and password "{password}"')
con.commit()
con.close()
