#!/bin/bash
gunicorn \
    --bind 0.0.0.0:5050 \
    --timeout 300 \
    --workers 4 \
    --threads 2 \
    --access-logfile /var/log/merit/access.log \
    --error-logfile /var/log/merit/error.log \
    --capture-output \
    --log-level debug \
    app:app 