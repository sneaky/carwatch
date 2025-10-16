"""
Email notification system for car listing scraper
Handles sending email notifications for new listings
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class EmailNotifier:
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.email_user = os.getenv('EMAIL_USER')
        self.email_password = os.getenv('EMAIL_PASSWORD')
        self.notification_email = os.getenv('NOTIFICATION_EMAIL')
        
        if not all([self.email_user, self.email_password, self.notification_email]):
            logger.warning("Email configuration incomplete. Notifications will be disabled.")
            self.enabled = False
        else:
            self.enabled = True
    
    def send_notification(self, listings: List[Dict]) -> bool:
        """Send email notification with new listings"""
        if not self.enabled:
            logger.warning("Email notifications disabled due to incomplete configuration")
            return False
        
        if not listings:
            logger.info("No new listings to notify about")
            return True
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.email_user
            msg['To'] = self.notification_email
            msg['Subject'] = f"🚗 New Car Listings Found ({len(listings)} new)"
            
            # Create email body
            body = self._create_email_body(listings)
            msg.attach(MIMEText(body, 'html'))
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_user, self.email_password)
                server.send_message(msg)
            
            logger.info(f"Successfully sent notification for {len(listings)} listings")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
            return False
    
    def _create_email_body(self, listings: List[Dict]) -> str:
        """Create HTML email body with listing details"""
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .listing {{ 
                    border: 1px solid #ddd; 
                    margin: 10px 0; 
                    padding: 15px; 
                    border-radius: 5px;
                    background-color: #f9f9f9;
                }}
                .title {{ font-weight: bold; font-size: 16px; color: #333; }}
                .price {{ font-size: 18px; color: #2e7d32; font-weight: bold; }}
                .details {{ color: #666; margin: 5px 0; }}
                .source {{ 
                    display: inline-block; 
                    padding: 2px 8px; 
                    border-radius: 3px; 
                    font-size: 12px; 
                    font-weight: bold;
                }}
                .carmax {{ background-color: #e3f2fd; color: #1976d2; }}
                .url {{ margin-top: 10px; }}
                .url a {{ color: #1976d2; text-decoration: none; }}
            </style>
        </head>
        <body>
            <h2>🚗 New Car Listings Found!</h2>
            <p>Found {len(listings)} new car listings matching your criteria:</p>
            <ul>
                <li>Years: 2016-2019</li>
                <li>Transmission: 6-speed manual</li>
                <li>Source: CarMax (nationwide)</li>
            </ul>
        """
        
        for listing in listings:
            source_class = listing.get('source', '').lower()
            price_str = f"${listing.get('price', 'N/A'):,}" if listing.get('price') else 'Price N/A'
            mileage_str = f"{listing.get('mileage', 'N/A'):,} miles" if listing.get('mileage') else 'Mileage N/A'
            
            html += f"""
            <div class="listing">
                <div class="title">{listing.get('title', 'Unknown Title')}</div>
                <div class="price">{price_str}</div>
                <div class="details">
                    <strong>Year:</strong> {listing.get('year', 'N/A')} | 
                    <strong>Mileage:</strong> {mileage_str} | 
                    <strong>Location:</strong> {listing.get('location', 'N/A')}
                </div>
                <div class="details">
                    <strong>Transmission:</strong> {listing.get('transmission', 'N/A')} | 
                    <span class="source {source_class}">{listing.get('source', 'Unknown')}</span>
                </div>
                <div class="url">
                    <a href="{listing.get('url', '#')}" target="_blank">View Listing →</a>
                </div>
            </div>
            """
        
        html += """
            <hr>
            <p><em>This is an automated notification from your car listing scraper.</em></p>
        </body>
        </html>
        """
        
        return html
    
    def test_connection(self) -> bool:
        """Test email configuration and connection"""
        if not self.enabled:
            return False
        
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_user, self.email_password)
            
            logger.info("Email configuration test successful")
            return True
            
        except Exception as e:
            logger.error(f"Email configuration test failed: {e}")
            return False


