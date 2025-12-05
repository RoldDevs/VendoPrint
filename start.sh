#!/bin/bash
# VendoPrint Startup Script

echo "Starting VendoPrint System."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run the application
python3 app.py

