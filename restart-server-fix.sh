#!/bin/bash

# Kill any existing processes using port 8000
echo "Checking for processes using port 8000..."
if command -v lsof >/dev/null 2>&1; then
    PIDS=$(lsof -ti:8000)
    if [ -n "$PIDS" ]; then
        echo "Found processes using port 8000: $PIDS"
        echo "Killing processes..."
        kill -9 $PIDS
        echo "Processes killed."
    else
        echo "No processes found using port 8000."
    fi
else
    echo "lsof command not found, skipping process check."
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Start the Flask application
echo "Starting Flask application..."
python app.py
