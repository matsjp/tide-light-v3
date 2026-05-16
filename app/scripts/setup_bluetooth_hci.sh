#!/bin/bash
#
# Bluetooth HCI Setup for Tide Light
#
# Disables bluetoothd service and configures HCI0 to be brought up on boot.
# This is required for pybleno/bleno to work correctly as a BLE peripheral.
#
# Reference: https://github.com/noble/bleno#prerequisites
#

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}ERROR: This script must be run as root${NC}"
    echo "Usage: sudo ./setup_bluetooth_hci.sh"
    exit 1
fi

echo -e "${GREEN}=== Configuring Bluetooth HCI for BLE Peripheral ===${NC}"
echo

echo -e "${GREEN}[1/3] Stopping bluetoothd service...${NC}"
if systemctl is-active --quiet bluetooth 2>/dev/null; then
    systemctl stop bluetooth
    echo "  ✓ bluetoothd stopped"
else
    echo "  ℹ bluetoothd already stopped"
fi

echo
echo -e "${GREEN}[2/3] Disabling bluetoothd service (persistent)...${NC}"
if systemctl is-enabled --quiet bluetooth 2>/dev/null; then
    systemctl disable bluetooth
    echo "  ✓ bluetoothd disabled"
else
    echo "  ℹ bluetoothd already disabled"
fi

echo
echo -e "${GREEN}[3/3] Creating systemd service to bring up HCI0 on boot...${NC}"

# Create systemd service file
cat > /etc/systemd/system/bluetooth-hci0-up.service <<'EOF'
[Unit]
Description=Bring up Bluetooth HCI0 for BLE Peripheral
After=sys-subsystem-bluetooth-devices-hci0.device
BindsTo=sys-subsystem-bluetooth-devices-hci0.device

[Service]
Type=oneshot
ExecStart=/usr/bin/hciconfig hci0 up
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

echo "  ✓ Service file created: /etc/systemd/system/bluetooth-hci0-up.service"

# Reload systemd and enable service
systemctl daemon-reload
systemctl enable bluetooth-hci0-up.service
echo "  ✓ Service enabled for boot"

# Bring up HCI0 now
echo
echo -e "${GREEN}Bringing up HCI0 now...${NC}"
if hciconfig hci0 up 2>/dev/null; then
    echo "  ✓ HCI0 is up"
    hciconfig hci0 | head -3
else
    echo -e "  ${YELLOW}⚠ Could not bring up HCI0 (may require reboot)${NC}"
fi

echo
echo -e "${GREEN}=== Bluetooth HCI Configuration Complete ===${NC}"
echo
echo "Changes made:"
echo "  - bluetoothd service disabled"
echo "  - bluetooth-hci0-up.service created and enabled"
echo "  - HCI0 will be brought up automatically on boot"
echo
echo -e "${YELLOW}IMPORTANT: These changes take full effect after reboot${NC}"
echo

exit 0
