#!/bin/bash
set -e  # Exit on error

# Install Python dependencies
pip install -r requirements.txt

# Create the public directory if it doesn't exist
mkdir -p public

# Copy static files to public directory if they exist
if [ -d "static" ]; then
    cp -r static/* public/
fi

# Create a simple index.html that redirects to the Firebase Function
cat > public/index.html << 'EOL'
<!DOCTYPE html>
<html>
<head>
    <meta http-equiv="refresh" content="0;url=/app">
</head>
<body>
    <p>Redirecting to application...</p>
</body>
</html>
EOL

# Make the script executable
chmod +x build.sh