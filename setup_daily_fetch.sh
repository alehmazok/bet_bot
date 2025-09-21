#!/bin/bash

# Simple NHL Game Data Fetcher - Daily Cron Setup
# This script sets up a daily cron job to fetch NHL game results

PROJECT_DIR="/workspace"
PYTHON_PATH="/usr/bin/python3"
MANAGE_PY="$PROJECT_DIR/manage.py"
LOG_FILE="$PROJECT_DIR/nhl_fetch.log"

# Create the cron job command (runs daily at 9:00 AM)
CRON_COMMAND="0 9 * * * cd $PROJECT_DIR && $PYTHON_PATH $MANAGE_PY fetch_nhl_scores >> $LOG_FILE 2>&1"

echo "Setting up daily NHL data fetch..."
echo "Command: $CRON_COMMAND"

# Add to crontab
(crontab -l 2>/dev/null | grep -v "fetch_nhl_scores"; echo "$CRON_COMMAND") | crontab -

echo "✅ Cron job setup complete!"
echo "   Runs daily at 9:00 AM"
echo "   Logs: $LOG_FILE"
echo ""
echo "To view logs: tail -f $LOG_FILE"
echo "To test manually: cd $PROJECT_DIR && $PYTHON_PATH $MANAGE_PY fetch_nhl_scores"