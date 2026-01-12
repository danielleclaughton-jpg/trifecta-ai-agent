"""Test chat endpoint with API key"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Check if API key is loaded
api_key = os.environ.get('ANTHROPIC_API_KEY', '')
if api_key:
    print(f"[OK] API Key loaded: {api_key[:20]}...{api_key[-10:]}")
else:
    print("[ERROR] API Key not found in environment")
    sys.exit(1)

# Import and start Flask app
from app import app
import threading
import time
import requests

def run_app():
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)

# Start Flask in background thread
print("Starting Flask app...")
t = threading.Thread(target=run_app, daemon=True)
t.start()
time.sleep(3)  # Wait for app to start

# Test chat endpoint
print("\n" + "="*50)
print("Testing /api/chat endpoint")
print("="*50)

try:
    response = requests.post(
        'http://127.0.0.1:5000/api/chat',
        json={'message': 'Hello! What services does Trifecta offer?'},
        timeout=30
    )
    
    print(f"\nStatus Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("\n[SUCCESS] Chat endpoint is working!")
        print(f"\nReply: {data.get('reply', '')[:200]}...")
        print(f"Matched Skill: {data.get('matched_skill', 'None')}")
        print(f"Timestamp: {data.get('timestamp', '')}")
    else:
        print(f"\n[ERROR] Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
except requests.exceptions.Timeout:
    print("\n[ERROR] Request timed out (30 seconds)")
except Exception as e:
    print(f"\n[ERROR] {e}")

print("\n" + "="*50)
