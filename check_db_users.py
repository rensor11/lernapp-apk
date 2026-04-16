import sqlite3
import os
path = 'C:/Users/Administrator/Desktop/Repo clone/lernapp-apk/app/lernapp.db'
if not os.path.exists(path):
    print('NO_DB')
    raise SystemExit(0)
con = sqlite3.connect(path)
cur = con.cursor()
cur.execute('SELECT name FROM sqlite_master WHERE type="table" AND name="users"')
r = cur.fetchone()
if not r:
    print('NO_USERS_TABLE')
    raise SystemExit(0)
cur.execute('SELECT id, username, password_hash FROM users')
rows = cur.fetchall()
if not rows:
    print('NO_USERS')
else:
    for x in rows:
        print(x[0], x[1], x[2][:20])
con.close()
