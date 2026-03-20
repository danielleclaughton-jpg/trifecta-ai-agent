@echo off
setlocal

set "OPENCLAW_ROOT=C:\Users\TrifectaAgent\.openclaw\workspaceopenclaw gateway"
set "TRIFECTA_ROOT=C:\Users\TrifectaAgent\trifecta-ai-agent"
set "API_HEALTH_URL=http://localhost:5000/health"
set "DASHBOARD_URL=http://localhost:8080/dashboard/leads.html"

if not exist "%TRIFECTA_ROOT%\.logs" mkdir "%TRIFECTA_ROOT%\.logs"

echo.
echo Starting Trifecta live leads stack...
echo.

powershell -NoProfile -Command "try { $r = Invoke-WebRequest -UseBasicParsing '%API_HEALTH_URL%' -TimeoutSec 3; if ($r.StatusCode -eq 200) { exit 0 } else { exit 1 } } catch { exit 1 }"
if errorlevel 1 (
    echo [1/3] Flask API is down. Starting on http://localhost:5000 ...
    if exist "%TRIFECTA_ROOT%\.venv\Scripts\python.exe" (
        set "PYTHON_EXE=%TRIFECTA_ROOT%\.venv\Scripts\python.exe"
    ) else (
        set "PYTHON_EXE=python"
    )
    start "Trifecta Flask API" /min cmd /c "cd /d "%TRIFECTA_ROOT%" && set FLASK_DEBUG=0 && ""%PYTHON_EXE%"" app.py > "%TRIFECTA_ROOT%\.logs\app-out.log" 2>&1"
    timeout /t 8 /nobreak >nul
) else (
    echo [1/3] Flask API already healthy.
)

powershell -NoProfile -Command "try { $r = Invoke-WebRequest -UseBasicParsing '%DASHBOARD_URL%' -TimeoutSec 3; if ($r.StatusCode -eq 200) { exit 0 } else { exit 1 } } catch { exit 1 }"
if errorlevel 1 (
    echo [2/3] Dashboard server is down. Starting on http://localhost:8080 ...
    start "OpenClaw Dashboard Server" /min cmd /c "cd /d "%OPENCLAW_ROOT%" && python -m http.server 8080"
    timeout /t 4 /nobreak >nul
) else (
    echo [2/3] Dashboard server already healthy.
)

echo [3/3] Opening live leads page...
start "" explorer.exe "%DASHBOARD_URL%"

echo.
echo Live leads page: %DASHBOARD_URL%
echo Flask health:    %API_HEALTH_URL%
echo.

endlocal
