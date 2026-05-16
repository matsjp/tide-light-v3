#!/bin/bash
#
# Tide Light Factory Reset
#
# Resets configuration to defaults using ConfigManager's built-in DEFAULT_CONFIG.
# This mimics the BLE reset characteristic behavior.
#
# The reset is performed by starting Python and calling ConfigManager.reset_to_defaults()
# which uses the hardcoded DEFAULT_CONFIG from config_manager.py
#

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$(dirname "$SCRIPT_DIR")"

echo -e "${YELLOW}=== Tide Light Factory Reset ===${NC}"
echo
echo "This will:"
echo "  - Reset config.json to hardcoded defaults (from ConfigManager)"
echo "  - Clear tide data cache"
echo "  - Restart the tide-light service"
echo
echo "This will NOT:"
echo "  - Uninstall services"
echo "  - Remove log files"
echo "  - Change RTC configuration"
echo
echo -e "${RED}WARNING: Current configuration will be backed up but overwritten!${NC}"
echo

read -p "Continue with factory reset? (y/N): " -n 1 -r
echo

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Factory reset cancelled."
    exit 0
fi

echo
echo -e "${GREEN}[1/4] Backing up current configuration...${NC}"

# Backup config with timestamp
if [ -f "$APP_DIR/config.json" ]; then
    BACKUP_FILE="$APP_DIR/config.json.backup.$(date +%Y%m%d_%H%M%S)"
    cp "$APP_DIR/config.json" "$BACKUP_FILE"
    echo "  ✓ Backed up to: $BACKUP_FILE"
else
    echo "  ℹ No existing config to backup"
fi

echo
echo -e "${GREEN}[2/4] Resetting configuration to defaults...${NC}"

# Use Python to call ConfigManager.reset_to_defaults()
# This ensures we use the exact same logic as BLE reset characteristic
cd "$APP_DIR"
python3 <<'PYTHON_SCRIPT'
import sys
from config_manager import ConfigManager

try:
    config_mgr = ConfigManager("config.json")
    config_mgr.reset_to_defaults()
    print("  ✓ Configuration reset to defaults")
    sys.exit(0)
except Exception as e:
    print(f"  ✗ ERROR: {e}", file=sys.stderr)
    sys.exit(1)
PYTHON_SCRIPT

if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to reset configuration${NC}"
    exit 1
fi

echo
echo -e "${GREEN}[3/4] Clearing tide data cache...${NC}"

if [ -f "$APP_DIR/tide_cache.sqlite" ]; then
    rm "$APP_DIR/tide_cache.sqlite"
    echo "  ✓ Cache cleared"
else
    echo "  ℹ No cache file to clear"
fi

echo
echo -e "${GREEN}[4/4] Restarting service...${NC}"

if systemctl is-active --quiet tide-light; then
    systemctl restart tide-light
    echo "  ✓ Service restarted"
else
    echo -e "  ${YELLOW}⚠ Service not running${NC}"
fi

echo
echo -e "${GREEN}=== Factory Reset Complete ===${NC}"
echo
echo "Configuration reset to defaults (from ConfigManager.DEFAULT_CONFIG):"
echo "  - Location: Per hardcoded defaults in config_manager.py"
echo "  - Settings: Per hardcoded defaults"
echo
echo "You can configure via web interface, BLE, or edit: $APP_DIR/config.json"
echo

exit 0
