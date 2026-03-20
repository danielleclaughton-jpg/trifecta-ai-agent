import sqlite3
from datetime import datetime

conn = sqlite3.connect('lead_pipeline.db')
c = conn.cursor()

now = datetime.utcnow().isoformat() + 'Z'

# Add Pamela
c.execute("""
    INSERT OR IGNORE INTO leads (id, name, email, source, status, initial_question, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
""", ('gd-011', 'Pamela', 'waypamela9@gmail.com', 'GODADDY', 'INQUIRY_RECEIVED', 'Left GoDaddy chat, needs follow-up', now, now))

# Update William Ball name
c.execute("""
    UPDATE leads SET name = 'William Ball', updated_at = ? WHERE id = 'gd-006'
""", (now,))

conn.commit()
print("Done")
conn.close()
