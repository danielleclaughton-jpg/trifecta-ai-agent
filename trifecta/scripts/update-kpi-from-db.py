#!/usr/bin/env python3
"""
update-kpi-from-db.py
Scans the Trifecta data sources and updates live-kpis.json with fresh counts.
Call this from cron after Scout/Quill runs, or manually.
"""

import json
import os
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR = Path(r"C:\Users\TrifectaAgent\trifecta-ai-agent")
DB_PATH = BASE_DIR / "lead_pipeline.db"
SENT_LOG = BASE_DIR / "trifecta" / "outbound" / "sent-log.jsonl"
POSTED_DIR = BASE_DIR / "trifecta" / "content" / "posted"
KPI_FILE = BASE_DIR / "trifecta" / "kpi" / "live-kpis.json"

# ── Helpers ──────────────────────────────────────────────────────────────────
def utcnow_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def load_kpis():
    """Load existing KPIs, return defaults if missing."""
    default = {
        "updated": utcnow_iso(),
        "leads_today": 0,
        "leads_total": 0,
        "emails_sent_today": 0,
        "emails_sent_week": 0,
        "content_posted_today": 0,
        "content_posted_week": 0,
        "active_clients": 3,
        "monthly_revenue": 0,
        "conversion_rate": 0.0,
        "pipeline_value": 0,
    }
    try:
        with open(KPI_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default

def save_kpis(kpis):
    """Save KPIs atomically."""
    kpis["updated"] = utcnow_iso()
    os.makedirs(KPI_FILE.parent, exist_ok=True)
    tmp = str(KPI_FILE) + ".tmp"
    with open(tmp, "w") as f:
        json.dump(kpis, f, indent=2)
    os.replace(tmp, KPI_FILE)

# ── Count leads from SQLite ───────────────────────────────────────────────────
def count_leads_from_db():
    """Returns (leads_total, leads_today)."""
    if not DB_PATH.exists():
        print(f"[KPI] DB not found at {DB_PATH}")
        return 0, 0
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) FROM leads")
        total = cur.fetchone()[0] or 0

        # Count leads created today (compare date part of created_at)
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        cur.execute(
            "SELECT COUNT(*) FROM leads WHERE DATE(created_at) = ?",
            (today,)
        )
        today_count = cur.fetchone()[0] or 0

        conn.close()
        print(f"[KPI] DB: {total} total leads, {today_count} today")
        return total, today_count
    except sqlite3.Error as e:
        print(f"[KPI] DB error: {e}")
        return 0, 0

# ── Count emails sent ─────────────────────────────────────────────────────────
def count_emails_sent():
    """Returns (emails_today, emails_week) by reading sent-log.jsonl."""
    today_count = 0
    week_count = 0
    if not SENT_LOG.exists():
        print(f"[KPI] Sent log not found at {SENT_LOG}")
        return 0, 0
    try:
        today = datetime.now(timezone.utc).date()
        week_ago = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        # Go back 7 days
        import datetime as dt
        week_ago = datetime.now(timezone.utc) - dt.timedelta(days=7)

        with open(SENT_LOG, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                # Each line should have a "timestamp" or "sent_at" ISO string
                ts_str = entry.get("timestamp") or entry.get("sent_at") or entry.get("created_at", "")
                try:
                    # Parse ISO timestamp
                    ts_str = ts_str.replace("Z", "+00:00")
                    if "+" not in ts_str and "-" in ts_str and ts_str.count("-") == 2:
                        ts_str += "+00:00"
                    dt_entry = datetime.fromisoformat(ts_str.replace("+00:00", ""))
                    dt_entry_utc = dt_entry.astimezone(timezone.utc)
                    if dt_entry_utc.date() == today:
                        today_count += 1
                    if dt_entry_utc >= week_ago:
                        week_count += 1
                except (ValueError, TypeError):
                    # Fallback: count all lines as week total
                    week_count += 1
        print(f"[KPI] Emails: {today_count} today, {week_count} this week")
        return today_count, week_count
    except Exception as e:
        print(f"[KPI] Sent log error: {e}")
        return 0, 0

# ── Count content posted ──────────────────────────────────────────────────────
def count_content_posted():
    """Returns (posted_today, posted_week) by scanning posted/ folder."""
    today_count = 0
    week_count = 0
    if not POSTED_DIR.exists():
        print(f"[KPI] Posted dir not found at {POSTED_DIR}")
        return 0, 0
    try:
        today = datetime.now(timezone.utc).date()
        import datetime as dt
        week_ago = datetime.now(timezone.utc) - dt.timedelta(days=7)

        for fpath in POSTED_DIR.iterdir():
            if fpath.is_file():
                mtime = datetime.fromtimestamp(fpath.stat().st_mtime, tz=timezone.utc)
                if mtime.date() == today:
                    today_count += 1
                if mtime >= week_ago:
                    week_count += 1
        print(f"[KPI] Content: {today_count} posted today, {week_count} this week")
        return today_count, week_count
    except Exception as e:
        print(f"[KPI] Posted dir error: {e}")
        return 0, 0

# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    print(f"[KPI] Running KPI update at {utcnow_iso()}")

    leads_total, leads_today = count_leads_from_db()
    emails_today, emails_week = count_emails_sent()
    content_today, content_week = count_content_posted()

    kpis = load_kpis()
    kpis["leads_total"] = leads_total
    kpis["leads_today"] = leads_today
    kpis["emails_sent_today"] = emails_today
    kpis["emails_sent_week"] = emails_week
    kpis["content_posted_today"] = content_today
    kpis["content_posted_week"] = content_week

    save_kpis(kpis)
    print(f"[KPI] Saved to {KPI_FILE}")
    print(f"[KPI] Final KPIs: {json.dumps(kpis, indent=2)}")

if __name__ == "__main__":
    main()
