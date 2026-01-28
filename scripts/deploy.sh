#!/bin/bash
set -e

# Tunisia Price Tracker - Deployment Script
# Usage: ./scripts/deploy.sh [server-ip]

SERVER_IP=${1:-$DEPLOY_SERVER_IP}
SSH_KEY=${2:-${SSH_KEY:-~/.ssh/LightsailKey.pem}}
REMOTE_DIR="/opt/tunisia-price-tracker"

if [ -z "$SERVER_IP" ]; then
    echo "Usage: ./scripts/deploy.sh <server-ip> [ssh-key-path]"
    echo ""
    echo "Examples:"
    echo "  ./scripts/deploy.sh 1.2.3.4 ~/.ssh/LightsailKey.pem"
    echo "  ./scripts/deploy.sh 1.2.3.4 ~/.ssh/id_rsa"
    echo "  SSH_KEY=~/.ssh/mykey.pem ./scripts/deploy.sh 1.2.3.4"
    exit 1
fi

if [ ! -f "$SSH_KEY" ]; then
    echo "Error: SSH key not found at $SSH_KEY"
    echo "Specify the key path: ./scripts/deploy.sh <ip> <path-to-key>"
    exit 1
fi

echo "==> Deploying to $SERVER_IP"

# Create deployment package (exclude unnecessary files)
echo "==> Creating deployment package..."
tar --exclude='node_modules' \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='.venv' \
    --exclude='*.pyc' \
    --exclude='.env' \
    --exclude='admin/dist' \
    -czf /tmp/deploy.tar.gz -C "$(dirname "$0")/.." .

# Copy to server
echo "==> Copying files to server..."
scp -i "$SSH_KEY" /tmp/deploy.tar.gz "ubuntu@$SERVER_IP:/tmp/"

# Deploy on server
echo "==> Deploying on server..."
ssh -i "$SSH_KEY" "ubuntu@$SERVER_IP" << 'ENDSSH'
set -e

# Create directory if not exists
sudo mkdir -p /opt/tunisia-price-tracker
sudo chown ubuntu:ubuntu /opt/tunisia-price-tracker

# Extract files
cd /opt/tunisia-price-tracker
tar -xzf /tmp/deploy.tar.gz
rm /tmp/deploy.tar.gz

# Check if .env exists, if not copy from template
if [ ! -f .env ]; then
    echo "==> Creating .env from .env.production template"
    echo "==> IMPORTANT: Edit .env and change passwords before running!"
    cp .env.production .env
    echo ""
    echo "!! Run 'nano /opt/tunisia-price-tracker/.env' to set passwords !!"
    echo ""
fi

# Build and start containers
echo "==> Building and starting containers..."
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d

# Show status
echo "==> Deployment complete!"
docker compose -f docker-compose.prod.yml ps
ENDSSH

echo "==> Done! Your app should be running at http://$SERVER_IP"
