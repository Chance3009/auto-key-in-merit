#!/usr/bin/env bash
# exit on error
set -o errexit

STORAGE_DIR=/opt/render/project/.render

if [[ ! -d $STORAGE_DIR/chrome ]]; then
  echo "...Downloading Chrome"
  mkdir -p $STORAGE_DIR/chrome
  cd $STORAGE_DIR/chrome
  wget -P ./ https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
  dpkg -x ./google-chrome-stable_current_amd64.deb $STORAGE_DIR/chrome
  rm ./google-chrome-stable_current_amd64.deb
  cd $HOME/project/src # Make sure we return to where we were
else
  echo "...Using Chrome from cache"
fi

# Fetch Chrome version and use it to get the corresponding ChromeDriver
CHROME_VERSION=$($STORAGE_DIR/chrome/opt/google/chrome/chrome --version | awk '{print $3}')
echo "Chrome Version: $CHROME_VERSION"

# Try to fetch the ChromeDriver version
DRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_$CHROME_VERSION")

# If the exact version is not found, fall back to a compatible version
if [[ -z "$DRIVER_VERSION" ]]; then
  echo "ChromeDriver version for $CHROME_VERSION not found. Trying with the closest available version..."
  DRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE")  # Fallback to latest release
fi

echo "Using ChromeDriver Version: $DRIVER_VERSION"

# Download the corresponding ChromeDriver
wget "https://chromedriver.storage.googleapis.com/$DRIVER_VERSION/chromedriver_linux64.zip" -P $STORAGE_DIR/chrome
unzip -o $STORAGE_DIR/chrome/chromedriver_linux64.zip -d $STORAGE_DIR/chrome
rm $STORAGE_DIR/chrome/chromedriver_linux64.zip

# be sure to add Chromes location to the PATH as part of your Start Command
# export PATH="${PATH}:/opt/render/project/.render/chrome/opt/google/chrome"

# add your own build commands...
pip install -r requirements.txt