#!/usr/bin/env python3
"""Check Anthropic API key loading"""

import os
from dotenv import load_dotenv

load_dotenv()

key = os.environ.get('ANTHROPIC_API_KEY', 'NOT SET')

if key == 'NOT SET':
    print("ANTHROPIC_API_KEY: NOT SET - .env not loading!")
else:
    print(f"ANTHROPIC_API_KEY: {key[:25]}...")
    print(f"Length: {len(key)}")

# Also check current env
env_key = os.environ.get('ANTHROPIC_API_KEY', None)
print(f"\nDirect os.environ: {'SET' if env_key else 'NOT SET'}")
