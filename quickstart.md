# VendoPrint Quick Start Guide

1. **Run setup script:**
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

2. **Configure printer:**
   ```bash
   sudo lpadmin -p Brother -E -v <your_printer_uri>
   # Or use CUPS web interface: http://localhost:631
   ```

3. **Edit configuration:**
   - Open `config.json`
   - Update printer name, pricing, coin slot GPIO pin

4. **Start the system:**
   ```bash
   ./start.sh
   # Or: python3 app.py
   ```

5. **Access web interface:**
   - Connect to Raspberry Pi's Wi-Fi
   - Open browser: `http://raspberrypi.local:5000`

## Coin Slot Integration

The coin slot is connected via GPIO pin 18 (default). To customize:

1. Edit `config.json`:
   ```json
   {
     "COIN_SLOT_GPIO_PIN": 18
   }
   ```

2. Update `modules/payment_system.py`:
   - Modify `_determine_coin_value()` to match your coin slot's pulse pattern
   - Adjust pulse detection logic based on your coin slot model

## Testing Without Hardware

For development/testing without Raspberry Pi hardware:

1. The system will run but GPIO functions will fail gracefully
2. You can manually trigger payments via the API:
   ```bash
   curl -X POST http://localhost:5000/api/coin-inserted \
     -H "Content-Type: application/json" \
     -d '{"value": 5}'
   ```

## Common Issues

**Printer not found:**
- Check printer is powered and connected
- Verify in CUPS: `lpstat -p`
- Update `PRINTER_NAME` in `config.json`

**Coin slot not working:**
- Check GPIO pin connection
- Verify coin slot power supply
- Review coin slot documentation for pulse patterns

**File upload fails:**
- Check file size (max 50MB)
- Verify file type is supported
- Check disk space

## API Endpoints

- `GET /` - Main menu
- `GET /print-photo` - Print photo interface
- `GET /print-document` - Print document interface
- `POST /api/upload` - Upload file
- `POST /api/calculate-cost` - Calculate printing cost
- `GET /api/payment-status` - Get payment status
- `POST /api/coin-inserted` - Simulate coin insertion
- `POST /api/start-print` - Start printing
- `GET /api/print-status` - Get print job status
- `GET /api/dashboard` - Owner dashboard
- `GET /api/dashboard/stats` - Dashboard statistics
- `GET /api/dashboard/logs` - Activity logs
- `GET /api/printer-status` - Printer status

## File Structure

```
vendoprint/
├── app.py                 # Main application
├── modules/               # Core modules
├── templates/             # HTML templates
├── static/                # CSS, JS, assets
├── uploads/               # Uploaded files
├── logs/                  # Log files
├── config.json            # Configuration
├── requirements.txt       # Dependencies
├── setup.sh              # Setup script
└── start.sh              # Startup script
```

## Support

Refer to README.md for detailed documentation.

