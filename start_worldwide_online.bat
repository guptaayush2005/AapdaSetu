@echo off
title AapdaSetu - Worldwide Public Access Launcher
cls
echo ====================================================================
echo        AapdaSetu - Worldwide Online Launcher (No Same Wi-Fi Needed)
echo ====================================================================
echo.

cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    set "PYTHON_EXE=.venv\Scripts\python.exe"
) else (
    set "PYTHON_EXE=python"
)

echo [1/2] Starting AapdaSetu Backend on port 8000...
start "AapdaSetu Backend" /min cmd /c "%PYTHON_EXE% -m uvicorn backend.main:app --host 0.0.0.0 --port 8000"

timeout /t 3 /nobreak >nul

echo [2/2] Launching Cloudflare Worldwide Tunnel...
echo.
echo ====================================================================
echo  Look below for your Public Worldwide HTTPS URL (ending in trycloudflare.com):
echo ====================================================================
echo.

.\cloudflared.exe tunnel --url http://127.0.0.1:8000

pause
