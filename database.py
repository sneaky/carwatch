"""
Database layer for car listing scraper
Handles SQLite database operations for storing and tracking listings
"""

import sqlite3
import logging
from datetime import datetime
from typing import List, Dict, Optional
from config import DATABASE_PATH

logger = logging.getLogger(__name__)

class ListingDatabase:
    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create listings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS listings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL,
                    title TEXT NOT NULL,
                    price INTEGER,
                    mileage INTEGER,
                    location TEXT,
                    url TEXT UNIQUE NOT NULL,
                    year INTEGER,
                    transmission TEXT,
                    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    notified BOOLEAN DEFAULT FALSE
                )
            ''')
            
            # Create index on URL for faster lookups
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_url ON listings(url)
            ''')
            
            # Create index on source for filtering
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_source ON listings(source)
            ''')
            
            conn.commit()
            logger.info("Database initialized successfully")
    
    def add_listing(self, listing: Dict) -> bool:
        """Add a new listing to the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if listing already exists
                cursor.execute('SELECT id FROM listings WHERE url = ?', (listing['url'],))
                if cursor.fetchone():
                    # Update last_seen timestamp
                    cursor.execute('''
                        UPDATE listings 
                        SET last_seen = CURRENT_TIMESTAMP 
                        WHERE url = ?
                    ''', (listing['url'],))
                    return False  # Not a new listing
                
                # Insert new listing
                cursor.execute('''
                    INSERT INTO listings 
                    (source, title, price, mileage, location, url, year, transmission)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    listing.get('source'),
                    listing.get('title'),
                    listing.get('price'),
                    listing.get('mileage'),
                    listing.get('location'),
                    listing.get('url'),
                    listing.get('year'),
                    listing.get('transmission')
                ))
                
                conn.commit()
                logger.info(f"Added new listing: {listing.get('title', 'Unknown')}")
                return True
                
        except sqlite3.Error as e:
            logger.error(f"Database error adding listing: {e}")
            return False
    
    def get_new_listings(self) -> List[Dict]:
        """Get all listings that haven't been notified yet"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM listings 
                    WHERE notified = FALSE 
                    ORDER BY first_seen DESC
                ''')
                
                return [dict(row) for row in cursor.fetchall()]
                
        except sqlite3.Error as e:
            logger.error(f"Database error getting new listings: {e}")
            return []
    
    def mark_as_notified(self, listing_ids: List[int]):
        """Mark listings as notified"""
        if not listing_ids:
            return
            
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                placeholders = ','.join('?' * len(listing_ids))
                cursor.execute(f'''
                    UPDATE listings 
                    SET notified = TRUE 
                    WHERE id IN ({placeholders})
                ''', listing_ids)
                
                conn.commit()
                logger.info(f"Marked {len(listing_ids)} listings as notified")
                
        except sqlite3.Error as e:
            logger.error(f"Database error marking as notified: {e}")
    
    def get_all_listings(self, source: Optional[str] = None) -> List[Dict]:
        """Get all listings, optionally filtered by source"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                if source:
                    cursor.execute('SELECT * FROM listings WHERE source = ? ORDER BY first_seen DESC', (source,))
                else:
                    cursor.execute('SELECT * FROM listings ORDER BY first_seen DESC')
                
                return [dict(row) for row in cursor.fetchall()]
                
        except sqlite3.Error as e:
            logger.error(f"Database error getting listings: {e}")
            return []
    
    def cleanup_old_listings(self, days_old: int = 30):
        """Remove listings that haven't been seen in X days"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    DELETE FROM listings 
                    WHERE last_seen < datetime('now', '-{} days')
                '''.format(days_old))
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                if deleted_count > 0:
                    logger.info(f"Cleaned up {deleted_count} old listings")
                
        except sqlite3.Error as e:
            logger.error(f"Database error cleaning up old listings: {e}")
    
    def get_stats(self) -> Dict:
        """Get database statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Total listings
                cursor.execute('SELECT COUNT(*) FROM listings')
                total = cursor.fetchone()[0]
                
                # New listings (not notified)
                cursor.execute('SELECT COUNT(*) FROM listings WHERE notified = FALSE')
                new = cursor.fetchone()[0]
                
                # By source
                cursor.execute('SELECT source, COUNT(*) FROM listings GROUP BY source')
                by_source = dict(cursor.fetchall())
                
                return {
                    'total': total,
                    'new': new,
                    'by_source': by_source
                }
                
        except sqlite3.Error as e:
            logger.error(f"Database error getting stats: {e}")
            return {'total': 0, 'new': 0, 'by_source': {}}


