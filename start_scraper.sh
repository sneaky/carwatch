#!/bin/bash

# CarWatch - Start Script
# This script sets up the cron job to run the scraper every 6 hours

echo "🚗 Starting CarWatch scraper..."
echo "Setting up cron job to run every 6 hours..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run setup first."
    echo "Run: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Please create it with your email settings."
    echo "Copy .env.example to .env and fill in your email configuration."
    exit 1
fi

# Get the current directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Create the cron job
CRON_JOB="0 */6 * * * cd $SCRIPT_DIR && $SCRIPT_DIR/venv/bin/python3 $SCRIPT_DIR/main.py >> $SCRIPT_DIR/scraper.log 2>&1"

# Add the cron job
echo "$CRON_JOB" | crontab -

# Verify it was added
echo "✅ Cron job added successfully!"
echo "📅 Schedule: Every 6 hours (00:00, 06:00, 12:00, 18:00)"
echo "📧 You'll receive email notifications when new listings are found"
echo ""
echo "To check if it's running: crontab -l"
echo "To view logs: tail -f scraper.log"
echo "To stop the scraper: ./stop_scraper.sh"

