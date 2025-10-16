"""
CarMax scraper for car listings
Scrapes CarMax nationwide for specified make/model with customizable filters
"""

import requests
from bs4 import BeautifulSoup
import logging
import time
import re
import random
from typing import List, Dict
from urllib.parse import urljoin, urlparse, parse_qs, quote

logger = logging.getLogger(__name__)

class CarMaxScraper:
    def __init__(self, make, model, year_start, year_end, max_mileage=None, max_price=None, transmission='any'):
        self.base_url = "https://www.carmax.com"
        
        # Store search parameters
        self.make = make
        self.model = model
        self.year_start = year_start
        self.year_end = year_end
        self.max_mileage = max_mileage
        self.max_price = max_price
        self.transmission = transmission
        
        # Build dynamic search URL
        make_encoded = quote(make.lower())
        model_encoded = quote(model.lower())
        self.search_url = f"{self.base_url}/cars/{make_encoded}/{model_encoded}"
        
        self.session = requests.Session()
        
        # Enhanced headers to bypass anti-bot detection
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'DNT': '1',
            'Sec-CH-UA': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'Sec-CH-UA-Mobile': '?0',
            'Sec-CH-UA-Platform': '"Windows"'
        })
    
    def _make_request(self, url: str, max_retries: int = 3) -> requests.Response:
        """Make a request with retry logic and anti-detection measures"""
        for attempt in range(max_retries):
            try:
                # Random delay between requests
                if attempt > 0:
                    time.sleep(random.uniform(2, 5))
                
                # Rotate user agents
                user_agents = [
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15'
                ]
                
                self.session.headers['User-Agent'] = random.choice(user_agents)
                
                # Make request with timeout and appropriate headers for search
                if 'carmax.com/cars/' in url:
                    # This is a search request, add referer
                    self.session.headers['Referer'] = self.base_url
                    self.session.headers['Sec-Fetch-Site'] = 'same-origin'
                else:
                    # This is homepage or other request
                    self.session.headers.pop('Referer', None)
                    self.session.headers['Sec-Fetch-Site'] = 'none'
                
                response = self.session.get(url, timeout=30, allow_redirects=True)
                
                # Check for successful response
                if response.status_code == 200:
                    return response
                elif response.status_code == 403:
                    logger.warning(f"403 Forbidden on attempt {attempt + 1}, retrying...")
                    continue
                elif response.status_code == 418:
                    logger.warning(f"418 I'm a teapot on attempt {attempt + 1}, retrying...")
                    continue
                else:
                    logger.warning(f"Unexpected status {response.status_code} on attempt {attempt + 1}")
                    continue
                    
            except requests.RequestException as e:
                logger.warning(f"Request failed on attempt {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    logger.error(f"All {max_retries} attempts failed for {url}")
                    return None
                continue
        
        return None
    
    def _parse_javascript_data(self, html_content: str) -> List[Dict]:
        """Parse JavaScript data embedded in the HTML"""
        import json
        
        try:
            # Look for JavaScript arrays containing car data
            js_patterns = [
                r'const cars = \[(.*?)\];',
                r'var cars = \[(.*?)\];',
                r'cars:\s*\[(.*?)\]',
                r'"cars":\s*\[(.*?)\]'
            ]
            
            for pattern in js_patterns:
                matches = re.findall(pattern, html_content, re.DOTALL)
                for match in matches:
                    try:
                        # Try to parse as JSON array
                        json_str = '[' + match + ']'
                        cars_data = json.loads(json_str)
                        if isinstance(cars_data, list) and len(cars_data) > 0:
                            logger.info(f"Found {len(cars_data)} cars in JavaScript data")
                            return cars_data
                    except json.JSONDecodeError:
                        continue
            
            # Look for individual car objects
            car_patterns = [
                r'"stockNumber":(\d+).*?"vin":"([^"]+)".*?"year":(\d+).*?"make":"([^"]+)".*?"model":"([^"]+)"',
                r'"vin":"([^"]+)".*?"year":(\d+).*?"make":"([^"]+)".*?"model":"([^"]+)"'
            ]
            
            cars = []
            for pattern in car_patterns:
                matches = re.findall(pattern, html_content)
                for match in matches:
                    if len(match) >= 4:
                        car_data = {
                            'vin': match[0] if len(match) > 0 else '',
                            'year': int(match[1]) if len(match) > 1 else None,
                            'make': match[2] if len(match) > 2 else '',
                            'model': match[3] if len(match) > 3 else ''
                        }
                        cars.append(car_data)
            
            if cars:
                logger.info(f"Found {len(cars)} cars in JavaScript patterns")
                return cars
                
        except Exception as e:
            logger.debug(f"Error parsing JavaScript data: {e}")
        
        return []
    
    def _convert_js_listing(self, js_data: Dict) -> Dict:
        """Convert JavaScript car data to our listing format"""
        listing = {
            'source': 'CarMax',
            'title': '',
            'price': None,
            'mileage': None,
            'location': '',
            'url': '',
            'year': None,
            'transmission': ''
        }
        
        try:
            # Extract basic info
            listing['year'] = js_data.get('year')
            make = js_data.get('make', '')
            model = js_data.get('model', '')
            listing['title'] = f"{listing['year']} {make} {model}"
            
            # Extract price
            if 'basePrice' in js_data:
                listing['price'] = int(js_data['basePrice'])
            elif 'price' in js_data:
                listing['price'] = js_data['price']
            elif 'listPrice' in js_data:
                listing['price'] = js_data['listPrice']
            
            # Extract mileage
            if 'mileage' in js_data:
                listing['mileage'] = js_data['mileage']
            elif 'odometer' in js_data:
                listing['mileage'] = js_data['odometer']
            
            # Extract location
            if 'storeCity' in js_data and 'stateAbbreviation' in js_data:
                listing['location'] = f"{js_data['storeCity']}, {js_data['stateAbbreviation']}"
            elif 'location' in js_data:
                listing['location'] = js_data['location']
            elif 'city' in js_data and 'state' in js_data:
                listing['location'] = f"{js_data['city']}, {js_data['state']}"
            
            # Extract URL
            if 'url' in js_data:
                listing['url'] = js_data['url']
            elif 'stockNumber' in js_data:
                listing['url'] = f"{self.base_url}/cars/{js_data['stockNumber']}"
            
            # Extract transmission
            if 'transmission' in js_data:
                listing['transmission'] = js_data['transmission']
            elif 'transmissionType' in js_data:
                listing['transmission'] = js_data['transmissionType']
            
            # Extract status information
            listing['is_reserved'] = js_data.get('isReserved', False)
            listing['is_saleable'] = js_data.get('isSaleable', True)
            listing['is_coming_soon'] = js_data.get('isComingSoon', False)
            
        except Exception as e:
            logger.debug(f"Error converting JS listing: {e}")
        
        return listing
    
    def scrape_listings(self) -> List[Dict]:
        """Scrape CarMax for car listings matching search parameters"""
        listings = []
        
        try:
            # First visit homepage to establish session
            logger.info("Establishing CarMax session...")
            homepage_response = self._make_request(self.base_url)
            if homepage_response:
                logger.info("Session established successfully")
                time.sleep(random.uniform(2, 4))
            else:
                logger.warning("Failed to establish session, continuing anyway...")
            
            # Try different search approaches including pagination
            search_urls = [
                self.search_url,
                f"{self.search_url}?transmission={self.transmission}" if self.transmission != 'any' else self.search_url,
                f"{self.search_url}?year={self.year_start},{self.year_end}&transmission={self.transmission}" if self.transmission != 'any' else f"{self.search_url}?year={self.year_start},{self.year_end}",
                # Try with different parameters to get more results
                f"{self.search_url}?sort=price_asc",
                f"{self.search_url}?sort=price_desc",
                f"{self.search_url}?sort=mileage_asc"
            ]
            
            for search_url in search_urls:
                logger.info(f"Searching CarMax: {search_url}")
                page_listings = self._scrape_search_page(search_url)
                listings.extend(page_listings)
                
                # Add delay between requests
                time.sleep(random.uniform(2, 4))
            
            # Remove duplicates based on URL
            seen_urls = set()
            unique_listings = []
            for listing in listings:
                if listing['url'] not in seen_urls:
                    seen_urls.add(listing['url'])
                    unique_listings.append(listing)
            
            # Filter listings based on search parameters
            filtered_listings = []
            for listing in unique_listings:
                year = listing.get('year')
                transmission = listing.get('transmission', '').lower()
                mileage = listing.get('mileage')
                price = listing.get('price')
                
                # Check year range
                valid_year = year and self.year_start <= year <= self.year_end
                
                # Check transmission filter
                transmission_match = True
                if self.transmission == 'manual':
                    transmission_match = any(keyword in transmission for keyword in ['manual', '6-speed', '6 speed', 'stick'])
                elif self.transmission == 'automatic':
                    transmission_match = any(keyword in transmission for keyword in ['automatic', 'auto'])
                # If 'any', no transmission filtering
                
                # Check mileage filter
                mileage_match = True
                if self.max_mileage and mileage:
                    mileage_match = mileage <= self.max_mileage
                
                # Check price filter
                price_match = True
                if self.max_price and price:
                    price_match = price <= self.max_price
                
                if valid_year and transmission_match and mileage_match and price_match:
                    # Add status information to the listing
                    status_parts = []
                    if listing.get('is_reserved'):
                        status_parts.append('RESERVED')
                    if not listing.get('is_saleable'):
                        status_parts.append('NOT_SALEABLE')
                    if listing.get('is_coming_soon'):
                        status_parts.append('COMING_SOON')
                    
                    status_str = ', '.join(status_parts) if status_parts else 'AVAILABLE'
                    listing['status'] = status_str
                    
                    filtered_listings.append(listing)
                    logger.info(f"Found valid {self.make} {self.model}: {listing.get('title')} - {listing.get('year')} - {listing.get('transmission')} - {status_str}")
                else:
                    logger.debug(f"Filtered out: {listing.get('title')} - Year: {year}, Transmission: {transmission}, Mileage: {mileage}, Price: {price}")
            
            logger.info(f"Found {len(filtered_listings)} {self.make} {self.model} listings ({self.year_start}-{self.year_end}) out of {len(unique_listings)} total {self.make} {self.model}s")
            return filtered_listings
            
        except Exception as e:
            logger.error(f"Error scraping CarMax: {e}")
            return []
    
    def _scrape_search_page(self, url: str) -> List[Dict]:
        """Scrape a single search page"""
        listings = []
        
        try:
            # Add random delay to appear more human-like
            time.sleep(random.uniform(1, 3))
            
            # Try multiple request strategies
            response = self._make_request(url)
            if not response:
                return listings
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # First try to parse JavaScript data (CarMax often embeds data in JS)
            js_listings = self._parse_javascript_data(response.text)
            if js_listings:
                logger.info(f"Found {len(js_listings)} listings in JavaScript data")
                for js_listing in js_listings:
                    listing = self._convert_js_listing(js_listing)
                    if listing:
                        logger.debug(f"Converted listing: {listing}")
                        if self._is_valid_listing(listing):
                            logger.info(f"Valid {self.make} {self.model} listing found: {listing.get('title', 'Unknown')}")
                            listings.append(listing)
                        else:
                            logger.debug(f"Listing failed validation: {listing.get('title', 'Unknown')}")
            
            # Also try traditional HTML parsing
            car_selectors = [
                'article[data-testid="car-tile"]',
                '.car-tile',
                '.vehicle-card',
                '[data-testid="vehicle-card"]',
                '.car-card',
                '[data-testid="car-card"]',
                '.inventory-listing'
            ]
            
            car_elements = []
            for selector in car_selectors:
                elements = soup.select(selector)
                if elements:
                    car_elements = elements
                    logger.info(f"Found {len(elements)} cars using selector: {selector}")
                    break
            
            if not car_elements:
                # Fallback: look for any elements that might contain car data
                car_elements = soup.find_all(['div', 'article'], class_=re.compile(r'car|vehicle|tile|card|listing', re.I))
                logger.info(f"Fallback search found {len(car_elements)} potential car elements")
            
            for car_element in car_elements:
                try:
                    listing = self._extract_car_data(car_element)
                    if listing and self._is_valid_listing(listing):
                        listings.append(listing)
                except Exception as e:
                    logger.debug(f"Error extracting car data: {e}")
                    continue
            
            # Check for pagination and follow all pages
            page_num = 2
            while True:
                next_page = self._find_next_page(soup, page_num)
                if not next_page:
                    break
                
                logger.info(f"Found page {page_num}: {next_page}")
                time.sleep(random.uniform(2, 4))  # Be respectful between pages
                
                next_response = self._make_request(next_page)
                if not next_response:
                    logger.warning(f"Failed to get page {page_num}")
                    break
                
                next_soup = BeautifulSoup(next_response.content, 'html.parser')
                next_js_listings = self._parse_javascript_data(next_response.text)
                
                if not next_js_listings:
                    logger.info(f"No more listings on page {page_num}")
                    break
                
                logger.info(f"Found {len(next_js_listings)} listings on page {page_num}")
                for js_listing in next_js_listings:
                    listing = self._convert_js_listing(js_listing)
                    if listing and self._is_valid_listing(listing):
                        logger.info(f"Valid {self.make} {self.model} listing found on page {page_num}: {listing.get('title', 'Unknown')}")
                        listings.append(listing)
                    else:
                        logger.debug(f"Listing failed validation on page {page_num}: {listing.get('title', 'Unknown')}")
                
                soup = next_soup  # Update soup for next iteration
                page_num += 1
                
                # Safety limit to prevent infinite loops
                if page_num > 10:
                    logger.warning("Reached page limit (10), stopping pagination")
                    break
            
        except requests.RequestException as e:
            logger.error(f"Request error scraping {url}: {e}")
        except Exception as e:
            logger.error(f"Error parsing {url}: {e}")
        
        return listings
    
    def _extract_car_data(self, car_element) -> Dict:
        """Extract car data from a car element"""
        listing = {
            'source': 'CarMax',
            'title': '',
            'price': None,
            'mileage': None,
            'location': '',
            'url': '',
            'year': None,
            'transmission': ''
        }
        
        try:
            # Extract title
            title_selectors = [
                'h3', 'h2', '.title', '.car-title', '[data-testid="car-title"]',
                '.vehicle-title', '.car-name'
            ]
            for selector in title_selectors:
                title_elem = car_element.select_one(selector)
                if title_elem:
                    listing['title'] = title_elem.get_text(strip=True)
                    break
            
            # Extract price
            price_selectors = [
                '.price', '.car-price', '[data-testid="price"]', '.vehicle-price',
                '.price-value', '.listing-price'
            ]
            for selector in price_selectors:
                price_elem = car_element.select_one(selector)
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    price_match = re.search(r'[\$]?([\d,]+)', price_text.replace(',', ''))
                    if price_match:
                        listing['price'] = int(price_match.group(1))
                    break
            
            # Extract mileage
            mileage_selectors = [
                '.mileage', '.car-mileage', '[data-testid="mileage"]', '.vehicle-mileage',
                '.odometer', '.miles'
            ]
            for selector in mileage_selectors:
                mileage_elem = car_element.select_one(selector)
                if mileage_elem:
                    mileage_text = mileage_elem.get_text(strip=True)
                    mileage_match = re.search(r'([\d,]+)', mileage_text.replace(',', ''))
                    if mileage_match:
                        listing['mileage'] = int(mileage_match.group(1))
                    break
            
            # Extract location
            location_selectors = [
                '.location', '.car-location', '[data-testid="location"]', '.vehicle-location',
                '.dealer-location', '.store-location'
            ]
            for selector in location_selectors:
                location_elem = car_element.select_one(selector)
                if location_elem:
                    listing['location'] = location_elem.get_text(strip=True)
                    break
            
            # Extract URL
            link_elem = car_element.find('a', href=True)
            if link_elem:
                href = link_elem['href']
                if href.startswith('/'):
                    listing['url'] = urljoin(self.base_url, href)
                else:
                    listing['url'] = href
            
            # Extract year from title
            if listing['title']:
                year_match = re.search(r'(20\d{2})', listing['title'])
                if year_match:
                    listing['year'] = int(year_match.group(1))
            
            # Extract transmission info
            title_lower = listing['title'].lower()
            if any(keyword in title_lower for keyword in ['manual', '6-speed', '6 speed', 'stick']):
                listing['transmission'] = 'manual'
            elif any(keyword in title_lower for keyword in ['automatic', 'auto']):
                listing['transmission'] = 'automatic'
            
        except Exception as e:
            logger.debug(f"Error extracting car data: {e}")
        
        return listing
    
    def _is_valid_listing(self, listing: Dict) -> bool:
        """Check if listing is a valid car of the specified make/model"""
        if not listing.get('title'):
            return False
        
        title_lower = listing['title'].lower()
        
        # Must contain the specified make and model
        if not (self.make.lower() in title_lower and self.model.lower() in title_lower):
            return False
        
        # Accept any car of the specified make/model - filtering happens in main logic
        return True
    
    def _find_next_page(self, soup: BeautifulSoup, page_num: int = 2) -> str:
        """Find next page URL if pagination exists"""
        # Try different pagination patterns
        next_selectors = [
            'a[aria-label="Next page"]',
            'a[aria-label="Next"]',
            '.next-page',
            '.pagination-next',
            'a:contains("Next")',
            'a:contains(">")',
            f'a:contains("{page_num}")',
            f'[data-page="{page_num}"]'
        ]
        
        for selector in next_selectors:
            next_elem = soup.select_one(selector)
            if next_elem and next_elem.get('href'):
                href = next_elem['href']
                if href.startswith('/'):
                    return urljoin(self.base_url, href)
                return href
        
        # Try to construct page URL manually
        # Look for current URL and try to modify it for next page
        current_url = None
        for link in soup.find_all('a', href=True):
            href = link['href']
            if f'carmax.com/cars/{self.make.lower()}/{self.model.lower()}' in href and 'page=' in href:
                # Extract base URL and increment page number
                base_url = href.split('page=')[0]
                return f"{base_url}page={page_num}"
        
        # Try common pagination patterns
        base_search_urls = [
            f"{self.search_url}?page={page_num}",
            f"{self.search_url}?p={page_num}",
            f"{self.search_url}?pageNumber={page_num}"
        ]
        
        # Return the first pattern to try
        return base_search_urls[0] if page_num <= 10 else None
