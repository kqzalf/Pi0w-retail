#!/bin/bash
# Enhanced Pi Provisioning Script for BLE Logger Devices

set -e

echo "[*] Updating system packages..."
sudo apt update && sudo apt upgrade -y

echo "[*] Installing required packages..."
sudo apt install -y python3-pip git iw

echo "[*] Cloning or updating repo..."
cd /home/pi
REPO_DIR="ble-foot-traffic-logger"
REPO_URL="https://github.com/YOUR_ORG/ble-foot-traffic-logger.git"

if [ -d "$REPO_DIR" ]; then
  cd "$REPO_DIR"
  git pull
else
  git clone "$REPO_URL"
  cd "$REPO_DIR"
fi

echo "[*] Installing Python requirements..."
pip3 install -r requirements.txt

echo "[*] Configuring timezone and hostname..."

# Set timezone (default: America/Chicago)
TIMEZONE="${TIMEZONE:-America/Chicago}"
sudo timedatectl set-timezone "$TIMEZONE"

# Set hostname (based on SENSOR_ID env or fallback)
HOSTNAME="${SENSOR_ID:-ble-node}"
sudo hostnamectl set-hostname "$HOSTNAME"
echo "127.0.1.1 $HOSTNAME" | sudo tee -a /etc/hosts

echo "[*] Replacing SENSOR_ID in logger script..."
sed -i "s/^SENSOR_ID = .*/SENSOR_ID = \"$HOSTNAME\"/" ble_wifi_gps_logger_pi.py

echo "[*] Registering systemd service..."
SERVICE_PATH="/etc/systemd/system/ble-logger.service"
sudo cp ble_logger.service "$SERVICE_PATH"
sudo systemctl daemon-reexec
sudo systemctl daemon-reload
sudo systemctl enable ble-logger.service
sudo systemctl restart ble-logger.service

echo "[✔] Provisioning complete."
echo "Hostname: $HOSTNAME"
echo "Timezone: $TIMEZONE"
