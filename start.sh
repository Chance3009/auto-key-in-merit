#!/bin/bash

# Create log directory if it doesn't exist
mkdir -p /var/log/merit

# Set proper permissions
chown -R www-data:www-data /var/log/merit

# Start Gunicorn with improved configuration
gunicorn \
    --bind 0.0.0.0:5050 \
    --timeout 300 \
    --workers 2 \
    --threads 4 \
    --worker-class=gthread \
    --worker-tmp-dir=/dev/shm \
    --access-logfile /var/log/merit/access.log \
    --error-logfile /var/log/merit/error.log \
    --capture-output \
    --enable-stdio-inheritance \
    --log-level debug \
    --reload \
    app:app 