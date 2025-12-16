#!/bin/bash
# LinkedBench IoT System Installation Script
# For Raspberry Pi OS (Raspbian)

set -e

echo "================================"
echo "LinkedBench IoT System Installer"
echo "================================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (use sudo)"
    exit 1
fi

# Get the actual user (not root when using sudo)
ACTUAL_USER=${SUDO_USER:-$USER}
ACTUAL_HOME=$(eval echo ~$ACTUAL_USER)

echo "Installing for user: $ACTUAL_USER"
echo ""

# Update system
echo "[1/8] Updating system packages..."
apt-get update

# Install system dependencies
echo "[2/8] Installing system dependencies..."
apt-get install -y python3-pip python3-dev python3-smbus i2c-tools git

# Enable I2C
echo "[3/8] Enabling I2C interface..."
if ! grep -q "^dtparam=i2c_arm=on" /boot/config.txt; then
    echo "dtparam=i2c_arm=on" >> /boot/config.txt
    echo "I2C enabled in /boot/config.txt (reboot required)"
fi

# Load I2C module
modprobe i2c-dev || true

# Add user to i2c group
usermod -a -G i2c $ACTUAL_USER

# Install Python dependencies
echo "[4/8] Installing Python dependencies..."
pip3 install --break-system-packages -r requirements.txt

# Create directories
echo "[5/8] Creating directories..."
mkdir -p /var/lib/linkedbench
mkdir -p /var/log
chown $ACTUAL_USER:$ACTUAL_USER /var/lib/linkedbench

# Create log file
touch /var/log/linkedbench.log
chown $ACTUAL_USER:$ACTUAL_USER /var/log/linkedbench.log

# Copy files to /opt/linkedbench
echo "[6/8] Installing application files..."
INSTALL_DIR="/opt/linkedbench"
mkdir -p $INSTALL_DIR
cp -r ./* $INSTALL_DIR/
chown -R $ACTUAL_USER:$ACTUAL_USER $INSTALL_DIR

# Make scripts executable
chmod +x $INSTALL_DIR/*.py
chmod +x $INSTALL_DIR/install.sh
chmod +x $INSTALL_DIR/run.sh

# Create systemd service
echo "[7/8] Creating systemd service..."
cat > /etc/systemd/system/linkedbench.service << EOF
[Unit]
Description=LinkedBench IoT System
After=network.target

[Service]
Type=simple
User=$ACTUAL_USER
WorkingDirectory=$INSTALL_DIR
ExecStart=/usr/bin/python3 $INSTALL_DIR/linkedbench.py
Restart=always
RestartSec=10
StandardOutput=append:/var/log/linkedbench.log
StandardError=append:/var/log/linkedbench.log

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
systemctl daemon-reload

echo "[8/8] Installation complete!"
echo ""
echo "================================"
echo "Next steps:"
echo "================================"
echo ""
echo "1. Configure the bench ID in config.ini"
echo "2. Test the installation: cd $INSTALL_DIR && python3 linkedbench.py"
echo "3. Enable autostart: sudo systemctl enable linkedbench"
echo "4. Start the service: sudo systemctl start linkedbench"
echo "5. Check status: sudo systemctl status linkedbench"
echo "6. View logs: sudo journalctl -u linkedbench -f"
echo ""
echo "To test I2C devices: i2cdetect -y 1"
echo ""
echo "REST API will be available at: http://$(hostname -I | awk '{print $1}'):5000"
echo ""
echo "NOTE: If I2C was just enabled, you may need to reboot: sudo reboot"
echo ""
