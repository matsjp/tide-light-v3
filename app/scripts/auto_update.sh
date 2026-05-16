#!/bin/bash
#
# Tide Light Auto-Updater
#
# Pulls latest code from GitHub main branch and restarts service if updated.
# Runs automatically on boot via systemd timer.
#

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
REPO_DIR="/home/pi/tide-light-v3"
BRANCH="main"
SERVICE_NAME="tide-light"

# Logging
log() {
    echo -e "${GREEN}[Auto-Update]${NC} $1"
    logger -t tide-light-updater "$1"
}

log_warn() {
    echo -e "${YELLOW}[Auto-Update]${NC} $1"
    logger -t tide-light-updater "WARNING: $1"
}

log_error() {
    echo -e "${RED}[Auto-Update]${NC} $1"
    logger -t tide-light-updater "ERROR: $1"
}

# Check if we have internet connectivity
# Try multiple methods to ensure we have actual internet, not just network interface up
log "Checking internet connectivity..."

# Method 1: Try to reach Google DNS
if ping -c 1 -W 2 8.8.8.8 &> /dev/null; then
    log "Internet connectivity confirmed (via ping)"
# Method 2: Try to reach Cloudflare DNS  
elif ping -c 1 -W 2 1.1.1.1 &> /dev/null; then
    log "Internet connectivity confirmed (via ping)"
# Method 3: Try to resolve GitHub domain
elif nslookup github.com &> /dev/null; then
    log "Internet connectivity confirmed (via DNS)"
else
    log_warn "No internet connection detected (WiFi/Ethernet may be down)"
    log_warn "Skipping update check - will retry on next boot"
    exit 0
fi

# Navigate to repo
cd "$REPO_DIR" || {
    log_error "Repository directory not found: $REPO_DIR"
    exit 1
}

# Check if git repo
if [ ! -d .git ]; then
    log_error "Not a git repository: $REPO_DIR"
    exit 1
fi

# Store current commit hash
BEFORE=$(git rev-parse HEAD)

# Fetch latest changes
log "Fetching latest changes from origin/$BRANCH..."
if ! git fetch origin "$BRANCH" 2>&1 | logger -t tide-light-updater; then
    log_error "Failed to fetch from remote"
    exit 1
fi

# Check if updates available
if git diff --quiet HEAD "origin/$BRANCH"; then
    log "Already up to date"
    exit 0
fi

# Stash any local changes (e.g., config.json modifications)
log "Stashing local changes..."
git stash push -m "Auto-update stash $(date)" 2>&1 | logger -t tide-light-updater

# Pull latest changes
log "Pulling latest changes..."
if ! git pull origin "$BRANCH" 2>&1 | logger -t tide-light-updater; then
    log_error "Failed to pull from remote"
    git stash pop 2>&1 | logger -t tide-light-updater
    exit 1
fi

# Restore local changes
log "Restoring local changes..."
git stash pop 2>&1 | logger -t tide-light-updater || log_warn "No stashed changes to restore"

# Store new commit hash
AFTER=$(git rev-parse HEAD)

# Install/update Python dependencies if requirements.txt changed
if git diff --name-only "$BEFORE" "$AFTER" | grep -q "app/requirements.txt"; then
    log "requirements.txt changed - updating Python packages..."
    sudo pip3 install --break-system-packages -r app/requirements.txt 2>&1 | logger -t tide-light-updater
fi

# Restart service
log "Code updated from $BEFORE to $AFTER"
log "Restarting $SERVICE_NAME service..."

if systemctl is-active --quiet "$SERVICE_NAME"; then
    systemctl restart "$SERVICE_NAME"
    log "Service restarted successfully"
else
    log_warn "Service not running - not restarting"
fi

log "Auto-update complete"
exit 0
