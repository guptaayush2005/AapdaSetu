@echo off
title AapdaSetu - Always-On Backend Daemon
cls
echo ====================================================================
echo             AapdaSetu - 24x7 Always-On Watchdog Service
echo ====================================================================
echo.

cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    set "PYTHON_EXE=.venv\Scripts\python.exe"
) else (
    set "PYTHON_EXE=python"
)

:LOOP
echo [%DATE% %TIME%] Starting AapdaSetu backend on port 8000...
"%PYTHON_EXE%" -m uvicorn backend.main:app --host 127.0.0.1 --port 8000

echo.
echo [WARNING] AapdaSetu backend process terminated. Auto-restarting in 3 seconds...
timeout /t 3 /nobreak >nul
goto LOOP
