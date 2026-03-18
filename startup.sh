#!/bin/bash
cd /home/site/wwwroot

# Install dependencies if not already present
pip install -r requirements.txt --quiet 2>&1 | tail -5

# Ensure persistent data directory exists
mkdir -p /home/data

# Start gunicorn (--preload ensures scheduler runs once in master, not per-worker)
gunicorn --bind=0.0.0.0:8000 \
         --preload \
         --workers=2 \
         --threads=4 \
         --timeout=120 \
         --access-logfile=- \
         --error-logfile=- \
         --log-level=info \
         app:app
