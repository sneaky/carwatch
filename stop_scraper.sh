#!/bin/bash

# CarWatch - Stop Script
# This script removes the cron job and stops the automated scraping

echo "🛑 Stopping CarWatch scraper..."

# Remove all cron jobs (this removes the scraper cron job)
crontab -r

# Check if removal was successful
if [ $? -eq 0 ]; then
    echo "✅ Cron job removed successfully!"
    echo "🚗 CarWatch scraper has been stopped."
    echo "📧 You will no longer receive automated email notifications."
    echo ""
    echo "To restart the scraper: ./start_scraper.sh"
else
    echo "❌ Failed to remove cron job."
    echo "You may need to run: crontab -r manually"
fi

# Show current cron jobs (should be empty)
echo ""
echo "Current cron jobs:"
crontab -l 2>/dev/null || echo "No cron jobs found."

