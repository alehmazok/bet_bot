#!/bin/bash

# NHL Data Fetcher - Cron Job Setup Script
# This script sets up a daily cron job to fetch NHL game results

# Configuration
PROJECT_DIR="/workspace"
PYTHON_PATH="/usr/bin/python3"
MANAGE_PY="$PROJECT_DIR/manage.py"
LOG_DIR="$PROJECT_DIR/logs"
LOG_FILE="$LOG_DIR/nhl_fetch.log"

# Create logs directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Create the cron job command
CRON_COMMAND="0 9 * * * cd $PROJECT_DIR && $PYTHON_PATH $MANAGE_PY fetch_nhl_scores >> $LOG_FILE 2>&1"

echo "Setting up NHL data fetcher cron job..."
echo "Command: $CRON_COMMAND"
echo ""

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "fetch_nhl_scores"; then
    echo "NHL data fetcher cron job already exists. Updating..."
    # Remove existing job and add new one
    (crontab -l 2>/dev/null | grep -v "fetch_nhl_scores"; echo "$CRON_COMMAND") | crontab -
else
    echo "Adding new NHL data fetcher cron job..."
    # Add new job to existing crontab
    (crontab -l 2>/dev/null; echo "$CRON_COMMAND") | crontab -
fi

echo "Cron job setup complete!"
echo ""
echo "The NHL data fetcher will run daily at 9:00 AM"
echo "Logs will be written to: $LOG_FILE"
echo ""
echo "To view current cron jobs: crontab -l"
echo "To manually run the command: cd $PROJECT_DIR && $PYTHON_PATH $MANAGE_PY fetch_nhl_scores"
echo "To view logs: tail -f $LOG_FILE"