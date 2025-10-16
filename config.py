"""
Configuration settings for car listing scraper
"""

# Search parameters
SEARCH_CONFIG = {
    'make': 'BMW',
    'model': 'M2',
    'year_start': 2016,
    'year_end': 2019,
    'max_mileage': None,  # No limit if None
    'max_price': None,    # No limit if None
    'transmission': 'manual',  # 'manual', 'automatic', or 'any'
    'transmission_keywords': ['manual', '6-speed', '6 speed', 'stick shift']
}


# Database settings
DATABASE_PATH = 'listings.db'

# Logging settings
LOG_LEVEL = 'INFO'
LOG_FILE = 'scraper.log'

