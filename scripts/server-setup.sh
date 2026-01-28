#!/bin/bash
set -e

# Tunisia Price Tracker - Server Setup Script
# Run this on a fresh Ubuntu Lightsail instance
# Usage: curl -sSL <raw-url> | bash

echo "==> Updating system..."
sudo apt-get update
sudo apt-get upgrade -y

echo "==> Installing Docker..."
curl -fsSL https://get.docker.com | sh

echo "==> Adding user to docker group..."
sudo usermod -aG docker ubuntu

echo "==> Installing Docker Compose plugin..."
sudo apt-get install -y docker-compose-plugin

echo "==> Creating app directory..."
sudo mkdir -p /opt/tunisia-price-tracker
sudo chown ubuntu:ubuntu /opt/tunisia-price-tracker

echo "==> Setting up firewall..."
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable

echo "==> Setup complete!"
echo ""
echo "Next steps:"
echo "1. Log out and back in (for docker group to take effect)"
echo "2. From your local machine, run: ./scripts/deploy.sh <this-server-ip>"
echo ""
