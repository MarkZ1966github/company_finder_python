#!/bin/bash

# Check if server is already running on port 8000
if lsof -i:8000 > /dev/null; then
    echo "Port 8000 is already in use. Stopping existing process..."
    # Get the PID of the process using port 8000
    PID=$(lsof -t -i:8000)
    if [ -n "$PID" ]; then
        echo "Killing process $PID using port 8000..."
        kill -9 $PID
        sleep 1
    fi
fi

# Navigate to project directory
cd ~/Documents/company_finder_python

# Create and activate virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

# Install requirements
echo "Installing dependencies..."
pip install -r requirements.txt

# Clear any existing sessions
echo "Clearing Chrome sessions..."
rm -rf ~/.config/chromium/Default/Session* 2>/dev/null
rm -rf ~/.config/google-chrome/Default/Session* 2>/dev/null
rm -rf ~/Library/Application\ Support/Google/Chrome/Default/Session* 2>/dev/null

# Start the Flask app
echo "Starting Flask application..."
python3 app.py