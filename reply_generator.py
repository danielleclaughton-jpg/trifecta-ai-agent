#!/usr/bin/env python3
"""
Draft personalized responses for new leads using Claude API.
"""
import os
import sqlite3
from datetime import datetime
import requests as http_requests

# Configuration
DB_PATH = "lead_pipeline.db"
LOG_DIR = ".logs"

FLASK_API_URL = os.environ.get("FLASK_API_URL", "http://localhost:5000")

def log_action(message):
    """Log action to file and console."""
    timestamp = datetime.now().isoformat()
    log_msg = f"[{timestamp}] {message}"
    print(log_msg)
    
    log_file = os.path.join(LOG_DIR, f"auto-reply-{datetime.now().strftime('%Y-%m-%d')}.log")
    with open(log_file, "a") as f:
        f.write(log_msg + "\n")

def get_awaiting_response_leads():
    """Get leads that need responses drafted."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, contact_email, initial_message, contact_name
            FROM leads
            WHERE status = 'AWAITING_RESPONSE' 
            AND draft_response IS NULL
            LIMIT 10
        """)
        
        leads = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        log_action(f"Found {len(leads)} leads awaiting response drafts")
        return leads
        
    except Exception as e:
        log_action(f"ERROR fetching awaiting-response leads: {str(e)}")
        return []

def draft_response(lead_message):
    """Use Claude to draft a warm, professional response."""
    try:
        prompt = f"""You are a warm, professional addiction recovery intake specialist responding to a potential client inquiry.

The client wrote:
'{lead_message}'

Draft a brief, 2-sentence response that:
1. Acknowledges their inquiry with empathy
2. Invites them to the next step (consultation call or program info)

Keep it professional, warm, and human. No marketing jargon.
Do NOT use em dashes (--). Use commas, periods, or colons instead."""

        # Use Flask API layer (avoids Python 3.14 Anthropic SDK incompatibility)
        resp = http_requests.post(
            f"{FLASK_API_URL}/api/chat",
            json={"message": prompt, "skill": "trifecta-lead-intake-workflow"},
            timeout=60
        )
        resp.raise_for_status()
        data = resp.json()
        response_text = data.get("response") or data.get("message") or str(data)
        log_action(f"Flask/Claude drafted response ({len(response_text)} chars)")
        return response_text
        
    except Exception as e:
        log_action(f"ERROR drafting response with Claude: {str(e)}")
        return None

def store_draft_response(lead_id, draft_response):
    """Store drafted response in database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE leads
            SET draft_response = ?, status = 'AWAITING_SEND'
            WHERE id = ?
        """, (draft_response, lead_id))
        
        conn.commit()
        conn.close()
        
        return True
        
    except Exception as e:
        log_action(f"ERROR storing draft: {str(e)}")
        return False

if __name__ == "__main__":
    log_action("Starting response generation...")
    
    # Get leads that need responses
    leads = get_awaiting_response_leads()
    
    drafted_count = 0
    for lead in leads:
        log_action(f"Drafting response for lead {lead['id']} ({lead['contact_email']})")
        
        draft = draft_response(lead['initial_message'])
        if draft:
            if store_draft_response(lead['id'], draft):
                drafted_count += 1
                log_action(f"Stored draft for lead {lead['id']}")
    
    log_action(f"Response generation complete. Drafted {drafted_count} responses.")
