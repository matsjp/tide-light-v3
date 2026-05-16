#!/bin/bash
#
# Tide Light - Complete Fresh Pi Installation
#
# Master script that orchestrates full installation:
# 1. System dependencies
# 2. Bluetooth HCI configuration
# 3. RTC hardware setup (optional)
# 4. Application installation
#

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Print header
print_header() {
    echo
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  $1${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    echo
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}ERROR: This script must be run as root${NC}"
    echo "Usage: sudo ./install_complete.sh"
    exit 1
fi

print_header "Tide Light v3 - Complete Installation"

echo "This script will install and configure:"
echo "  1. System dependencies (Bluetooth, Python, build tools)"
echo "  2. Bluetooth HCI configuration (disable bluetoothd, enable hci0)"
echo "  3. RTC hardware (DS3231, I2C, boot sync) - optional"
echo "  4. Tide Light application (Python deps, systemd services)"
echo
echo "Installation path: $(dirname "$SCRIPT_DIR")"
echo
echo "All services will run as root (no permission issues)."
echo
echo -e "${YELLOW}The system will need to REBOOT after installation.${NC}"
echo

read -p "Continue with installation? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Installation cancelled."
    exit 0
fi

# STEP 1: System Dependencies
print_header "Step 1/4: Installing System Dependencies"
"$SCRIPT_DIR/install_system_dependencies.sh"

# STEP 2: Bluetooth HCI Configuration
print_header "Step 2/4: Configuring Bluetooth HCI"
"$SCRIPT_DIR/setup_bluetooth_hci.sh"

# STEP 3: RTC Setup (Optional)
print_header "Step 3/4: Setting Up RTC Hardware"
echo "Do you have a DS3231 RTC module connected to the Pi?"
echo "(This provides accurate time when offline)"
echo
read -p "Install RTC support? (Y/n): " -n 1 -r
echo

if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    "$SCRIPT_DIR/setup_rtc_complete.sh" --no-reboot
else
    echo "Skipping RTC setup"
fi

# STEP 4: Application Installation
print_header "Step 4/4: Installing Tide Light Application"
"$SCRIPT_DIR/install_app.sh"

# Final Summary
print_header "Installation Complete!"

echo -e "${GREEN}✓ System dependencies installed${NC}"
echo -e "${GREEN}✓ Bluetooth HCI configured (bluetoothd disabled)${NC}"
echo -e "${GREEN}✓ RTC hardware configured (if selected)${NC}"
echo -e "${GREEN}✓ Application installed and services enabled${NC}"
echo
echo -e "${YELLOW}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}  IMPORTANT: System must reboot for all changes to take effect${NC}"
echo -e "${YELLOW}═══════════════════════════════════════════════════════════════${NC}"
echo
echo "After reboot, the Tide Light will:"
echo "  1. Bring up Bluetooth HCI0 (for BLE peripheral)"
echo "  2. Check for updates from GitHub (2 minutes after boot)"
echo "  3. Start automatically and advertise via Bluetooth"
echo
echo "⚠️  You MUST configure the location via BLE or web interface after installation"
echo "   (temporary default location is set, but you should change it)"
echo
echo "Useful commands:"
echo "  - View logs:           journalctl -u tide-light -f"
echo "  - Restart service:     systemctl restart tide-light"
echo "  - Check status:        systemctl status tide-light"
echo "  - Stop auto-updates:   systemctl disable tide-light-updater.timer"
echo "  - Check RTC time:      tide-rtc status"
echo "  - Factory reset:       $SCRIPT_DIR/factory_reset.sh"
echo
echo "Configuration file:  /home/pi/tide-light-v3/app/config.json"
echo "Default BLE name:    Tide Light"
echo
echo

read -p "Reboot now? (Y/n): " -n 1 -r
echo

if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    echo "Rebooting in 5 seconds... (Ctrl+C to cancel)"
    sleep 5
    reboot
else
    echo -e "${YELLOW}Please reboot manually to complete installation:${NC}"
    echo "  sudo reboot"
    echo
fi

exit 0
