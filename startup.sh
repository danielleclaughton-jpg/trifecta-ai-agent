#!/bin/bash
cd /home/site/wwwroot

# Install dependencies if not already present
pip install -r requirements.txt --quiet 2>&1 | tail -5

# Start gunicorn
gunicorn --bind=0.0.0.0:8000 \
         --workers=2 \
         --threads=4 \
         --timeout=120 \
         --access-logfile=- \
         --error-logfile=- \
         --log-level=info \
         app:app
