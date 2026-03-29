#!/bin/bash
cd /home/site/wwwroot

# Ensure persistent data directory exists
mkdir -p /home/data

# Start gunicorn
# Note: pip install is handled by Oryx build at deploy time, not here
exec gunicorn --bind=0.0.0.0:8000 \
         --workers=2 \
         --threads=4 \
         --timeout=120 \
         --access-logfile=- \
         --error-logfile=- \
         --log-level=info \
         app:app
