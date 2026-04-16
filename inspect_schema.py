import sqlite3
path = 'C:/Users/Administrator/Desktop/Repo clone/data/lernapp.db'
con = sqlite3.connect(path)
cur = con.cursor()
cur.execute('PRAGMA table_info(users)')
print(cur.fetchall())
con.close()
