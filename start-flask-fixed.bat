@echo off
REM Trifecta AI Agent - Fixed Flask Startup Script
REM Uses .venv Python with all dependencies properly installed
echo Starting Trifecta Flask API...

REM Change to project directory
cd /d "%~dp0"

REM Run Flask using .venv Python
.venv\Scripts\python.exe -c "from app import app; app.run(host='0.0.0.0', port=5000, debug=False)"
