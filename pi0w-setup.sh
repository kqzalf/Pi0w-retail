#!/bin/bash

echo "Updating system..."
sudo apt update && sudo apt upgrade -y

echo "Installing Docker..."
curl -sSL https://get.docker.com | sh
sudo usermod -aG docker $USER

echo "Cloning BLE logger repository..."
git clone https://github.com/YOUR_USERNAME/ble-foot-traffic-logger.git
cd ble-foot-traffic-logger

echo "Building Docker image..."
docker compose build

echo "Starting BLE logger container..."
docker compose up -d

echo "Setup complete. Rebooting recommended."
