@echo off
cd /d "%~dp0"
echo ========================================
echo   Resume Studio - AI (Ollama) Setup
echo ========================================
echo.

where ollama >nul 2>&1
if errorlevel 1 (
    echo [1/3] Ollama not found. Trying winget install...
    winget install --id Ollama.Ollama -e --accept-source-agreements --accept-package-agreements
    if errorlevel 1 (
        echo.
        echo Install failed. Please download from https://ollama.com/download
        echo Then re-run this script.
        pause
        exit /b 1
    )
    echo Please close this window, start Ollama from Start Menu, then run setup_ai.bat again.
    pause
    exit /b 0
)

echo [1/3] Ollama found.
echo [2/3] Pulling model qwen2.5:3b (may take several minutes)...
ollama pull qwen2.5:3b
if errorlevel 1 (
    echo Pull failed. Check network and retry: ollama pull qwen2.5:3b
    pause
    exit /b 1
)

echo [3/3] Checking API...
curl -s http://127.0.0.1:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo Ollama API not responding. Start the Ollama app, then retry.
    pause
    exit /b 1
)

echo.
echo AI setup OK. Start the app with run.bat
echo Homepage badge should show: Ollama ready
pause
