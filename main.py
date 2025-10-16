"""
Main orchestration script for car listing scraper
Coordinates scraping, database operations, and notifications
"""

import argparse
import logging
import sys
from datetime import datetime
from typing import List, Dict

from database import ListingDatabase
from notifier import EmailNotifier
from scrapers.carmax_scraper import CarMaxScraper
from config import LOG_LEVEL, LOG_FILE, SEARCH_CONFIG

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler(sys.stdout)
        ]
    )

def parse_arguments():
    """Parse command line arguments with fallback to config defaults"""
    parser = argparse.ArgumentParser(description='Car listing scraper for CarMax')
    
    parser.add_argument('--make', type=str, default=SEARCH_CONFIG['make'],
                       help='Car make (e.g., BMW, Toyota)')
    parser.add_argument('--model', type=str, default=SEARCH_CONFIG['model'],
                       help='Car model (e.g., M2, Camry)')
    parser.add_argument('--year-start', type=int, default=SEARCH_CONFIG['year_start'],
                       help='Starting year for search')
    parser.add_argument('--year-end', type=int, default=SEARCH_CONFIG['year_end'],
                       help='Ending year for search')
    parser.add_argument('--max-miles', type=int, default=SEARCH_CONFIG['max_mileage'],
                       help='Maximum mileage (no limit if not specified)')
    parser.add_argument('--max-price', type=int, default=SEARCH_CONFIG['max_price'],
                       help='Maximum price (no limit if not specified)')
    parser.add_argument('--transmission', type=str, choices=['manual', 'automatic', 'any'],
                       default=SEARCH_CONFIG['transmission'],
                       help='Transmission type preference')
    
    args = parser.parse_args()
    
    # Convert to dict for easier passing
    search_params = {
        'make': args.make,
        'model': args.model,
        'year_start': args.year_start,
        'year_end': args.year_end,
        'max_mileage': args.max_miles,
        'max_price': args.max_price,
        'transmission': args.transmission
    }
    
    return search_params

def main():
    """Main function to orchestrate the scraping process"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Parse command line arguments
    search_params = parse_arguments()
    
    logger.info(f"Starting car listing scraper for {search_params['make']} {search_params['model']}")
    start_time = datetime.now()
    
    try:
        # Initialize components
        db = ListingDatabase()
        notifier = EmailNotifier()
        carmax_scraper = CarMaxScraper(**search_params)
        
        # Test email configuration
        if not notifier.test_connection():
            logger.warning("Email configuration test failed. Notifications may not work.")
        
        all_new_listings = []
        
        # Scrape CarMax
        logger.info("Scraping CarMax...")
        try:
            carmax_listings = carmax_scraper.scrape_listings()
            logger.info(f"CarMax: Found {len(carmax_listings)} listings")
            
            # Add new CarMax listings to database
            carmax_new = []
            for listing in carmax_listings:
                if db.add_listing(listing):
                    carmax_new.append(listing)
            
            all_new_listings.extend(carmax_new)
            logger.info(f"CarMax: {len(carmax_new)} new listings added to database")
            
        except Exception as e:
            logger.error(f"Error scraping CarMax: {e}")
        
        # Send notifications for new listings
        if all_new_listings:
            logger.info(f"Sending notifications for {len(all_new_listings)} new listings")
            
            if notifier.send_notification(all_new_listings):
                # Mark listings as notified
                new_listing_ids = [listing.get('id') for listing in db.get_new_listings() 
                                 if listing['url'] in [l['url'] for l in all_new_listings]]
                db.mark_as_notified(new_listing_ids)
                logger.info("Notifications sent successfully")
            else:
                logger.error("Failed to send notifications")
        else:
            logger.info("No new listings found")
        
        # Cleanup old listings (optional)
        db.cleanup_old_listings(days_old=30)
        
        # Log final statistics
        stats = db.get_stats()
        logger.info(f"Database stats: {stats['total']} total listings, {stats['new']} new, by source: {stats['by_source']}")
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        logger.info(f"Scraping completed in {duration:.2f} seconds")
        
    except Exception as e:
        logger.error(f"Fatal error in main process: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
