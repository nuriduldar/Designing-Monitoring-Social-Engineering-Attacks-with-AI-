#!/bin/bash

# Idempotent provisioning script for social-engineering-ai VM
# This script can be run multiple times safely

set -e

echo "=========================================="
echo "Provisioning social-engineering-ai VM"
echo "=========================================="

# Update package list
echo "Updating package list..."
sudo apt-get update -qq

# Install basic dependencies
echo "Installing basic dependencies..."
sudo apt-get install -y -qq \
    python3 \
    python3-pip \
    python3-venv \
    git \
    wget \
    curl \
    unzip

# Install MailHog
echo "Installing MailHog..."
if [ ! -f /usr/local/bin/mailhog ]; then
    wget -q https://github.com/mailhog/MailHog/releases/download/v1.0.1/mailhog_linux_amd64 -O /tmp/mailhog
    sudo mv /tmp/mailhog /usr/local/bin/mailhog
    sudo chmod +x /usr/local/bin/mailhog
    
    # Create systemd service for MailHog
    sudo tee /etc/systemd/system/mailhog.service > /dev/null <<EOF
[Unit]
Description=MailHog Service
After=network.target

[Service]
Type=simple
User=vagrant
ExecStart=/usr/local/bin/mailhog -api-bind-addr 0.0.0.0:8025 -ui-bind-addr 0.0.0.0:8025 -smtp-bind-addr 0.0.0.0:1025
Restart=always

[Install]
WantedBy=multi-user.target
EOF
    
    sudo systemctl daemon-reload
    sudo systemctl enable mailhog
    sudo systemctl start mailhog
    echo "MailHog installed and started"
else
    echo "MailHog already installed"
fi

# Create Python virtual environment
echo "Setting up Python virtual environment..."
cd /home/vagrant/project

if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo "Virtual environment created"
else
    echo "Virtual environment already exists"
fi

# Activate virtual environment and install requirements
source .venv/bin/activate

# Install requirements from each module
if [ -f "sim_server/requirements.txt" ]; then
    echo "Installing sim_server requirements..."
    pip install -q -r sim_server/requirements.txt
fi

if [ -f "detection/requirements.txt" ]; then
    echo "Installing detection requirements..."
    pip install -q -r detection/requirements.txt
fi

if [ -f "generator/requirements.txt" ]; then
    echo "Installing generator requirements..."
    pip install -q -r generator/requirements.txt
fi

# Create logs directory
echo "Creating logs directory..."
mkdir -p logs

# Create interaction_logs.csv if it doesn't exist
if [ ! -f "interaction_logs.csv" ]; then
    echo "Creating interaction_logs.csv..."
    echo "timestamp,participant_id,scenario_id,action,metadata" > interaction_logs.csv
fi

# Create models directory
mkdir -p models

echo ""
echo "=========================================="
echo "Provisioning complete!"
echo "=========================================="
echo ""
echo "To start the Flask application:"
echo "  1. vagrant ssh"
echo "  2. cd /home/vagrant/project"
echo "  3. source .venv/bin/activate"
echo "  4. python sim_server/app.py"
echo ""
echo "Access from host:"
echo "  - Flask app: http://localhost:5000"
echo "  - MailHog UI: http://localhost:8025"
echo ""
echo "MailHog is running as a systemd service."
echo "To check status: sudo systemctl status mailhog"
echo ""

