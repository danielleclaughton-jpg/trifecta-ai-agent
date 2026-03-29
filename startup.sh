#!/bin/bash
cd /home/site/wwwroot

# Ensure persistent data directory exists
mkdir -p /home/data

# Activate Oryx-built virtual environment (if present)
# Azure/Oryx installs packages into antenv - must activate before gunicorn
if [ -f antenv/bin/activate ]; then
    source antenv/bin/activate
    echo "[startup] Activated antenv virtualenv"
elif [ -f /opt/defaultenv/bin/activate ]; then
    source /opt/defaultenv/bin/activate
    echo "[startup] Activated defaultenv virtualenv"
else
    echo "[startup] No virtualenv found, using system Python"
fi

# Start gunicorn
exec gunicorn --bind=0.0.0.0:8000 \
         --workers=2 \
         --threads=4 \
         --timeout=120 \
         --access-logfile=- \
         --error-logfile=- \
         --log-level=info \
         app:app
