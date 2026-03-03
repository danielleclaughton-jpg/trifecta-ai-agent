#!/usr/bin/env python3
"""Set env first, then start Flask"""
import os
from dotenv import load_dotenv

# CRITICAL: Load .env FIRST before any other imports
env_path = "C:\\Users\\TrifectaAgent\\trifecta-ai-agent\\.env"
load_dotenv(env_path)

# Verify key is loaded
key = os.environ.get('ANTHROPIC_API_KEY', '')
print(f"ANTHROPIC_API_KEY in env: {bool(key)}")

# Now import and run Flask
from app import app
import requests

print("Flask imported. Testing health...")

# Test health
r = requests.get('http://127.0.0.1:8000/health', timeout=5)
data = r.json()
print(f"Anthropic in health check: {data['services']['anthropic']}")

if data['services']['anthropic']:
    print("✅ SUCCESS! Claude is connected!")
    
    # Test real chat
    print("\nTesting real Claude chat...")
    r = requests.post(
        'http://127.0.0.1:8000/api/chat',
        json={'message': 'What is your name and what services does Trifecta provide?'},
        timeout=60
    )
    data = r.json()
    reply = data.get('reply', '')
    if 'Trifecta' in reply or 'Claude' in reply:
        print(f"✅ REAL AI RESPONSE: {reply[:400]}...")
    else:
        print(f"Response: {reply[:200]}...")
else:
    print("❌ Anthropic still not connected")
