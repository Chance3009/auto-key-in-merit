#!/usr/bin/env bash
# exit on error
set -o errexit

# Define storage directory for Render environment
STORAGE_DIR=/opt/render/project/.render

# Check if Chrome is already downloaded; if not, download and extract it
if [[ ! -d $STORAGE_DIR/chrome ]]; then
  echo "...Downloading Chrome"
  
  # Create directory for Chrome installation
  mkdir -p $STORAGE_DIR/chrome
  
  # Change to the storage directory and download Chrome
  cd $STORAGE_DIR/chrome
  
  # Download the latest stable version of Google Chrome
  wget -P ./ https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
  
  # Extract the package to the storage directory
  dpkg -x ./google-chrome-stable_current_amd64.deb $STORAGE_DIR/chrome
  
  # Clean up the downloaded .deb package
  rm ./google-chrome-stable_current_amd64.deb
  
  # Return to the project source directory
  cd $HOME/project/src
else
  echo "...Using Chrome from cache"
fi

# Add Chrome's location to the PATH so it's accessible during execution
export PATH="${PATH}:${STORAGE_DIR}/chrome/opt/google/chrome"

# Optionally, you can verify the Chrome installation
google-chrome --version

# Add your build or install commands here (if any)
pip install -r requirements.txt
