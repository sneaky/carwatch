Note: This was an experiement at 100% vibecoding a simple project. Might redo this at a later date in Go but for now I just wanted to get something up and running.

# CarWatch

A configurable Python application that monitors CarMax for specific car listings and sends email notifications when new matches are found. Search by make, model, year range, transmission type, and more.

## Features

- **Configurable Search**: Search by make, model, year range, transmission, price, and mileage
- **CarMax Monitoring**: Scrapes CarMax nationwide for matching listings
- **Email Notifications**: Sends beautiful HTML email alerts for new listings
- **SQLite Database**: Tracks seen listings to avoid duplicate notifications
- **Automated Scheduling**: Runs every 6 hours via cron job
- **Comprehensive Logging**: Detailed logs for monitoring and debugging
- **Command-Line Arguments**: Override config settings from the command line

## Setup Instructions

### 1. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Optional: Create virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Email Settings

Copy the example environment file and configure your email settings:

```bash
cp .env.example .env
```

Edit `.env` with your email configuration:

```env
# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USER=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
NOTIFICATION_EMAIL=your_email@gmail.com
```

**For Gmail users:**
1. Enable 2-factor authentication
2. Generate an app password: Google Account → Security → App passwords
3. Use the app password (not your regular password)

**For other email providers:**
- Outlook: `smtp-mail.outlook.com:587`
- Yahoo: `smtp.mail.yahoo.com:587`
- Custom SMTP: Update `SMTP_SERVER` and `SMTP_PORT` accordingly

### 3. Configure Your Search

Edit `config.py` to set your search parameters:

```python
SEARCH_CONFIG = {
    'make': 'BMW',           # e.g., 'Toyota', 'Honda', 'Ford'
    'model': 'M2',           # e.g., 'Camry', 'Civic', 'Mustang'
    'year_start': 2016,      # Starting year
    'year_end': 2019,        # Ending year
    'max_mileage': None,     # Maximum mileage (None = no limit)
    'max_price': None,       # Maximum price (None = no limit)
    'transmission': 'manual', # 'manual', 'automatic', or 'any'
    'transmission_keywords': ['manual', '6-speed', '6 speed', 'stick shift']
}
```

### 4. Test the Application

Run a test to ensure everything is configured correctly:

```bash
python3 main.py
```

You can also override config settings from the command line:

```bash
# Search for a different car
python3 main.py --make Toyota --model Supra --year-start 2020 --year-end 2024

# Set price and mileage limits
python3 main.py --max-price 50000 --max-miles 30000

# Search for automatic transmission
python3 main.py --transmission automatic
```

Check the logs to verify:
- Database initialization
- Email configuration test
- Scraping results
- Notification sending

### 5. Setup Automated Scheduling

Add a cron job to run every 6 hours:

Use the provided start/stop scripts:

```bash
# Start the automated scraper
./start_scraper.sh

# Stop the automated scraper (when you find your car!)
./stop_scraper.sh
```

## Configuration

### Search Parameters

**Config File (`config.py`):**

```python
SEARCH_CONFIG = {
    'make': 'BMW',                    # Car manufacturer
    'model': 'M2',                    # Car model
    'year_start': 2016,               # Starting year (inclusive)
    'year_end': 2019,                 # Ending year (inclusive)
    'max_mileage': None,              # Max mileage in miles (None = unlimited)
    'max_price': None,                # Max price in dollars (None = unlimited)
    'transmission': 'manual',         # 'manual', 'automatic', or 'any'
    'transmission_keywords': ['manual', '6-speed', '6 speed', 'stick shift']
}
```

**Command-Line Arguments:**

```bash
python3 main.py [options]

Options:
  --make MAKE                Car make (e.g., BMW, Toyota)
  --model MODEL              Car model (e.g., M2, Camry)
  --year-start YEAR          Starting year
  --year-end YEAR            Ending year
  --max-miles MILES          Maximum mileage
  --max-price PRICE          Maximum price
  --transmission TYPE        Transmission: manual, automatic, or any
```

**Example Searches:**

```bash
# 2020-2024 Toyota Supra
python3 main.py --make Toyota --model Supra --year-start 2020 --year-end 2024

# Manual transmission Civic under $25k with less than 50k miles
python3 main.py --make Honda --model Civic --transmission manual --max-price 25000 --max-miles 50000

# Any Porsche 911 from 2015-2020
python3 main.py --make Porsche --model 911 --year-start 2015 --year-end 2020 --transmission any
```

### Logging

- **Application logs**: `scraper.log`
- **Cron logs**: `logs/scraper_YYYYMMDD_HHMMSS.log`
- **Error logs**: `logs/error.log`

## File Structure

```
carwatch/
├── main.py                 # Main orchestration script
├── database.py            # SQLite database operations
├── notifier.py            # Email notification system
├── config.py              # Configuration settings
├── requirements.txt       # Python dependencies
├── .env                   # Email configuration (not tracked in git)
├── .gitignore             # Git ignore rules
├── start_scraper.sh       # Start automated scraping
├── stop_scraper.sh        # Stop automated scraping
├── scrapers/
│   └── carmax_scraper.py  # CarMax scraper implementation
├── listings.db            # SQLite database (not tracked in git)
└── scraper.log            # Application logs (not tracked in git)
```

## Database Schema

The SQLite database stores listings with the following fields:

- `id`: Primary key
- `source`: 'CarMax'
- `title`: Listing title
- `price`: Price in dollars
- `mileage`: Mileage in miles
- `location`: Location string
- `url`: Listing URL
- `year`: Car year
- `transmission`: Transmission type
- `first_seen`: When first discovered
- `last_seen`: When last seen
- `notified`: Whether notification was sent

## Monitoring

### Check Recent Activity

```bash
# View recent logs
tail -f scraper.log

# Check cron execution
ls -la logs/

# View database stats
sqlite3 listings.db "SELECT source, COUNT(*) FROM listings GROUP BY source;"
```

### Manual Database Queries

```bash
# View all listings
sqlite3 listings.db "SELECT * FROM listings ORDER BY first_seen DESC;"

# View new listings (not notified)
sqlite3 listings.db "SELECT * FROM listings WHERE notified = FALSE;"

# Clean up old listings
sqlite3 listings.db "DELETE FROM listings WHERE last_seen < datetime('now', '-30 days');"
```

## Troubleshooting

### Common Issues

1. **Email not working**
   - Check `.env` file configuration
   - Verify app password for Gmail
   - Test SMTP connection: `python3 -c "from notifier import EmailNotifier; EmailNotifier().test_connection()"`

2. **No listings found**
   - Check if websites have changed structure
   - Verify search parameters in `config.py`
   - Check logs for scraping errors

3. **Cron not running**
   - Check cron service: `systemctl status cron`
   - Verify cron job: `crontab -l`
   - Check script permissions: `chmod +x run_scraper.sh`

4. **Database errors**
   - Check file permissions on `listings.db`
   - Verify SQLite installation: `python3 -c "import sqlite3"`

### Debug Mode

Run with debug logging:

```bash
# Edit config.py
LOG_LEVEL = 'DEBUG'

# Run manually
python3 main.py
```

## Legal Considerations

- **Respect robots.txt**: CarMax has robots.txt files
- **Rate limiting**: Built-in delays between requests
- **Terms of service**: Review CarMax's ToS before use
- **Personal use only**: This tool is for personal car shopping

## Use Cases

This tool is perfect for:
- Finding rare or specific car configurations
- Monitoring nationwide inventory for hard-to-find models
- Tracking manual transmission vehicles
- Setting up alerts for cars within your budget
- Finding low-mileage examples of specific models

## Examples

**Find a manual BMW M2:**
```bash
python3 main.py --make BMW --model M2 --transmission manual --year-start 2016 --year-end 2019
```

**Find a Tesla Model 3 under $30k:**
```bash
python3 main.py --make Tesla --model "Model 3" --max-price 30000
```

**Find low-mileage Mazda Miata:**
```bash
python3 main.py --make Mazda --model Miata --max-miles 50000 --year-start 2016 --year-end 2024
```

## License

This project is for personal use only. Please respect the terms of service of the websites being scraped.

