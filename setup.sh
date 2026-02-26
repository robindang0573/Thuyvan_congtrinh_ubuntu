#!/bin/bash

# Update package list
echo "Updating package list..."
sudo apt-get update

# Install Python 3, pip, and venv if not present
echo "Installing Python 3 and dependencies..."
sudo apt-get install -y python3 python3-pip python3-venv

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install requirements
echo "Installing project dependencies..."
pip install -r requirements.txt

echo "Setup complete! Run ./run.sh to start the application."
