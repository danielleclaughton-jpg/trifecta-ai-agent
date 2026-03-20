import sqlite3
conn = sqlite3.connect('lead_pipeline.db')
c = conn.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
print('Tables:', [r[0] for r in c.fetchall()])
c.execute('SELECT COUNT(*) FROM leads')
print('Total leads:', c.fetchone()[0])
c.execute('SELECT * FROM leads LIMIT 3')
cols = [d[0] for d in c.description]
print('Columns:', cols)
for row in c.fetchall():
    print(dict(zip(cols, row)))
conn.close()
