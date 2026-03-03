#!/usr/bin/env python3
"""Start Flask without debug reload to preserve env"""
import subprocess
import time
import requests
import sys
import os

# Set environment with .env
from dotenv import load_dotenv
env_path = "C:\\Users\\TrifectaAgent\\trifecta-ai-agent\\.env"
load_dotenv(env_path)

env = os.environ.copy()
env['FLASK_ENV'] = 'production'  # Disable debug reload
env['FLASK_DEBUG'] = '0'

print("Starting Flask (production mode - no reload)...")
proc = subprocess.Popen(
    [sys.executable, "app.py"],
    cwd="C:\\Users\\TrifectaAgent\\trifecta-ai-agent",
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    env=env
)

print("Waiting for startup...")
time.sleep(6)

print("\nChecking health...")
try:
    r = requests.get('http://127.0.0.1:8000/health', timeout=5)
    data = r.json()
    print(f"Anthropic connected: {data['services']['anthropic']}")
    if data['services']['anthropic']:
        print("✅ CLAUDE AI IS CONNECTED!")
    else:
        print("❌ Anthropic still showing False")
except Exception as e:
    print(f"Error: {e}")

print("\nTesting chat...")
try:
    r = requests.post(
        'http://127.0.0.1:8000/api/chat',
        json={'message': 'What programs do you offer for addiction recovery?'},
        timeout=60
    )
    data = r.json()
    reply = data.get('reply', 'NO REPLY')
    if 'Trifecta AI Agent Orchestration System' in reply[:100]:
        print("Response: Skill content (fallback)")
    else:
        print(f"✅ REAL CLAUDE RESPONSE: {reply[:300]}...")
except Exception as e:
    print(f"Chat error: {e}")

print("\nStopping Flask...")
proc.terminate()
proc.wait()
print("Done.")
