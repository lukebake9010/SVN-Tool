#!/bin/bash
# SVN External Manager - Startup Script

echo "======================================================================="
echo "SVN External Manager - Starting Application"
echo "======================================================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating..."
    python3 -m venv venv
    echo "Virtual environment created."
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Check if dependencies are installed
if ! python -c "import flask" 2>/dev/null; then
    echo "Dependencies not found. Installing..."
    pip install -r requirements.txt
    echo "Dependencies installed."
fi

# Check if SVN is available
if ! command -v svn &> /dev/null; then
    echo "WARNING: SVN command not found!"
    echo "Please install Subversion (SVN) to use this application."
    echo ""
fi

# Start the application
echo ""
echo "Starting Flask server..."
echo "======================================================================="
python app.py
