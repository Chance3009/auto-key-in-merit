#!/usr/bin/env bash
# exit on error
set -o errexit

# Define storage directory for Render environment
# Install Chrome (as before)
STORAGE_DIR=/opt/render/project/.render

if [[ ! -d $STORAGE_DIR/chrome ]]; then
    echo "...Downloading Chrome"
    mkdir -p $STORAGE_DIR/chrome
    cd $STORAGE_DIR/chrome
    wget -P ./ https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
    dpkg -x ./google-chrome-stable_current_amd64.deb $STORAGE_DIR/chrome
    rm ./google-chrome-stable_current_amd64.deb
    cd $HOME/project/src
else
    echo "...Using Chrome from cache"
fi

# Get the Chrome version
CHROME_VERSION=$($STORAGE_DIR/chrome/opt/google/chrome/chrome --version | awk '{print $3}')
echo "Chrome Version: $CHROME_VERSION"  # Log the version to check if it's correct

# Now fetch the correct ChromeDriver version for this Chrome version
DRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_$CHROME_VERSION")
echo "ChromeDriver Version: $DRIVER_VERSION"  # Log the driver version to check if it's correct

# Download ChromeDriver
wget -P $STORAGE_DIR/chrome/ https://chromedriver.storage.googleapis.com/$DRIVER_VERSION/chromedriver_linux64.zip
unzip $STORAGE_DIR/chrome/chromedriver_linux64.zip -d $STORAGE_DIR/chrome/
rm $STORAGE_DIR/chrome/chromedriver_linux64.zip

# Add Chrome and ChromeDriver to the PATH
export PATH="$STORAGE_DIR/chrome/opt/google/chrome:$STORAGE_DIR/chrome:$PATH"

# Optionally, you can verify the Chrome installation
google-chrome --version

# Add your build or install commands here (if any)
pip install -r requirements.txt
