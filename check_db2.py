import sqlite3
conn = sqlite3.connect('lead_pipeline.db')
c = conn.cursor()
c.execute('SELECT id, name, source, status, program_interest FROM leads')
for row in c.fetchall():
    print(f"  {row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]}")
c.execute('SELECT COUNT(*) FROM email_drafts')
print(f"\nEmail drafts: {c.fetchone()[0]}")
c.execute('SELECT COUNT(*) FROM lead_events')
print(f"Lead events: {c.fetchone()[0]}")
conn.close()
