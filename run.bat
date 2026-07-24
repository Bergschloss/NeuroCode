@echo off
setlocal enabledelayedexpansion
title Neurocode Studio

set PYTHON=C:\Users\relig\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe

if not exist "%PYTHON%" (
    set PYTHON=python
)

"%PYTHON%" -c "import fastapi, uvicorn, edge_tts, soundfile, webview" >nul 2>&1
if !errorlevel! neq 0 (
    echo [1/2] Installing required packages...
    "%PYTHON%" -m pip install -r requirements.txt
)

if not exist "%USERPROFILE%\Desktop\Neurocode Studio.lnk" (
    echo [2/2] Creating desktop shortcut...
    "%PYTHON%" create_shortcut.py >nul 2>&1
)

echo Starting Neurocode Studio...
"%PYTHON%" app.py

if !errorlevel! neq 0 (
    echo.
    echo [ERROR] App exited with error code !errorlevel!
    pause
)
