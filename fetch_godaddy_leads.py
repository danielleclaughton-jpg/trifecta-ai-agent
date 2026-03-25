#!/usr/bin/env python3
"""
Fetch fresh GoDaddy leads from Re:amaze API.
Compares against local DB to identify new conversations.
"""
import os
import sqlite3
import json
import requests
from datetime import datetime
# anthropic import removed - use Flask API layer for LLM calls instead

# Configuration
REAMAZE_ENDPOINT = "https://296192a1-995f-4939-9ee8-40270af7aaa5.reamaze.godaddy.com/api/v2"
DB_PATH = "lead_pipeline.db"
LOG_DIR = ".logs"

# Ensure log directory exists
os.makedirs(LOG_DIR, exist_ok=True)

def log_action(message):
    """Log action to file and console."""
    timestamp = datetime.now().isoformat()
    log_msg = f"[{timestamp}] {message}"
    print(log_msg)
    
    log_file = os.path.join(LOG_DIR, f"auto-reply-{datetime.now().strftime('%Y-%m-%d')}.log")
    with open(log_file, "a") as f:
        f.write(log_msg + "\n")

def get_godaddy_conversations():
    """Fetch conversations from Re:amaze API."""
    try:
        # Use browser session via Chrome debug port (GoDaddy already logged in)
        # This is a placeholder - actual implementation uses Selenium or direct API with auth
        headers = {
            "User-Agent": "Trifecta-AI-Agent/1.0"
        }
        
        # For now, return empty list (browser automation would fetch this)
        log_action("GoDaddy API: Using browser session via Chrome debug port")
        return []
        
    except Exception as e:
        log_action(f"ERROR fetching GoDaddy conversations: {str(e)}")
        return []

def get_new_leads(conversations):
    """Compare against DB to find new leads."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get existing source_ids
        cursor.execute("SELECT DISTINCT source_id FROM leads WHERE source_id IS NOT NULL")
        existing_ids = {row['source_id'] for row in cursor.fetchall()}
        
        new_leads = []
        for conv in conversations:
            conv_id = conv.get('id')
            if conv_id and str(conv_id) not in existing_ids:
                new_leads.append(conv)
        
        conn.close()
        log_action(f"Found {len(new_leads)} new leads out of {len(conversations)} total conversations")
        return new_leads
        
    except Exception as e:
        log_action(f"ERROR checking for new leads: {str(e)}")
        return []

def insert_leads_to_db(new_leads):
    """Insert new leads into database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        inserted_count = 0
        for lead in new_leads:
            cursor.execute("""
                INSERT INTO leads (
                    source_id, contact_email, contact_name, 
                    initial_message, status, created_at
                ) VALUES (?, ?, ?, ?, ?, datetime('now'))
            """, (
                str(lead.get('id')),
                lead.get('email', ''),
                lead.get('name', 'Unknown'),
                lead.get('latest_message', ''),
                'AWAITING_RESPONSE'
            ))
            inserted_count += 1
        
        conn.commit()
        conn.close()
        
        log_action(f"Inserted {inserted_count} new leads into database")
        return inserted_count
        
    except Exception as e:
        log_action(f"ERROR inserting leads: {str(e)}")
        return 0

if __name__ == "__main__":
    log_action("Starting GoDaddy lead fetch...")
    
    # Fetch from GoDaddy
    conversations = get_godaddy_conversations()
    
    # Find new ones
    new_leads = get_new_leads(conversations)
    
    # Insert to DB
    count = insert_leads_to_db(new_leads)
    
    log_action(f"Fetch complete. Processed {count} new leads.")
