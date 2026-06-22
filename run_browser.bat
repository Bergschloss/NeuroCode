@echo off
echo ========================================
echo  NEUROCODE STUDIO (BROWSER MODE)
echo ========================================
echo.

set PYTHON=C:\Users\relig\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe

rem Auto-create shortcut if it doesn't exist on Desktop
if not exist "%USERPROFILE%\Desktop\Neurocode Studio.lnk" (
    echo [0/1] Creating desktop shortcut...
    "%PYTHON%" create_shortcut.py
    echo.
)

echo [1/1] Starting server in browser mode...
echo.
echo.
echo.
echo  Open in browser: http://127.0.0.1:7860
echo.
"%PYTHON%" app.py --browser
pause
