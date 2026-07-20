@echo off
setlocal enabledelayedexpansion
title Neurocode Studio

set PYTHON=C:\Users\relig\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe

if not exist "%PYTHON%" (
    set PYTHON=python
)

if not exist ".deps_ok" (
    echo [1/2] Checking dependencies...
    "%PYTHON%" -c "import fastapi, uvicorn, edge_tts, soundfile, webview" >nul 2>&1
    if !errorlevel! neq 0 (
        echo Dependencies are missing or incomplete. Installing...
        "%PYTHON%" -m pip install -r requirements.txt
    )
    echo ok > ".deps_ok"
)

if not exist "%USERPROFILE%\Desktop\Neurocode Studio.lnk" (
    "%PYTHON%" create_shortcut.py >nul 2>&1
)

"%PYTHON%" app.py
