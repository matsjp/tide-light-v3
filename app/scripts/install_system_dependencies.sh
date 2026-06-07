#!/bin/bash
#
# System Dependencies Installation for Tide Light
#
# Installs all required system packages for Bluetooth, GPIO, I2C, and Python development.
#

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}ERROR: This script must be run as root${NC}"
    echo "Usage: sudo ./install_system_dependencies.sh"
    exit 1
fi

echo -e "${GREEN}=== Installing System Dependencies ===${NC}"
echo

echo -e "${GREEN}[1/5] Updating package lists...${NC}"
apt-get update -qq

echo -e "${GREEN}[2/5] Installing Bluetooth packages...${NC}"
apt-get install -y -qq \
    bluetooth \
    bluez \
    libbluetooth-dev \
    bluez-tools

echo "  ✓ Bluetooth packages installed"

echo
echo -e "${GREEN}[3/5] Installing Python development packages...${NC}"
apt-get install -y -qq \
    python3 \
    python3-pip \
    python3-dev \
    python3-setuptools \
    python3-dbus \
    libglib2.0-dev

echo "  ✓ Python packages installed"

echo
echo -e "${GREEN}[4/5] Installing build tools and utilities...${NC}"
apt-get install -y -qq \
    git \
    gcc \
    make \
    build-essential \
    i2c-tools \
    util-linux-extra

echo "  ✓ Build tools installed"

echo
echo -e "${GREEN}[5/5] Configuring network-online.target...${NC}"

# Enable systemd-networkd-wait-online to ensure network-online.target
# actually waits for internet connectivity (not just interface up)
if systemctl list-unit-files | grep -q systemd-networkd-wait-online.service; then
    systemctl enable systemd-networkd-wait-online.service 2>/dev/null || true
    echo "  ✓ systemd-networkd-wait-online enabled"
else
    echo "  ℹ systemd-networkd-wait-online not available (using default network manager)"
fi

echo
echo -e "${GREEN}=== System Dependencies Installed ===${NC}"
echo
echo "Installed packages:"
echo "  - Bluetooth: bluetooth, bluez, libbluetooth-dev"
echo "  - Python: python3, python3-pip, python3-dev, python3-dbus"
echo "  - Build tools: git, gcc, make, build-essential"
echo "  - Hardware: i2c-tools, util-linux-extra (hwclock)"
echo "  - Network: systemd-networkd-wait-online (for proper network-online.target)"
echo

exit 0
