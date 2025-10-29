#!/bin/bash

###############################################################################
# AI Platform - Systemd Installation Script
# Configures systemd services for automatic startup and management
###############################################################################

set -euo pipefail

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}This script must be run as root${NC}"
   exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="/opt/ai_platform"

echo -e "${GREEN}Installing AI Platform Systemd Services${NC}"
echo "============================================"

# 1. Copy service files
echo -e "\n${YELLOW}Step 1: Installing service files...${NC}"

cp "${SCRIPT_DIR}/ai-platform.service" /etc/systemd/system/
cp "${SCRIPT_DIR}/ai-platform-backup.service" /etc/systemd/system/
cp "${SCRIPT_DIR}/ai-platform-backup.timer" /etc/systemd/system/
cp "${SCRIPT_DIR}/ai-platform-healthcheck.service" /etc/systemd/system/
cp "${SCRIPT_DIR}/ai-platform-healthcheck.timer" /etc/systemd/system/

echo "✓ Service files installed to /etc/systemd/system/"

# 2. Reload systemd
echo -e "\n${YELLOW}Step 2: Reloading systemd daemon...${NC}"
systemctl daemon-reload
echo "✓ Systemd daemon reloaded"

# 3. Enable services
echo -e "\n${YELLOW}Step 3: Enabling services...${NC}"

systemctl enable ai-platform.service
echo "✓ Enabled ai-platform.service"

systemctl enable ai-platform-backup.timer
echo "✓ Enabled ai-platform-backup.timer (daily backups at 2 AM)"

systemctl enable ai-platform-healthcheck.timer
echo "✓ Enabled ai-platform-healthcheck.timer (every 5 minutes)"

# 4. Show status
echo -e "\n${GREEN}Installation Complete!${NC}"
echo "============================================"
echo ""
echo "Available commands:"
echo "  systemctl start ai-platform           # Start the platform"
echo "  systemctl stop ai-platform            # Stop the platform"
echo "  systemctl restart ai-platform         # Restart the platform"
echo "  systemctl status ai-platform          # Check status"
echo "  systemctl enable ai-platform          # Enable auto-start"
echo "  systemctl disable ai-platform         # Disable auto-start"
echo ""
echo "Backup commands:"
echo "  systemctl start ai-platform-backup    # Manual backup"
echo "  systemctl status ai-platform-backup   # Check backup status"
echo ""
echo "Health check commands:"
echo "  systemctl status ai-platform-healthcheck  # Check health status"
echo ""
echo "Logs:"
echo "  journalctl -u ai-platform -f          # View platform logs"
echo "  journalctl -u ai-platform-backup -f   # View backup logs"
echo ""
echo "The platform will now start automatically on boot!"
echo ""
echo -e "${YELLOW}To start the platform now, run:${NC}"
echo "  systemctl start ai-platform"

