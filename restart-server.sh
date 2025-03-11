#!/bin/bash

# Function to check if a process is running on port 8000
check_port() {
    if command -v lsof >/dev/null 2>&1; then
        PIDS=$(lsof -ti:8000)
        if [ -n "$PIDS" ]; then
            echo "Found processes using port 8000: $PIDS"
            return 0
        else
            echo "No processes found using port 8000."
            return 1
        fi
    else
        echo "lsof command not found, skipping process check."
        return 1
    fi
}

# Kill any existing processes using port 8000
echo "Checking for processes using port 8000..."
if check_port; then
    echo "Killing processes..."
    kill -9 $PIDS
    echo "Processes killed."
    
    # Wait a moment to ensure the port is released
    sleep 2
    
    # Check again to make sure the port is free
    if check_port; then
        echo "ERROR: Failed to kill processes using port 8000. Please manually kill them."
        exit 1
    else
        echo "Port 8000 is now free."
    fi
fi

# Activate virtual environment
echo "Activating virtual environment..."
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
fi

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Fix chromedriver issue by updating the requirements.txt
if ! grep -q "chromedriver-binary" requirements.txt; then
    echo "Adding chromedriver-binary to requirements.txt..."
    echo "chromedriver-binary" >> requirements.txt
    pip install chromedriver-binary
fi

# Create a restart script that will handle issues better
cat > restart-server-fix.sh << 'EOF'
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
EOF

chmod +x restart-server-fix.sh

# Start the Flask application
echo "Starting Flask application..."
python app.py