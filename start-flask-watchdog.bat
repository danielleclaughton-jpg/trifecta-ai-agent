@echo off
title Trifecta Flask API (Auto-Restart)

echo Checking port 5000...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5000') do taskkill /F /PID %%a 2>nul

:loop
echo [%date% %time%] Starting Flask API...
cd /d C:\Users\TrifectaAgent\trifecta-ai-agent
python app.py
echo [%date% %time%] Flask crashed or stopped. Restarting in 5 seconds...
timeout /t 5 /nobreak
goto loop
