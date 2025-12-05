# VendoPrint - Automated Vending Machine Printer System

An automated printing system for Raspberry Pi 5 that allows students to print documents and photos via Wi-Fi using a coin-based payment system.

## Features

- **Web-based Interface**: Upload and print documents/photos via Wi-Fi
- **Coin Payment System**: Integrated with Allan Universal Coinslot
- **Smart Pricing**: Automatic cost calculation based on pages and color mode
- **Activity Logging**: Complete logging system for all print jobs
- **Owner Dashboard**: Monitor system status, revenue, and logs
- **Error Detection**: Automatic error notifications for paper jams, low ink, etc.
- **Audio Feedback**: Sound cues for coin insertion, printing, completion, and errors

## Hardware Requirements

- Raspberry Pi 5
- SD Card (32GB+ recommended)
- 5V Power source
- Allan Universal Coinslot
- 12V 3AMP DC power supply
- Brother Printer (or compatible CUPS printer)
- Wi-Fi module (built-in on Raspberry Pi)

## Software Requirements

- Raspberry Pi OS (64-bit recommended)
- Python 3.9+
- CUPS (Common Unix Printing System)

## Installation

1. **Clone or download this repository**

2. **Install system dependencies:**
```bash
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv cups cups-client
```

3. **Set up printer in CUPS:**
```bash
sudo lpadmin -p Brother -E -v <printer_uri> -i <driver_path>
```

4. **Create virtual environment:**
```bash
python3 -m venv venv
source venv/bin/activate
```

5. **Install Python dependencies:**
```bash
pip install -r requirements.txt
```

6. **Configure the system:**
Edit `config.json` to match your setup:
- Printer name
- Coin slot GPIO pin
- Pricing
- Notification settings

7. **Set up coin slot callback:**
The payment system needs to be connected to the coin slot callback. Update `app.py` to connect the coin slot callback:
```python
def coin_inserted_callback(coin_value):
    # This will be called when a coin is inserted
    # The frontend polls for payment status
    pass

payment_system.set_coin_callback(coin_inserted_callback)
```

## Running the System

1. **Activate virtual environment:**
```bash
source venv/bin/activate
```

2. **Run the application:**
```bash
python app.py
```

3. **Access the web interface:**
- Connect to the Raspberry Pi's Wi-Fi network
- Open browser and navigate to: `http://raspberrypi.local:5000` or `http://<pi-ip-address>:5000`

## Usage

### For Users

1. Connect your smartphone to the VendoPrint Wi-Fi network
2. Open browser and go to the VendoPrint URL
3. Choose "Print Photo" or "Print Document"
4. Upload your file
5. Configure printing options (copies, range, orientation, color)
6. Insert coins to pay (1 page = 5 pesos for B&W, 10 pesos for color)
7. Click "PRINT" when payment is complete
8. Wait for printing to complete
9. Collect your printed document

### For Owners

1. Access the Owner Dashboard at `/api/dashboard`
2. View statistics (total prints, revenue, success rate)
3. Monitor recent activity logs
4. Check printer status (paper, ink, errors)
5. Review error history

## Project Structure

```
vendoprint/
├── app.py                 # Main Flask application
├── modules/               # Core modules
│   ├── file_processor.py  # File upload and processing
│   ├── payment_system.py  # Coin slot integration
│   ├── printer_manager.py # CUPS printer management
│   ├── logging_system.py  # Activity logging
│   ├── error_handler.py   # Error detection and notifications
│   └── audio_feedback.py  # Audio cues
├── templates/             # HTML templates
│   ├── index.html
│   ├── print_photo.html
│   ├── print_document.html
│   └── dashboard.html
├── static/                # Static files
│   ├── css/              # Stylesheets
│   ├── js/               # JavaScript files
│   └── sounds/           # Audio files (optional)
├── uploads/              # Uploaded files (created automatically)
├── static/previews/      # Preview images (created automatically)
├── logs/                 # Log files (created automatically)
├── config.json           # Configuration file
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## Configuration

Edit `config.json` to customize:

- **PRICE_PER_PAGE_BW**: Price per page for black & white printing (default: 5.0 pesos)
- **PRICE_PER_PAGE_COLOR**: Price per page for color printing (default: 10.0 pesos)
- **PRINTER_NAME**: Name of your printer in CUPS
- **COIN_VALUES**: Accepted coin values in pesos
- **COIN_SLOT_GPIO_PIN**: GPIO pin for coin slot (default: 18)
- **notification_url**: URL for error notifications (optional)
- **owner_phone**: Owner's phone number for SMS notifications (optional)

## Troubleshooting

### Printer not found
- Check printer is connected and powered on
- Verify printer name in CUPS: `lpstat -p`
- Update `PRINTER_NAME` in `config.json`

### Coin slot not working
- Verify GPIO pin connection
- Check coin slot power supply
- Review coin slot documentation for pulse patterns
- Update `_determine_coin_value()` in `payment_system.py` to match your coin slot

### File upload fails
- Check file size (max 50MB)
- Verify file type is supported (PDF, DOC, DOCX, JPG, PNG)
- Check disk space on Raspberry Pi

### Audio not working
- Install audio system: `sudo apt-get install alsa-utils beep`
- Check audio output is configured
- Audio will fail silently if not available (non-critical)

## License

This project is developed for academic/research purposes.

## Support

For issues or questions, please refer to the system documentation or contact the development team.

