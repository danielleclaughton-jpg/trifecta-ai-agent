import sqlite3
from datetime import datetime, timezone

conn = sqlite3.connect('lead_pipeline.db')
c = conn.cursor()

now = datetime.now(timezone.utc).isoformat()

items = [
    ('Blog Post — Behavioral Activation (Fri Mar 20)',
     'Getting Off the Couch: How Behavioral Activation Helps Break the Cycle of Depression and Addiction. ~800 words. Full draft in #content-quill.',
     'content', 'normal'),
    ('Google Business Post — Behavioral Activation',
     'Calgary/Alberta local focus, 175 words, CTA to book consultation. Full draft in #content-quill.',
     'content', 'normal'),
    ('Facebook Post — Friday Reflection (Behavioral Activation)',
     'Conversational, community tone, 130 words, links to trifectaaddictionservices.com. Full draft in #content-quill.',
     'content', 'normal'),
    ('Instagram Caption — Behavioral Activation',
     'Inspirational, morning walk image suggestion, 100 words. Full draft in #content-quill.',
     'content', 'normal'),
    ('LinkedIn Post — Behavioral Activation (Executive Angle)',
     'High-performer / EAP audience, 200 words. Full draft in #content-quill.',
     'content', 'normal'),
    ('Email — Betty (Withdrawal Check-In for Luke)',
     'To: betty@cmlshield.com — Caring check-in on Lukes withdrawal safety. Draft in #ceo-lamby.',
     'email', 'high'),
    ('Email — Pamela (First Contact)',
     'To: waypamela9@gmail.com — First outreach, telescope method. Draft in #ceo-lamby.',
     'email', 'high'),
    ('Email — William Ball (Follow-Up)',
     'To: wbj19671@outlook.com — Warm follow-up, first contact. Draft in #intake-scout.',
     'email', 'high'),
]

inserted = 0
for item in items:
    title, description, category, priority = item
    # Check if already exists
    existing = c.execute('SELECT id FROM approvals WHERE title = ?', (title,)).fetchone()
    if not existing:
        c.execute('''
            INSERT INTO approvals (title, description, category, status, priority, created_at, updated_at)
            VALUES (?, ?, ?, 'pending', ?, ?, ?)
        ''', (title, description, category, priority, now, now))
        inserted += 1

conn.commit()
print(f"Inserted {inserted} approvals")
conn.close()
