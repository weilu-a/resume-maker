@echo off
chcp 65001 >nul
cd /d "%~dp0"

set "PY=py -3"
if exist ".venv\Scripts\python.exe" set "PY=.venv\Scripts\python.exe"

echo [1/4] Install build deps...
%PY% -m pip install -r requirements.txt pyinstaller -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn
if errorlevel 1 (
  echo pip failed
  pause
  exit /b 1
)

echo [2/4] PyInstaller onedir build...
%PY% -m PyInstaller --noconfirm --clean resume_studio.spec
if errorlevel 1 (
  echo build failed
  pause
  exit /b 1
)

echo [3/4] Prepare folders...
if not exist "dist\ResumeStudio\data\photos" mkdir "dist\ResumeStudio\data\photos"
if not exist "dist\ResumeStudio\data\uploads" mkdir "dist\ResumeStudio\data\uploads"
if not exist "dist\ResumeStudio\data\interviews" mkdir "dist\ResumeStudio\data\interviews"
if not exist "dist\ResumeStudio\output" mkdir "dist\ResumeStudio\output"

if exist ".env" (
  copy /Y ".env" "dist\ResumeStudio\.env" >nul
) else if exist ".env.example" (
  copy /Y ".env.example" "dist\ResumeStudio\.env.example" >nul
)

echo [4/4] Bundle built-in AI (Ollama CPU + qwen2.5:3b)...
powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\bundle_ai_runtime.ps1"
if errorlevel 1 (
  echo.
  echo WARNING: AI runtime bundle failed. App will still run, but classmates need Ollama or DeepSeek.
  echo You can retry later: powershell -File scripts\bundle_ai_runtime.ps1
)

> "dist\ResumeStudio\使用说明.txt" (
  echo 简历工坊 · 使用说明（完整打包版，含内置 AI^）
  echo.
  echo 【启动】
  echo   双击 ResumeStudio.exe（请保持本文件夹完整^）
  echo.
  echo 【功能】
  echo   生成简历 / 简历优化 / 模拟面试
  echo.
  echo 【AI】
  echo   - 本包若含 runtime 文件夹：首次启动会自动拉起内置模型，无需安装 Ollama
  echo   - 模型较大，首次对话/润色可能需等待十几秒加载
  echo   - 也可在 .env 配置 DEEPSEEK_API_KEY，面试优先走云端
  echo.
  echo 【输出】
  echo   PDF -^> output    面试记录 -^> data\interviews
  echo.
  echo 【系统】Windows 10/11 + WebView2（一般已自带^）
)

echo.
echo Done: dist\ResumeStudio\
echo Share the WHOLE ResumeStudio folder (including runtime\).
echo.
pause
