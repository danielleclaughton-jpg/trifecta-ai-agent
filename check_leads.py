import sqlite3
conn = sqlite3.connect('lead_pipeline.db')
c = conn.cursor()
c.execute("PRAGMA table_info(leads)")
cols = [row[1] for row in c.fetchall()]
print("COLUMNS:", cols)
c.execute("SELECT * FROM leads")
rows = c.fetchall()
for r in rows:
    print(r)
conn.close()
