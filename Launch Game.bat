@echo off
setlocal

cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    set "PYTHON_EXE=.venv\Scripts\python.exe"
) else (
    set "PYTHON_EXE=python"
)

"%PYTHON_EXE%" -m game.main
if errorlevel 1 (
    echo.
    echo Game failed to launch. Make sure dependencies are installed:
    echo python -m pip install -r requirements.txt
    echo.
    pause
)
