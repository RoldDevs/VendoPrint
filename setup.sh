#!/bin/bash
# VendoPrint Setup Script for Raspberry Pi 5

echo "VendoPrint Setup Script"
echo "======================="
echo ""

# Check if running on Raspberry Pi
if [ ! -f /proc/device-tree/model ]; then
    echo "Warning: This script is designed for Raspberry Pi"
fi

# Update system
echo "Updating system packages..."
sudo apt-get update

# Install system dependencies
echo "Installing system dependencies..."
sudo apt-get install -y python3-pip python3-venv cups cups-client python3-dev

# Create virtual environment
echo "Creating Python virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo "Creating directories..."
mkdir -p uploads
mkdir -p static/previews
mkdir -p static/sounds
mkdir -p logs

# Set permissions
echo "Setting permissions..."
chmod +x start.sh
chmod +x setup.sh

echo ""
echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Configure your printer in CUPS:"
echo "   sudo lpadmin -p Brother -E -v <printer_uri>"
echo ""
echo "2. Edit config.json with your settings"
echo ""
echo "3. Run the system:"
echo "   ./start.sh"
echo "   or"
echo "   python3 app.py"
echo ""

