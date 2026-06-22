@echo off
echo ========================================
echo  CREATING DESKTOP SHORTCUT...
echo ========================================
echo.

set PYTHON=C:\Users\relig\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe
if not exist "%PYTHON%" (
    set PYTHON=python
)

"%PYTHON%" create_shortcut.py
pause
