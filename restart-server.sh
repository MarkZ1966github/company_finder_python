#!/bin/bash

# Navigate to project directory
cd ~/Documents/company_finder_python

# Create and activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Check port 8000 and kill any process using it
echo "Checking if port 8000 is in use..."
if command -v lsof >/dev/null 2>&1; then
  PORT_PID=$(lsof -ti:8000)
  if [ ! -z "$PORT_PID" ]; then
    echo "Killing process using port 8000: $PORT_PID"
    kill -9 $PORT_PID
    sleep 1
  else
    echo "Port 8000 is available"
  fi
fi

# Install specific versions of dependencies
echo "Installing correct dependencies..."
pip install werkzeug==2.2.3
pip install flask==2.2.3
pip install webdriver-manager==3.8.5

# Start the Flask app
echo "Starting Flask application..."
echo "Access the application at http://localhost:8000 or http://localhost:8080"
python app.py