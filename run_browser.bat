@echo off
echo ========================================
echo  NEUROCODE STUDIO (BROWSER MODE)
echo ========================================
echo.

set PYTHON=C:\Users\relig\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe

if not exist "%PYTHON%" (
    set PYTHON=python
)

echo [1/2] Checking dependencies...
"%PYTHON%" -c "import fastapi, uvicorn, edge_tts, soundfile, librosa, pywebview" >nul 2>&1
if %errorlevel% neq 0 (
    echo Dependencies are missing or incomplete. Installing...
    "%PYTHON%" -m pip install -r requirements.txt
    
    echo Verifying installation...
    "%PYTHON%" -c "import fastapi, uvicorn, edge_tts, soundfile, librosa, pywebview" >nul 2>&1
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install dependencies.
        pause
        exit /b 1
    )
) else (
    echo Dependencies are OK.
)
echo.

rem Auto-create shortcut if it doesn't exist on Desktop
if not exist "%USERPROFILE%\Desktop\Neurocode Studio.lnk" (
    echo [2/2] Creating desktop shortcut...
    "%PYTHON%" create_shortcut.py
    echo.
)

echo Starting server in browser mode...
echo.
echo  Open in browser: http://127.0.0.1:7860
echo.
"%PYTHON%" app.py --browser
pause
