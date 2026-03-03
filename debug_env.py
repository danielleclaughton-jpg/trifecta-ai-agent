#!/usr/bin/env python3
"""Debug .env loading in app context"""
import os
import sys
from pathlib import Path

# Add app dir to path
sys.path.insert(0, "C:\\Users\\TrifectaAgent\\trifecta-ai-agent")

# Simulate what app.py does
env_path = os.path.join(os.path.dirname(os.path.abspath("C:\\Users\\TrifectaAgent\\trifecta-ai-agent\\app.py")), '.env')
print(f"Looking for .env at: {env_path}")
print(f"File exists: {os.path.exists(env_path)}")

from dotenv import load_dotenv
load_dotenv(env_path)

key = os.environ.get('ANTHROPIC_API_KEY', 'NOT SET')
if key == 'NOT SET':
    print("KEY NOT LOADED")
else:
    print(f"KEY LOADED: {key[:30]}...")
