#!/bin/bash

# Log file location
LOG_FILE="/var/log/auth.log"
MONITOR_LOG="$HOME/ssh_monitoring.log"

# Function to check SSH login attempts
check_ssh() {
    echo "=== SSH Access Report $(date) ===" >> "$MONITOR_LOG"
    echo "Last 10 successful logins:" >> "$MONITOR_LOG"
    grep "Accepted publickey" "$LOG_FILE" | tail -n 10 >> "$MONITOR_LOG"
    echo -e "\nFailed login attempts in the last hour:" >> "$MONITOR_LOG"
    grep "Invalid user\|Failed password" "$LOG_FILE" | grep "$(date +%b' '%d)" >> "$MONITOR_LOG"
    echo -e "\n=== End Report ===\n" >> "$MONITOR_LOG"
}

# Run the check
check_ssh 