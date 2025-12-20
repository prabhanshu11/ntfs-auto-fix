#!/bin/bash
set -e

# NTFS Auto Fix Installer

if [ "$EUID" -ne 0 ]; then 
  echo "Please run as root (sudo ./install.sh)"
  exit 1
fi

# Check for ntfsfix
if ! command -v ntfsfix &> /dev/null; then
    echo "Error: 'ntfsfix' command not found."
    echo "Please install 'ntfs-3g' package (e.g., sudo pacman -S ntfs-3g)"
    exit 1
fi

INSTALL_DIR="/usr/local/bin"
SCRIPT_NAME="ntfs-auto-fix-monitor"
SERVICE_NAME="ntfs-auto-fix.service"

echo "Installing script to $INSTALL_DIR/$SCRIPT_NAME..."
cp main.py "$INSTALL_DIR/$SCRIPT_NAME"
chmod +x "$INSTALL_DIR/$SCRIPT_NAME"

# Create Service
echo "Creating systemd service at /etc/systemd/system/$SERVICE_NAME..."
cat <<EOF > "/etc/systemd/system/$SERVICE_NAME"
[Unit]
Description=NTFS Auto Fix Monitor
After=local-fs.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 $INSTALL_DIR/$SCRIPT_NAME
Restart=always
RestartSec=5
User=root
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

# Reload and Enable
echo "Enabling and starting service..."
systemctl daemon-reload
systemctl enable --now "$SERVICE_NAME"

echo "========================================"
echo "Installation Complete!"
echo "The service is now running in the background."
echo "If an NTFS mount error occurs, it will automatically attempt a fix and notify you."
echo "========================================"
