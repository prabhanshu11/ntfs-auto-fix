#!/bin/bash
set -e

if [ "$EUID" -ne 0 ]; then 
  echo "Please run as root"
  exit 1
fi

SERVICE_NAME="ntfs-auto-fix.service"
INSTALL_DIR="/usr/local/bin"
SCRIPT_NAME="ntfs-auto-fix-monitor"

echo "Stopping and disabling service..."
systemctl stop "$SERVICE_NAME" || true
systemctl disable "$SERVICE_NAME" || true

echo "Removing service file..."
rm -f "/etc/systemd/system/$SERVICE_NAME"
systemctl daemon-reload

echo "Removing script..."
rm -f "$INSTALL_DIR/$SCRIPT_NAME"

echo "Uninstallation complete."
