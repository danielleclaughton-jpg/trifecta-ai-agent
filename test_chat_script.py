#!/usr/bin/env python3
"""Test Trifecta AI Agent chat functionality"""

import requests
import json

print("=" * 60)
print("TRIFECTA AI AGENT - CHAT TEST")
print("=" * 60)

# Test 1: Check health
print("\n1. Testing /health endpoint...")
response = requests.get('http://127.0.0.1:8000/health', timeout=5)
print(f"   Status: {response.status_code}")
print(f"   Response: {json.dumps(response.json(), indent=4)}")

# Test 2: List skills
print("\n2. Testing /api/skills endpoint...")
response = requests.get('http://127.0.0.1:8000/api/skills', timeout=5)
print(f"   Status: {response.status_code}")
data = response.json()
print(f"   Skills loaded: {data.get('count', 0)}")
print(f"   Sample skills: {[s.get('title') for s in data.get('skills', [])[:5]]}")

# Test 3: Chat with agent
print("\n3. Testing /api/chat endpoint...")
print("   Sending: 'What programs do you offer for addiction recovery?'")
response = requests.post(
    'http://127.0.0.1:8000/api/chat',
    json={'message': 'What programs do you offer for addiction recovery?'},
    timeout=30
)
print(f"   Status: {response.status_code}")
data = response.json()
print(f"   Matched Skill: {data.get('matched_skill', 'None')}")
print(f"   Matched Title: {data.get('skill_title', 'None')}")
print(f"\n   Agent Response:")
reply = data.get('reply', 'NO REPLY')
if reply and len(reply) > 500:
    print(f"   {reply[:500]}...")
else:
    print(f"   {reply}")

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
