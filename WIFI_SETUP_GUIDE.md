# WiFi Captive Portal Setup Guide

## Overview

VendoPrint uses a WiFi captive portal to automatically open the printing interface when users connect to the WiFi network. This guide explains how to set up and use this feature.

## How It Works

1. **WiFi Access Point**: The Raspberry Pi creates a WiFi network named "VendoPrint"
2. **Automatic Redirect**: When users connect to this WiFi, their browser automatically opens the VendoPrint interface
3. **No Manual URL Needed**: Users don't need to type any URL - it opens automatically

## Setup Instructions

### Step 1: Run WiFi Setup Script

```bash
sudo ./setup_wifi_portal.sh
```

This script will:
- Install required packages (hostapd, dnsmasq)
- Configure the Raspberry Pi as a WiFi access point
- Set up DHCP and DNS services
- Configure firewall rules for captive portal

### Step 2: Reboot Raspberry Pi

```bash
sudo reboot
```

### Step 3: Start VendoPrint

After reboot, start the VendoPrint application:

```bash
# Option 1: Normal start (port 5000 only)
python3 app.py

# Option 2: With root privileges (enables port 80 redirect)
sudo python3 app.py
```

**Note**: For best captive portal experience, run with `sudo` to enable the HTTP redirect server on port 80.

### Step 4: Verify WiFi Network

Check that the WiFi network is active:

```bash
iwconfig wlan0
```

You should see the "VendoPrint" network is up.

## User Instructions

### For End Users (Students/Customers)

1. **Open WiFi Settings** on your phone/tablet
2. **Connect to WiFi network**: "VendoPrint"
   - No password required
3. **Browser Opens Automatically**: The VendoPrint interface should open automatically
4. **If Browser Doesn't Open**: 
   - Open your browser manually
   - Go to: `http://192.168.4.1` or `http://192.168.4.1:5000`

### Troubleshooting Portal Access

**Problem**: Browser shows "Cannot be found" or "No internet connection"

**Solutions**:
1. Make sure you're connected to the "VendoPrint" WiFi network
2. Try opening: `http://192.168.4.1`
3. Try opening: `http://192.168.4.1:5000`
4. Clear browser cache and try again
5. Try a different browser

**Problem**: Portal doesn't open automatically

**Solutions**:
1. Some devices require manual browser opening
2. Open browser and navigate to `http://192.168.4.1`
3. The portal should load

## Technical Details

### Network Configuration

- **SSID**: VendoPrint
- **IP Address**: 192.168.4.1
- **Port**: 5000 (Flask app), 80 (HTTP redirect)
- **DHCP Range**: 192.168.4.2 - 192.168.4.20

### Captive Portal Detection

The system responds to various captive portal detection methods:
- Android: `/generate_204` endpoint (returns 204 No Content)
- iOS: `/hotspot-detect.html`
- Windows: `/ncsi.txt`
- Chrome: Various connectivity check endpoints

### Port Configuration

- **Port 80**: HTTP redirect server (requires root)
- **Port 5000**: Main Flask application
- **Port 443**: HTTPS redirect (if configured)

The iptables rules redirect all port 80 traffic to port 5000 automatically.

## Manual Testing

### Test Coin Insertion

If coin slot hardware is not connected, you can test payment using the test buttons:
- Click "Test ₱1", "Test ₱5", "Test ₱10", or "Test ₱20" buttons
- These simulate coin insertion for testing purposes

### Test Portal Access

1. Connect to "VendoPrint" WiFi
2. Open browser
3. Try accessing:
   - `http://192.168.4.1`
   - `http://192.168.4.1:5000`
   - `http://localhost` (if on the Pi itself)

## Common Issues

### WiFi Network Not Appearing

**Check**:
```bash
sudo systemctl status hostapd
sudo iwconfig wlan0
```

**Fix**: Restart hostapd service
```bash
sudo systemctl restart hostapd
```

### Portal Shows "Cannot be found"

**Check**:
1. Flask app is running: `ps aux | grep app.py`
2. Port 5000 is listening: `sudo netstat -tlnp | grep 5000`
3. Firewall rules: `sudo iptables -t nat -L`

**Fix**: Restart services
```bash
sudo systemctl restart hostapd
sudo systemctl restart dnsmasq
python3 app.py
```

### Port 80 Permission Denied

**Solution**: Run with sudo or start HTTP redirect server separately:
```bash
sudo python3 http_redirect_server.py
```

## Summary

The WiFi captive portal feature allows users to:
- ✅ Connect to WiFi without typing URLs
- ✅ Automatically open the printing interface
- ✅ Use the system without technical knowledge

The system works best when:
- WiFi setup script has been run
- Services (hostapd, dnsmasq) are running
- Flask app is running on port 5000
- HTTP redirect server is running on port 80 (optional but recommended)
