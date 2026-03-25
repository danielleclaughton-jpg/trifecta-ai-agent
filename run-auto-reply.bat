@echo off
REM Trifecta AI Agent - Auto-Reply Loop Runner
REM Runs the auto-reply cycle every 5 minutes
echo Starting Auto-Reply Loop...

REM Change to project directory
cd /d "%~dp0"

REM Create logs directory if not exists
if not exist ".logs" mkdir .logs

:loop
echo [%date% %time%] Starting auto-reply cycle...
.venv\Scripts\python.exe auto_reply_loop.py >> .logs\auto-reply-loop.log 2>&1
echo [%date% %time%] Cycle complete. Sleeping 5 minutes...
timeout /t 300 /nobreak >nul
goto loop
