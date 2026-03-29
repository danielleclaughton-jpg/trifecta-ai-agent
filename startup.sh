#!/bin/bash
cd /home/site/wwwroot

# Install dependencies
pip install -r requirements.txt

# Ensure persistent data directory exists
mkdir -p /home/data

# Start gunicorn
exec gunicorn --bind=0.0.0.0:8000 \
         --workers=2 \
         --threads=4 \
         --timeout=120 \
         --access-logfile=- \
         --error-logfile=- \
         --log-level=info \
         app:app
