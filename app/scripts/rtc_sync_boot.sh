#!/bin/bash
#
# RTC Sync Boot Script for Tide Light
#
# Syncs system time from hardware RTC on boot.
# Critical for tide calculations when NTP is unavailable.
#
# This script should run early in the boot process
# before any time-dependent services start.
#

# Exit on error
set -e

# Log file
LOG_FILE="/var/log/tide-light-rtc.log"

# Function to log messages
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Check if RTC hardware exists
if [ ! -e /dev/rtc0 ]; then
    log_message "INFO: No RTC hardware detected (/dev/rtc0 not found)"
    log_message "INFO: System will rely on NTP for time synchronization"
    exit 0
fi

log_message "INFO: RTC hardware detected, syncing system time from RTC..."

# Read current RTC time
RTC_TIME=$(sudo hwclock --show 2>&1) || {
    log_message "ERROR: Failed to read RTC time: $RTC_TIME"
    exit 1
}

log_message "INFO: RTC time: $RTC_TIME"

# Sync RTC to system time
sudo hwclock --hctosys 2>&1 || {
    log_message "ERROR: Failed to sync RTC to system time"
    exit 1
}

# Read new system time
SYSTEM_TIME=$(date '+%Y-%m-%d %H:%M:%S')
log_message "INFO: System time updated to: $SYSTEM_TIME"
log_message "INFO: RTC sync completed successfully"

exit 0
