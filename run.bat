@echo off
REM SVN External Manager - Startup Script for Windows

echo =======================================================================
echo SVN External Manager - Starting Application
echo =======================================================================

REM Check if virtual environment exists
if not exist "venv\" (
    echo Virtual environment not found. Creating...
    python -m venv venv
    echo Virtual environment created.
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if dependencies are installed
python -c "import flask" 2>nul
if errorlevel 1 (
    echo Dependencies not found. Installing...
    pip install -r requirements.txt
    echo Dependencies installed.
)

REM Check if SVN is available
where svn >nul 2>nul
if errorlevel 1 (
    echo WARNING: SVN command not found!
    echo Please install TortoiseSVN or Subversion command-line tools.
    echo.
)

REM Start the application
echo.
echo Starting Flask server...
echo =======================================================================
python app.py

pause
