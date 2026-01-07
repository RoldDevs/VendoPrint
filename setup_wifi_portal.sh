#!/bin/bash
# VendoPrint WiFi Captive Portal Setup
# This creates a WiFi hotspot that automatically opens the VendoPrint interface

echo "=========================================="
echo "VendoPrint WiFi Captive Portal Setup"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root: sudo ./setup_wifi_portal.sh"
    exit 1
fi

# Install required packages
echo "Installing required packages..."
apt-get update
apt-get install -y hostapd dnsmasq iptables-persistent

# Stop services
echo "Stopping services..."
systemctl stop hostapd
systemctl stop dnsmasq

# Backup existing configurations
echo "Backing up configurations..."
cp /etc/dhcpcd.conf /etc/dhcpcd.conf.backup 2>/dev/null
cp /etc/dnsmasq.conf /etc/dnsmasq.conf.backup 2>/dev/null
cp /etc/hostapd/hostapd.conf /etc/hostapd/hostapd.conf.backup 2>/dev/null

# Configure static IP for wlan0
echo "Configuring static IP for WiFi interface..."
cat >> /etc/dhcpcd.conf << 'EOF'

# VendoPrint WiFi Configuration
interface wlan0
    static ip_address=192.168.4.1/24
    nohook wpa_supplicant
EOF

# Configure dnsmasq (DHCP and DNS)
echo "Configuring DHCP server..."
cat > /etc/dnsmasq.conf << 'EOF'
# VendoPrint DHCP Configuration
interface=wlan0
dhcp-range=192.168.4.2,192.168.4.20,255.255.255.0,24h
dhcp-option=3,192.168.4.1  # Gateway
dhcp-option=6,192.168.4.1  # DNS Server

# Captive Portal - redirect all DNS queries to this server
address=/#/192.168.4.1

# Log queries
log-queries
log-dhcp
EOF

# Configure hostapd (WiFi Access Point)
echo "Configuring WiFi Access Point..."
cat > /etc/hostapd/hostapd.conf << 'EOF'
# VendoPrint WiFi Access Point Configuration
interface=wlan0
driver=nl80211
ssid=VendoPrint
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=0
EOF

# Tell hostapd where to find the config
echo "Configuring hostapd daemon..."
cat > /etc/default/hostapd << 'EOF'
DAEMON_CONF="/etc/hostapd/hostapd.conf"
EOF

# Enable IP forwarding
echo "Enabling IP forwarding..."
sed -i 's/#net.ipv4.ip_forward=1/net.ipv4.ip_forward=1/' /etc/sysctl.conf
echo 1 > /proc/sys/net/ipv4/ip_forward

# Configure iptables for captive portal
echo "Configuring firewall rules..."
iptables -t nat -F
iptables -F
iptables -t nat -A PREROUTING -i wlan0 -p tcp --dport 80 -j DNAT --to-destination 192.168.4.1:5000
iptables -t nat -A PREROUTING -i wlan0 -p tcp --dport 443 -j DNAT --to-destination 192.168.4.1:5000
iptables -t nat -A POSTROUTING -o wlan0 -j MASQUERADE
iptables -A FORWARD -i wlan0 -o wlan0 -j ACCEPT

# Save iptables rules
echo "Saving firewall rules..."
netfilter-persistent save

# Enable services
echo "Enabling services..."
systemctl unmask hostapd
systemctl enable hostapd
systemctl enable dnsmasq

# Restart services
echo "Restarting services..."
systemctl restart dhcpcd
sleep 2
systemctl start hostapd
systemctl start dnsmasq

# Check status
echo ""
echo "=========================================="
echo "Checking service status..."
echo "=========================================="
echo ""

echo "hostapd status:"
systemctl status hostapd --no-pager | grep Active

echo ""
echo "dnsmasq status:"
systemctl status dnsmasq --no-pager | grep Active

echo ""
echo "=========================================="
echo "WiFi Captive Portal Setup Complete!"
echo "=========================================="
echo ""
echo "WiFi Network Name (SSID): VendoPrint"
echo "No Password Required"
echo "Portal IP: 192.168.4.1:5000"
echo ""
echo "When users connect to 'VendoPrint' WiFi,"
echo "they will automatically be redirected to"
echo "the VendoPrint interface."
echo ""
echo "Next steps:"
echo "1. Reboot your Raspberry Pi: sudo reboot"
echo "2. After reboot, start VendoPrint: python3 app.py"
echo "3. Connect to 'VendoPrint' WiFi from any device"
echo "4. Browser should automatically open to VendoPrint"
echo ""
echo "To check WiFi status: iwconfig wlan0"
echo "To check connected devices: sudo iw dev wlan0 station dump"
echo ""

