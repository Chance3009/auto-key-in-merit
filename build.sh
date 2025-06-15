#!/bin/bash
set -e  # Exit on error

echo "Starting build process..."

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Create the public directory if it doesn't exist
echo "Setting up public directory..."
mkdir -p public

# Copy static files to public directory if they exist
if [ -d "static" ]; then
    echo "Copying static files..."
    cp -r static/* public/ || {
        echo "Error: Failed to copy static files"
        exit 1
    }
else
    echo "Warning: static directory not found"
fi

# Ensure public files exist
if [ ! -f "public/404.html" ]; then
    echo "Error: 404.html not found in public directory"
    exit 1
fi

if [ ! -f "public/robots.txt" ]; then
    echo "Error: robots.txt not found in public directory"
    exit 1
fi

if [ ! -f "public/sitemap.xml" ]; then
    echo "Error: sitemap.xml not found in public directory"
    exit 1
fi

echo "Build completed successfully!"