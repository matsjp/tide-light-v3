#!/bin/bash
#
# Complete RTC Setup Script for Tide Light
#
# This script performs complete first-time RTC setup:
# 1. Detects Raspberry Pi configuration
# 2. Enables I2C interface
# 3. Configures DS3231 RTC kernel module
# 4. Disables fake-hwclock (conflicts with real RTC)
# 5. Installs boot-time sync service
# 6. Verifies RTC is working
#
# Supports DS3231 RTC module (high accuracy, I2C-based)
#
# Usage:
#   sudo ./setup_rtc_complete.sh
#
# IMPORTANT: This script will reboot the system after configuration!
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
RTC_MODULE="ds3231"
I2C_BUS=1  # Usually 1 on modern Pi boards

# Function to print colored headers
print_header() {
    echo
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  $1${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    echo
}

# Function to print step header
print_step() {
    echo
    echo -e "${GREEN}[$1] $2${NC}"
}

# Function to print info
print_info() {
    echo -e "  ${BLUE}ℹ${NC} $1"
}

# Function to print success
print_success() {
    echo -e "  ${GREEN}✓${NC} $1"
}

# Function to print warning
print_warning() {
    echo -e "  ${YELLOW}⚠${NC} $1"
}

# Function to print error
print_error() {
    echo -e "  ${RED}✗${NC} $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}ERROR: This script must be run as root${NC}"
    echo "Usage: sudo ./setup_rtc_complete.sh"
    exit 1
fi

print_header "Tide Light - Complete RTC Setup"

print_info "This script will configure a DS3231 Real-Time Clock module"
print_info "for automatic time synchronization when offline."
print_warning "IMPORTANT: The system will reboot after setup!"
echo

read -p "Continue with RTC setup? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Setup cancelled."
    exit 0
fi

# ============================================================================
# STEP 1: Detect Raspberry Pi and locate boot config
# ============================================================================

print_step "1/8" "Detecting Raspberry Pi configuration"

# Detect Pi model
PI_MODEL=$(cat /proc/device-tree/model 2>/dev/null || echo "Unknown")
print_info "Raspberry Pi model: $PI_MODEL"

# Detect boot config location (varies by Raspberry Pi OS version)
if [ -f /boot/firmware/config.txt ]; then
    BOOT_CONFIG="/boot/firmware/config.txt"
elif [ -f /boot/config.txt ]; then
    BOOT_CONFIG="/boot/config.txt"
else
    print_error "Could not locate boot config file"
    print_info "Expected: /boot/config.txt or /boot/firmware/config.txt"
    exit 1
fi

print_success "Boot config located: $BOOT_CONFIG"

# ============================================================================
# STEP 2: Enable I2C interface
# ============================================================================

print_step "2/8" "Enabling I2C interface"

# Check if I2C already enabled
if grep -q "^dtparam=i2c_arm=on" "$BOOT_CONFIG"; then
    print_success "I2C already enabled in $BOOT_CONFIG"
else
    print_info "Enabling I2C in $BOOT_CONFIG..."
    
    # Add I2C enable parameter
    if grep -q "^#dtparam=i2c_arm=" "$BOOT_CONFIG"; then
        # Uncomment existing line
        sed -i 's/^#dtparam=i2c_arm=.*/dtparam=i2c_arm=on/' "$BOOT_CONFIG"
    else
        # Add new line
        echo "dtparam=i2c_arm=on" >> "$BOOT_CONFIG"
    fi
    
    print_success "I2C enabled in boot config"
fi

# Load I2C kernel module (for immediate use without reboot)
if lsmod | grep -q i2c_bcm2835; then
    print_success "I2C kernel module already loaded"
else
    print_info "Loading I2C kernel module..."
    modprobe i2c-dev 2>/dev/null || true
    modprobe i2c-bcm2835 2>/dev/null || true
    print_success "I2C kernel module loaded"
fi

# ============================================================================
# STEP 3: Configure RTC kernel module (DS3231)
# ============================================================================

print_step "3/8" "Configuring DS3231 RTC kernel module"

RTC_OVERLAY="dtoverlay=i2c-rtc,$RTC_MODULE"

if grep -q "^$RTC_OVERLAY" "$BOOT_CONFIG"; then
    print_success "RTC overlay already configured: $RTC_OVERLAY"
else
    print_info "Adding RTC overlay to $BOOT_CONFIG..."
    
    # Remove old RTC overlays if present
    sed -i '/^dtoverlay=i2c-rtc,/d' "$BOOT_CONFIG"
    
    # Add new overlay
    echo "$RTC_OVERLAY" >> "$BOOT_CONFIG"
    
    print_success "RTC overlay added: $RTC_OVERLAY"
fi

# ============================================================================
# STEP 4: Disable fake-hwclock (conflicts with real RTC)
# ============================================================================

print_step "4/8" "Disabling fake-hwclock service"

if systemctl is-active --quiet fake-hwclock 2>/dev/null; then
    print_info "Stopping and disabling fake-hwclock..."
    systemctl stop fake-hwclock 2>/dev/null || true
    systemctl disable fake-hwclock 2>/dev/null || true
    print_success "fake-hwclock disabled"
else
    print_success "fake-hwclock already disabled or not present"
fi

# Remove fake-hwclock from init if present
if [ -f /etc/init.d/fake-hwclock ]; then
    print_info "Removing fake-hwclock init script..."
    update-rc.d fake-hwclock remove 2>/dev/null || true
    print_success "fake-hwclock init script removed"
fi

# ============================================================================
# STEP 5: Install required packages
# ============================================================================

print_step "5/8" "Installing required packages"

print_info "Updating package list..."
apt-get update -qq

PACKAGES="i2c-tools"

print_info "Installing: $PACKAGES"
apt-get install -y -qq $PACKAGES > /dev/null 2>&1

print_success "Required packages installed"

# ============================================================================
# STEP 6: Set up RTC boot sync service
# ============================================================================

print_step "6/8" "Setting up RTC boot sync service"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RTC_SYNC_SCRIPT="$SCRIPT_DIR/rtc_sync_boot.sh"

# Check if rtc_sync_boot.sh exists
if [ ! -f "$RTC_SYNC_SCRIPT" ]; then
    print_error "rtc_sync_boot.sh not found at: $RTC_SYNC_SCRIPT"
    print_info "Please ensure rtc_sync_boot.sh is in the same directory as this script"
    exit 1
fi

# Make executable
chmod +x "$RTC_SYNC_SCRIPT"
print_success "rtc_sync_boot.sh is executable"

# Create systemd service
SERVICE_FILE="/etc/systemd/system/tide-light-rtc-sync.service"

cat > "$SERVICE_FILE" <<EOF
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

print_success "Service file created: $SERVICE_FILE"

# Enable service
systemctl daemon-reload
systemctl enable tide-light-rtc-sync.service 2>/dev/null

print_success "RTC sync service enabled for boot"

# ============================================================================
# STEP 7: Create verification/helper script
# ============================================================================

print_step "7/8" "Creating RTC helper script"

HELPER_SCRIPT="/usr/local/bin/tide-rtc"

cat > "$HELPER_SCRIPT" <<'EOF'
#!/bin/bash
# Tide Light RTC Helper Script

case "$1" in
    status)
        echo "=== RTC Status ==="
        echo "RTC Device: $(ls -l /dev/rtc* 2>/dev/null || echo 'Not found')"
        echo
        echo "RTC Time:"
        sudo hwclock --show 2>/dev/null || echo "  Error reading RTC"
        echo
        echo "System Time:"
        date
        echo
        echo "I2C Devices:"
        sudo i2cdetect -y 1 2>/dev/null || echo "  Error: I2C not available"
        ;;
    
    sync-from-rtc)
        echo "Syncing system time FROM RTC..."
        sudo hwclock --hctosys
        echo "Done. System time: $(date)"
        ;;
    
    sync-to-rtc)
        echo "Syncing system time TO RTC..."
        sudo hwclock --systohc
        echo "Done. RTC time: $(sudo hwclock --show)"
        ;;
    
    logs)
        echo "=== RTC Boot Sync Logs ==="
        sudo journalctl -u tide-light-rtc-sync.service -n 50
        ;;
    
    *)
        echo "Tide Light RTC Helper"
        echo
        echo "Usage: tide-rtc [command]"
        echo
        echo "Commands:"
        echo "  status          - Show RTC status and current times"
        echo "  sync-from-rtc   - Sync system time FROM RTC hardware"
        echo "  sync-to-rtc     - Sync system time TO RTC hardware"
        echo "  logs            - View RTC sync service logs"
        echo
        exit 1
        ;;
esac
EOF

chmod +x "$HELPER_SCRIPT"
print_success "Helper script created: $HELPER_SCRIPT"
print_info "You can use 'tide-rtc status' to check RTC at any time"

# ============================================================================
# STEP 8: Summary and reboot prompt
# ============================================================================

print_step "8/8" "Setup complete!"

print_header "Setup Summary"

print_success "I2C interface enabled"
print_success "DS3231 RTC module configured"
print_success "fake-hwclock disabled"
print_success "Boot sync service installed"
print_success "Helper script created: tide-rtc"

echo
print_warning "IMPORTANT: System must reboot for RTC hardware to be detected"
echo

print_header "Next Steps"

print_info "1. Connect your DS3231 RTC module to the Raspberry Pi:"
echo "     VCC  → Pin 1  (3.3V)"
echo "     GND  → Pin 6  (Ground)"
echo "     SDA  → Pin 3  (GPIO 2 / I2C SDA)"
echo "     SCL  → Pin 5  (GPIO 3 / I2C SCL)"
echo

print_info "2. After reboot, verify RTC is detected:"
echo "     sudo tide-rtc status"
echo

print_info "3. Set correct time via web interface or command:"
echo "     Web: Connect via BLE and click 'Sync Device to Browser Time'"
echo "     CLI: sudo hwclock --systohc"
echo

print_info "4. Useful commands:"
echo "     tide-rtc status         - Check RTC status"
echo "     tide-rtc sync-to-rtc    - Write system time to RTC"
echo "     tide-rtc sync-from-rtc  - Read RTC time to system"
echo "     tide-rtc logs           - View sync service logs"
echo

echo
read -p "Reboot now? (Y/n): " -n 1 -r
echo

if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    print_info "Rebooting in 5 seconds... (Ctrl+C to cancel)"
    sleep 5
    print_success "Rebooting..."
    reboot
else
    print_warning "Please reboot manually to complete RTC setup:"
    echo "  sudo reboot"
    echo
fi

exit 0
