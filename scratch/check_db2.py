import sqlite3
conn = sqlite3.connect('database/oriflame.db')
cur = conn.cursor()
cur.execute('SELECT id, name, parent_id FROM products WHERE name LIKE "%Lipstick%"')
for row in cur.fetchall():
    print(row)
