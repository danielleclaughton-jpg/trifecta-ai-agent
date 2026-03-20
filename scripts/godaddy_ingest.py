"""Ingest GoDaddy conversations into lead_pipeline.db from JSON export."""
import json
import sqlite3
import sys
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "lead_pipeline.db")

# Status codes from GoDaddy Re:amaze API
STATUS_MAP = {
    0: "open",
    1: "pending",  # replied/waiting on customer
    7: "spam",
    8: "resolved",
}

def ingest(conversations_json, messages_json=None):
    conversations = json.loads(conversations_json)
    messages_by_id = {}
    if messages_json:
        for entry in json.loads(messages_json):
            messages_by_id[entry["conversation_id"]] = entry["messages"]

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Get existing godaddy leads by external_id
    cur.execute("SELECT external_id FROM leads WHERE source = 'godaddy_chat'")
    existing = {row["external_id"] for row in cur.fetchall()}

    ingested = 0
    updated = 0
    skipped = 0

    for conv in conversations:
        ext_id = f"gd-{conv['id']}"
        status_code = conv.get("status", 0)
        gd_status = STATUS_MAP.get(status_code, "open")

        # Map GoDaddy status to our pipeline workflow_stage
        if gd_status == "resolved":
            stage = "ARCHIVED_CLOSED"
        elif gd_status == "pending":
            stage = "AWAITING_HUMAN_RESPONSE"
        elif gd_status == "spam":
            stage = "ARCHIVED_CLOSED"
        else:
            stage = "NEEDS_REVIEW_ERROR"

        # Extract display name and email from messages if available
        display_name = conv.get("display_name", "")
        email = conv.get("email", "")
        subject = conv.get("subject", "")
        msg_count = conv.get("message_count", 0)
        created = conv.get("created_at", "")
        updated_at = conv.get("updated_at", "")

        # Try to get name/email from messages
        msgs = messages_by_id.get(conv["id"], [])
        customer_name = ""
        customer_email = ""
        first_message = ""
        for m in reversed(msgs):  # oldest first
            s_type = m.get("sender_type", "")
            s_name = m.get("sender_name", "")
            s_email = m.get("sender_email", "")
            body = m.get("body", "")
            if s_name and "Guest User" not in s_name and "Trifecta" not in s_name:
                customer_name = s_name
            if s_email and "trifecta" not in s_email.lower():
                customer_email = s_email
            if body and not first_message and "Trifecta" not in body[:50]:
                first_message = body[:500]

        # If someone asked "Talk to a human", bump to AWAITING_HUMAN_RESPONSE
        for m in msgs:
            if "talk to a human" in (m.get("body", "") or "").lower():
                stage = "AWAITING_HUMAN_RESPONSE"
                break

        # Determine name to use
        name = customer_name or display_name or ""
        if "Guest User" in name:
            name = f"GoDaddy Chat #{conv['id']}"
        email_to_use = customer_email or email or ""

        # Notes
        notes = f"Subject: {subject}\nMessages: {msg_count}\n"
        if first_message:
            notes += f"First message: {first_message[:300]}\n"
        notes += f"GoDaddy status: {gd_status} (code {status_code})"

        if ext_id in existing:
            # Update existing lead
            cur.execute("""
                UPDATE leads SET
                    workflow_stage = CASE
                        WHEN workflow_stage IN ('ARCHIVED_CLOSED') THEN workflow_stage
                        ELSE ?
                    END,
                    notes = ?,
                    updated_at = ?
                WHERE external_id = ? AND source = 'godaddy_chat'
            """, (stage, notes, updated_at or datetime.utcnow().isoformat(), ext_id))
            updated += 1
        else:
            # Insert new lead
            cur.execute("""
                INSERT INTO leads (
                    external_id, source, name, email, phone,
                    workflow_stage, score, notes,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                ext_id, "godaddy_chat", name, email_to_use, "",
                stage, 0, notes,
                created or datetime.utcnow().isoformat(),
                updated_at or datetime.utcnow().isoformat()
            ))
            ingested += 1

    conn.commit()

    # Get total count
    cur.execute("SELECT COUNT(*) as cnt FROM leads")
    total = cur.fetchone()["cnt"]

    conn.close()
    return {"ingested": ingested, "updated": updated, "skipped": skipped, "total_leads": total}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python godaddy_ingest.py <conversations.json> [messages.json]")
        sys.exit(1)

    with open(sys.argv[1]) as f:
        conv_data = f.read()

    msg_data = None
    if len(sys.argv) > 2:
        with open(sys.argv[2]) as f:
            msg_data = f.read()

    result = ingest(conv_data, msg_data)
    print(json.dumps(result, indent=2))
