#!/bin/bash
cd /home/site/wwwroot

# Ensure persistent data directory exists
mkdir -p /home/data

# Activate Oryx-built virtual environment
# Azure Oryx installs to /antenv (absolute root), not antenv/ (relative)
# Check all known paths in order of priority
if [ -f /antenv/bin/activate ]; then
    source /antenv/bin/activate
    echo "[startup] Activated /antenv virtualenv"
elif [ -f antenv/bin/activate ]; then
    source antenv/bin/activate
    echo "[startup] Activated antenv virtualenv (relative path)"
elif [ -f /opt/defaultenv/bin/activate ]; then
    source /opt/defaultenv/bin/activate
    echo "[startup] Activated defaultenv virtualenv"
else
    echo "[startup] No virtualenv found — checking Python path"
    which python3 || which python
    python3 -c "import flask; print('[startup] Flask OK')" 2>&1 || echo "[startup] WARNING: Flask not found on system Python!"
fi

# Confirm packages are available before starting
python3 -c "import flask, gunicorn; print('[startup] Core packages verified')" 2>&1

# Start gunicorn — single worker to avoid scheduler duplication
# APScheduler starts at module import (production mode), 1 worker = 1 scheduler
exec gunicorn --bind=0.0.0.0:8000 \
         --workers=1 \
         --threads=8 \
         --timeout=120 \
         --preload \
         --access-logfile=- \
         --error-logfile=- \
         --log-level=info \
         app:app
