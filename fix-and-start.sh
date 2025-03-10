#!/bin/bash
# Navigate to project directory
cd ~/Documents/company_finder_python

# Create and activate virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

# Uninstall problematic package first
echo "Removing incompatible Werkzeug version..."
pip uninstall -y werkzeug

# Install requirements
echo "Installing dependencies..."
pip install -r requirements.txt

# Start the Flask app
echo "Starting Flask application..."
python3 app.py