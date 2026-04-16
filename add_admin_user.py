import sqlite3
from werkzeug.security import generate_password_hash
import os

path = 'C:/Users/Administrator/Desktop/Repo clone/lernapp-apk/app/lernapp.db'
if not os.path.exists(path):
    raise SystemExit('Database not found: ' + path)

con = sqlite3.connect(path)
con.row_factory = sqlite3.Row
cur = con.cursor()
cur.execute('SELECT name FROM sqlite_master WHERE type="table" AND name="users"')
if not cur.fetchone():
    raise SystemExit('Users table not found')

username = 'admin'
password = 'Admin@123'
password_hash = generate_password_hash(password)

cur.execute('SELECT id FROM users WHERE username = ?', (username,))
row = cur.fetchone()
if row:
    cur.execute('UPDATE users SET password_hash = ? WHERE username = ?', (password_hash, username))
    print(f'Updated existing admin user, password set to {password}')
else:
    cur.execute('INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, datetime("now"))', (username, password_hash))
    print(f'Created admin user with username "{username}" and password "{password}"')
con.commit()
con.close()
