#!/bin/bash
# VendoPrint Startup Script

echo "=========================================="
echo "Starting VendoPrint System"
echo "=========================================="

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d "env" ]; then
    source env/bin/activate
fi

# Check if running as root (for port 80)
if [ "$EUID" -eq 0 ]; then
    echo "Running as root - HTTP redirect server will start automatically"
else
    echo "Note: For full WiFi portal functionality, run with sudo to enable port 80 redirect"
    echo "Or run 'sudo python3 http_redirect_server.py' in a separate terminal"
fi

# Run the application
echo "Starting Flask application on port 5000..."
python3 app.py

