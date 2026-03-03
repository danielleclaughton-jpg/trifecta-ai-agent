#!/usr/bin/env python3
"""Direct test of Config and Anthropic"""
import os
from pathlib import Path

# Set up path and load env like app.py does
env_path = os.path.join(os.path.dirname(os.path.abspath("C:\\Users\\TrifectaAgent\\trifecta-ai-agent\\app.py")), '.env')

from dotenv import load_dotenv
load_dotenv(env_path)

# Now import Config like app.py does
os.chdir("C:\\Users\\TrifectaAgent\\trifecta-ai-agent")

# Import app to get Config
import app as trifecta_app

print(f"Config.ANTHROPIC_API_KEY: {trifecta_app.Config.ANTHROPIC_API_KEY[:30]}...")
print(f"bool(Config.ANTHROPIC_API_KEY): {bool(trifecta_app.Config.ANTHROPIC_API_KEY)}")
