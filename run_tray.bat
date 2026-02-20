@echo off
REM SVN External Manager - Tray App Launcher (no console window)

REM Check if virtual environment exists
if not exist "venv\" (
    echo Virtual environment not found. Creating...
    python -m venv venv
    echo Virtual environment created.
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Check if dependencies are installed
python -c "import pystray" 2>nul
if errorlevel 1 (
    echo Dependencies not found. Installing...
    pip install -r requirements.txt
    echo Dependencies installed.
)

REM Launch tray app with the venv's pythonw (no console window)
start "" "%~dp0venv\Scripts\pythonw.exe" "%~dp0tray_app.py"
