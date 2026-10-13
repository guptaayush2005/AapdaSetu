@echo off
title AapdaSetu - AI Disaster Response Platform
cls
echo ====================================================================
echo                AapdaSetu - Starting Platform
echo ====================================================================
echo.

cd /d "%~dp0"

echo [1/2] Checking Python Virtual Environment...
if exist ".venv\Scripts\python.exe" (
    set "PYTHON_EXE=.venv\Scripts\python.exe"
) else (
    set "PYTHON_EXE=python"
)

echo [2/2] Launching Backend and Frontend Dashboard...
start "" http://127.0.0.1:8000/frontend/index.html
"%PYTHON_EXE%" "backend\main.py"

pause
