#!/bin/bash
#
# Tide Light Application Installation
#
# Installs Python dependencies and configures the application.
# Must be run as root.
#

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_ROOT="$(dirname "$APP_DIR")"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}ERROR: This script must be run as root${NC}"
    echo "Usage: sudo ./install_app.sh"
    exit 1
fi

echo -e "${GREEN}=== Installing Tide Light Application ===${NC}"
echo "Project root: $PROJECT_ROOT"
echo "App directory: $APP_DIR"
echo

# Check if we're in the right place
if [ ! -f "$APP_DIR/main.py" ]; then
    echo -e "${RED}ERROR: main.py not found in $APP_DIR${NC}"
    exit 1
fi

echo -e "${GREEN}[1/2] Installing Python dependencies (as root)...${NC}"
cd "$APP_DIR"

# Install system-wide with sudo (required for root service to find packages)
sudo pip3 install -r requirements.txt

echo "  ✓ Python dependencies installed for root user"

echo
echo -e "${GREEN}[2/2] Installing systemd services...${NC}"

# Install main application service
cp "$SCRIPT_DIR/tide-light.service" /etc/systemd/system/
echo "  ✓ tide-light.service installed"

# Install auto-updater service and timer
cp "$SCRIPT_DIR/tide-light-updater.service" /etc/systemd/system/
cp "$SCRIPT_DIR/tide-light-updater.timer" /etc/systemd/system/
echo "  ✓ tide-light-updater service and timer installed"

# Make auto-update script executable
chmod +x "$SCRIPT_DIR/auto_update.sh"

# Reload systemd
systemctl daemon-reload

echo
echo -e "${GREEN}Enabling services...${NC}"

# Enable but don't start (user may want to configure first)
systemctl enable tide-light.service
echo "  ✓ tide-light service enabled"

systemctl enable tide-light-updater.timer
echo "  ✓ tide-light-updater timer enabled"

echo
echo -e "${GREEN}=== Application Installation Complete ===${NC}"
echo
echo "Installed services:"
echo "  - tide-light.service        (main application, runs as root)"
echo "  - tide-light-updater.timer  (auto-update on boot, runs as root)"
echo
echo "Services are enabled but NOT started yet."
echo
echo "To start services now:"
echo "  systemctl start tide-light"
echo "  systemctl start tide-light-updater.timer"
echo
echo "To view logs:"
echo "  journalctl -u tide-light -f"
echo "  journalctl -u tide-light-updater -f"
echo

exit 0
