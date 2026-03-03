#!/usr/bin/env python3
"""Direct Flask test - bypass reloader entirely"""
import os
os.environ['FLASK_DEBUG'] = '0'
os.environ['WERKZEUG_DEBUG_PIN'] = 'off'

from dotenv import load_dotenv
env_path = "C:\\Users\\TrifectaAgent\\trifecta-ai-agent\\.env"
load_dotenv(env_path)

from app import app, Config
import requests

print(f"Config.ANTHROPIC_API_KEY: {bool(Config.ANTHROPIC_API_KEY)}")
print(f"os.environ ANTHROPIC: {bool(os.environ.get('ANTHROPIC_API_KEY'))}")

# Don't use app.run() - it enables reloader
# Just test the endpoints directly

print("\nTesting /health...")
with app.test_client() as client:
    r = client.get('/health')
    data = r.get_json()
    print(f"Anthropic: {data['services']['anthropic']}")
    
    if data['services']['anthropic']:
        print("\n✅ CLAUDE CONNECTED!")
        
        print("\nTesting chat...")
        r = client.post('/api/chat', json={'message': 'What programs do you offer?'})
        data = r.get_json()
        reply = data.get('reply', '')
        if 'Trifecta' in reply or 'Claude' in reply:
            print(f"✅ REAL AI: {reply[:400]}...")
        else:
            print(f"Response: {reply[:200]}...")
    else:
        print("\n❌ Anthropic still false")
