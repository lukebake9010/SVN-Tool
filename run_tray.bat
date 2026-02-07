@echo off
REM SVN External Manager - Tray Application Launcher
REM Runs the server as a system tray icon instead of a console window.

REM Check if virtual environment exists
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
    echo Virtual environment created.
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Check if dependencies are installed (Flask + tray deps)
python -c "import flask" 2>nul
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
    echo Dependencies installed.
)

python -c "import pystray" 2>nul
if errorlevel 1 (
    echo Installing tray app dependencies...
    pip install pystray Pillow
    echo Tray dependencies installed.
)

REM Check if SVN is available
where svn >nul 2>nul
if errorlevel 1 (
    echo WARNING: SVN command not found!
    echo Please install TortoiseSVN or Subversion command-line tools.
    echo.
)

REM Launch the tray app.
REM Using "python" (not "pythonw") so a console window exists for the
REM Show/Hide Console toggle.  The tray app hides it immediately on startup.
python tray_app.py
