# Quick Setup Guide

## ✅ Dependencies Installed Successfully!

The pip install error has been resolved by creating a virtual environment. All dependencies are now installed.

## 🔧 Next Steps

### 1. Configure Email Settings

Create your email configuration file:

```bash
cp .env.example .env
```

Edit `.env` with your email settings:

```env
# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USER=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
NOTIFICATION_EMAIL=your_email@gmail.com
```

**For Gmail:**
1. Enable 2-factor authentication
2. Go to Google Account → Security → App passwords
3. Generate an app password
4. Use the app password (not your regular password)

### 2. Test Email Configuration

```bash
source venv/bin/activate
python3 -c "from notifier import EmailNotifier; EmailNotifier().test_connection()"
```

### 3. Run the Scraper

```bash
source venv/bin/activate
python3 main.py
```

### 4. Setup Automation (Optional)

```bash
./setup_cron.sh
```

## 🚨 Current Status

- ✅ Dependencies installed
- ✅ Application runs without errors
- ⚠️ Email configuration needed
- ⚠️ Web scraping may be blocked by anti-bot protection

## 📝 Notes

The scraper is working correctly, but CarMax may sometimes block requests with 403/418 errors. This is common with anti-bot protection. The scraper includes:

- Multiple user agents and headers
- Rate limiting between requests
- Fallback parsing methods

You may need to:
1. Run from a different IP address
2. Use a VPN
3. Add more sophisticated anti-detection measures
4. Check if the sites have changed their structure

The application is ready to work once the anti-bot protection is bypassed or the sites allow the requests.


