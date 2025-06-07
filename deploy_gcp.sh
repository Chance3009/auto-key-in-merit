#!/bin/bash

# Stop on any error
set -e

echo "=== Starting deployment ==="

# Create necessary directories
sudo mkdir -p /var/www/auto-key-in-merit
sudo mkdir -p /var/log/merit

# Set permissions
sudo chown -R www-data:www-data /var/log/merit
sudo chown -R www-data:www-data /var/www/auto-key-in-merit

# Navigate to app directory
cd /var/www/auto-key-in-merit

# Pull latest code
git pull origin main

# Setup virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Activate virtual environment and install requirements
source venv/bin/activate
pip install -r requirements.txt

# Make start.sh executable
chmod +x start.sh

# Copy service file
sudo cp merit.service /etc/systemd/system/

# Reload systemd and restart service
sudo systemctl daemon-reload
sudo systemctl enable merit
sudo systemctl restart merit

# Check service status
sudo systemctl status merit

echo "=== Deployment complete ==="

# Show logs
echo "=== Recent logs ==="
sudo tail -n 50 /var/log/merit/error.log 