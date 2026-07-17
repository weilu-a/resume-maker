@echo off
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" app\main.py
) else (
    echo venv not found. Run: python -m venv .venv
    pause
    exit /b 1
)
if errorlevel 1 pause
