#!/usr/bin/env python3
"""
Automated lead reply loop.
Runs every 5 minutes to:
1. Fetch new GoDaddy conversations
2. Draft responses with Claude
3. Send replies back to GoDaddy
4. Sync to spreadsheet
"""
import os
import json
import subprocess
from datetime import datetime
import time

LOG_DIR = ".logs"

def log_action(message):
    """Log action to file and console."""
    timestamp = datetime.now().isoformat()
    log_msg = f"[{timestamp}] {message}"
    print(log_msg)
    
    log_file = os.path.join(LOG_DIR, f"auto-reply-{datetime.now().strftime('%Y-%m-%d')}.log")
    os.makedirs(LOG_DIR, exist_ok=True)
    with open(log_file, "a") as f:
        f.write(log_msg + "\n")

VENV_PYTHON = os.path.join(os.path.dirname(__file__), '.venv', 'Scripts', 'python.exe')
if not os.path.exists(VENV_PYTHON):
    VENV_PYTHON = 'python'  # fallback

STATUS_DIR = os.path.join(
    os.path.expanduser('~'), '.openclaw',
    'workspaceopenclaw gateway', 'trifecta', 'agent-status'
)

def write_scout_status(status: str, leads_processed: int = 0, errors: list = None):
    """Write Scout agent status to the shared status directory."""
    os.makedirs(STATUS_DIR, exist_ok=True)
    from datetime import timezone
    existing = {}
    scout_file = os.path.join(STATUS_DIR, 'scout.json')
    if os.path.exists(scout_file):
        try:
            with open(scout_file, 'r') as f:
                existing = json.load(f)
        except Exception:
            pass
    existing['auto_reply_status'] = status
    existing['auto_reply_last_run'] = datetime.now(timezone.utc).isoformat()
    existing['auto_reply_leads_processed'] = leads_processed
    if errors:
        existing['auto_reply_errors'] = errors
    with open(scout_file, 'w') as f:
        json.dump(existing, f, indent=2)

def run_step(script_name):
    """Run a Python script and return success status."""
    try:
        log_action(f"Running {script_name}...")
        result = subprocess.run([VENV_PYTHON, script_name], capture_output=True, timeout=120)
        
        if result.returncode == 0:
            log_action(f"{script_name} completed successfully")
            return True
        else:
            log_action(f"ERROR in {script_name}: {result.stderr.decode()}")
            return False
            
    except Exception as e:
        log_action(f"ERROR running {script_name}: {str(e)}")
        return False

def sync_to_spreadsheet():
    """Sync database to master spreadsheet."""
    try:
        log_action("Running spreadsheet sync...")
        result = subprocess.run([VENV_PYTHON, 'sync_spreadsheet.py'], capture_output=True, timeout=60)
        
        if result.returncode == 0:
            log_action("Spreadsheet sync completed")
            return True
        else:
            log_action(f"ERROR in spreadsheet sync: {result.stderr.decode()}")
            return False
            
    except Exception as e:
        log_action(f"ERROR syncing spreadsheet: {str(e)}")
        return False

def run_cycle():
    """Run one complete cycle of the automated reply loop."""
    log_action("========== AUTO-REPLY CYCLE START ==========")
    write_scout_status("running")
    errors = []

    # Step 1: Fetch new GoDaddy conversations
    if not run_step("fetch_godaddy_leads.py"):
        log_action("SKIPPING CYCLE: fetch failed")
        errors.append("fetch_godaddy_leads failed")
        write_scout_status("error", 0, errors)
        return False

    time.sleep(2)

    # Step 2: Draft responses with Claude
    if not run_step("reply_generator.py"):
        log_action("WARNING: reply generation failed, continuing...")
        errors.append("reply_generator failed")

    time.sleep(2)

    # Step 3: Send replies to GoDaddy
    if not run_step("send_godaddy_reply.py"):
        log_action("WARNING: sending failed, continuing...")
        errors.append("send_godaddy_reply failed")

    time.sleep(2)

    # Step 4: Sync to spreadsheet
    sync_to_spreadsheet()

    write_scout_status("idle", 0, errors if errors else None)
    log_action("========== AUTO-REPLY CYCLE COMPLETE ==========")
    return True

if __name__ == "__main__":
    log_action("Automated reply loop starting...")
    
    # Run single cycle for testing
    run_cycle()
    
    log_action("Auto-reply loop shutdown.")
