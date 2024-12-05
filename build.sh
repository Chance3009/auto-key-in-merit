#!/bin/bash

# Update package manager and install required system dependencies
apt-get update -y && apt-get install -y \
    wget \
    curl \
    libx11-dev \
    libgconf-2-4 \
    libnss3 \
    libxss1 \
    libxtst6

# Install Google Chrome
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
apt-get install -y ./google-chrome-stable_current_amd64.deb

# Clean up
rm google-chrome-stable_current_amd64.deb

# Install Python dependencies from requirements.txt
pip install -r requirements.txt
