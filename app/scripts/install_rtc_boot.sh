#!/bin/bash
#
# RTC Boot Sync Installation Script for Tide Light
#
# Installs systemd service to automatically sync system time
# from hardware RTC on every boot.
#
# Usage:
#   sudo ./install_rtc_boot.sh
#

# Exit on error
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}ERROR: This script must be run as root${NC}"
    echo "Usage: sudo ./install_rtc_boot.sh"
    exit 1
fi

echo -e "${GREEN}=== Tide Light RTC Boot Sync Installer ===${NC}"
echo

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RTC_SYNC_SCRIPT="$SCRIPT_DIR/rtc_sync_boot.sh"

# Check if rtc_sync_boot.sh exists
if [ ! -f "$RTC_SYNC_SCRIPT" ]; then
    echo -e "${RED}ERROR: rtc_sync_boot.sh not found at: $RTC_SYNC_SCRIPT${NC}"
    exit 1
fi

echo -e "${GREEN}[1/5] Checking RTC hardware...${NC}"
if [ -e /dev/rtc0 ]; then
    echo "  ✓ RTC hardware detected at /dev/rtc0"
    RTC_TIME=$(hwclock --show 2>&1) || {
        echo -e "${YELLOW}  WARNING: Could not read RTC time${NC}"
    }
    echo "  Current RTC time: $RTC_TIME"
else
    echo -e "${YELLOW}  WARNING: No RTC hardware detected (/dev/rtc0 not found)${NC}"
    echo "  Service will be installed but won't do anything until RTC is connected"
fi

echo
echo -e "${GREEN}[2/5] Making rtc_sync_boot.sh executable...${NC}"
chmod +x "$RTC_SYNC_SCRIPT"
echo "  ✓ Done"

echo
echo -e "${GREEN}[3/5] Creating systemd service file...${NC}"

# Create systemd service
cat > /etc/systemd/system/tide-light-rtc-sync.service <<EOF
[Unit]
Description=Tide Light RTC Time Sync
DefaultDependencies=no
Before=time-sync.target sysinit.target shutdown.target
Conflicts=shutdown.target
After=systemd-remount-fs.service

[Service]
Type=oneshot
ExecStart=$RTC_SYNC_SCRIPT
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=sysinit.target
EOF

echo "  ✓ Service file created at /etc/systemd/system/tide-light-rtc-sync.service"

echo
echo -e "${GREEN}[4/5] Enabling service for boot startup...${NC}"
systemctl daemon-reload
systemctl enable tide-light-rtc-sync.service
echo "  ✓ Service enabled"

echo
echo -e "${GREEN}[5/5] Testing RTC sync (one-time run)...${NC}"
systemctl start tide-light-rtc-sync.service
sleep 1

# Check service status
if systemctl is-active --quiet tide-light-rtc-sync.service; then
    echo -e "  ${YELLOW}Service is still running (check logs)${NC}"
elif systemctl status tide-light-rtc-sync.service | grep -q "Active: inactive (dead)"; then
    echo "  ✓ Service completed"
else
    echo -e "  ${RED}✗ Service failed (check logs)${NC}"
fi

echo
echo -e "${GREEN}=== Installation Complete ===${NC}"
echo
echo "The RTC sync service will now run automatically on every boot."
echo
echo "Useful commands:"
echo "  - View logs:          sudo journalctl -u tide-light-rtc-sync.service"
echo "  - Check status:       sudo systemctl status tide-light-rtc-sync.service"
echo "  - Disable service:    sudo systemctl disable tide-light-rtc-sync.service"
echo "  - Manual RTC sync:    sudo hwclock --hctosys"
echo "  - Write to RTC:       sudo hwclock --systohc"
echo
echo -e "${YELLOW}NOTE: System time will be synced from RTC on next boot${NC}"
echo

exit 0
