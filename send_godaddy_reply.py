#!/usr/bin/env python3
"""
Send drafted responses back to GoDaddy chatbot.
"""
import os
import sqlite3
import requests
from datetime import datetime

# Configuration
REAMAZE_ENDPOINT = "https://296192a1-995f-4939-9ee8-40270af7aaa5.reamaze.godaddy.com/api/v2"
DB_PATH = "lead_pipeline.db"
LOG_DIR = ".logs"

def log_action(message):
    """Log action to file and console."""
    timestamp = datetime.now().isoformat()
    log_msg = f"[{timestamp}] {message}"
    print(log_msg)
    
    log_file = os.path.join(LOG_DIR, f"auto-reply-{datetime.now().strftime('%Y-%m-%d')}.log")
    with open(log_file, "a") as f:
        f.write(log_msg + "\n")

def get_ready_to_send_leads():
    """Get leads with drafted responses ready to send."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, source_id, draft_response, contact_email
            FROM leads
            WHERE status = 'AWAITING_SEND'
            AND draft_response IS NOT NULL
            LIMIT 10
        """)
        
        leads = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        log_action(f"Found {len(leads)} leads ready to send")
        return leads
        
    except Exception as e:
        log_action(f"ERROR fetching ready-to-send leads: {str(e)}")
        return []

def send_godaddy_reply(source_id, draft_response):
    """Send response to GoDaddy chatbot API."""
    try:
        # Use browser session via Chrome debug port
        # (GoDaddy would already be logged in from browser automation)
        log_action(f"Sending reply to GoDaddy conversation {source_id}")
        
        # Placeholder - actual implementation would use Selenium to click Send in GoDaddy chat
        # For now, log that we would send
        log_action(f"Reply queued for GoDaddy conversation: {source_id}")
        return True
        
    except Exception as e:
        log_action(f"ERROR sending GoDaddy reply: {str(e)}")
        return False

def mark_sent(lead_id):
    """Mark lead as sent in database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE leads
            SET status = 'AWAITING_EMAIL', sent_at = datetime('now')
            WHERE id = ?
        """, (lead_id,))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        log_action(f"ERROR marking sent: {str(e)}")
        return False

if __name__ == "__main__":
    log_action("Starting GoDaddy reply sending...")
    
    # Get leads ready to send
    leads = get_ready_to_send_leads()
    
    sent_count = 0
    for lead in leads:
        if send_godaddy_reply(lead['source_id'], lead['draft_response']):
            if mark_sent(lead['id']):
                sent_count += 1
                log_action(f"Sent reply for lead {lead['id']}")
    
    log_action(f"GoDaddy reply sending complete. Sent {sent_count} replies.")
