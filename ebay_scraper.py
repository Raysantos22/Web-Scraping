import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
from urllib.parse import urlencode, quote_plus
import re
import json
from datetime import datetime

class EbayScraper:
    def __init__(self):
        self.base_url = "https://www.ebay.com/sch/i.html"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def build_search_url(self, keyword, category=None, condition=None, price_min=None, price_max=None, sort_order=None):
        """Build eBay search URL with parameters"""
        params = {
            '_nkw': keyword,
            '_sacat': '0',  # All categories
            '_from': 'R40',  # Search results
            '_trksid': 'p2334524.m570.l1313',  # Track search
            '_odkw': '',  # Previous search
            '_osacat': '0'  # All categories
        }
        
        if category:
            params['_sacat'] = category
            
        if condition:
            condition_map = {
                'New': '1000',
                'Used': '3000', 
                'Refurbished': '2000'
            }
            if condition in condition_map:
                params['LH_ItemCondition'] = condition_map[condition]
        
        if price_min:
            params['_udlo'] = str(price_min)
            
        if price_max:
            params['_udhi'] = str(price_max)
            
        if sort_order:
            sort_map = {
                'BestMatch': '12',
                'PricePlusShipping': '15',
                'PricePlusShippingLowest': '16', 
                'EndTimeSoonest': '1',
                'NewestFirst': '10',
                'MostWatched': '7'
            }
            if sort_order in sort_map:
                params['_sop'] = sort_map[sort_order]
        
        return f"{self.base_url}?{urlencode(params)}"

    def extract_price(self, price_text):
        """Extract numeric price from price string"""
        if not price_text:
            return None
        
        # Handle price ranges like "$20.00 to $30.00"
        if 'to' in price_text.lower():
            prices = re.findall(r'[\d,]+\.?\d*', price_text.replace(',', ''))
            if prices:
                try:
                    return float(prices[0])  # Return the lower price
                except ValueError:
                    return None
        
        # Single price
        price_match = re.search(r'[\d,]+\.?\d*', price_text.replace(',', ''))
        if price_match:
            try:
                return float(price_match.group())
            except ValueError:
                return None
        return None

    def get_item_specifics(self, item_container):
        """Extract additional item details like brand, model, etc."""
        specifics = {}
        
        try:
            # Look for item specifics in various places
            specific_elements = item_container.find_all('span', class_='s-item__detail')
            for elem in specific_elements:
                text = elem.get_text(strip=True)
                if 'Brand:' in text:
                    specifics['brand'] = text.replace('Brand:', '').strip()
                elif 'Model:' in text:
                    specifics['model'] = text.replace('Model:', '').strip()
        except:
            pass
        
        return specifics

    def scrape_search_results(self, url, max_pages=3):
        """Scrape eBay search results with enhanced extraction"""
        all_items = []
        
        for page in range(1, max_pages + 1):
            print(f"Scraping page {page}...")
            
            # Add page parameter
            page_url = f"{url}&_pgn={page}"
            
            try:
                # Random delay
                time.sleep(random.uniform(2, 4))
                
                response = self.session.get(page_url)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Multiple selectors to find items - Enhanced approach
                items = []
                
                # Try different item container selectors with priority order
                selectors = [
                    'div.s-item__wrapper',
                    'div.s-item',
                    '.srp-results .s-item',
                    '[data-testid="item-card"]',
                    '.srp-river-results .s-item',
                    '.s-item__info'
                ]
                
                for selector in selectors:
                    found_items = soup.select(selector)
                    if found_items and len(found_items) > 5:  # Must find reasonable number of items
                        items = found_items
                        print(f"Found {len(items)} items using selector: {selector}")
                        break
                
                if not items:
                    print(f"No items found on page {page} - trying backup method")
                    # Fallback: look for any div containing item-related data
                    items = soup.find_all('div', {'class': lambda x: x and any(
                        keyword in x.lower() for keyword in ['s-item', 'item', 'listing']
                    )})
                
                page_items = []
                for i, item in enumerate(items[:60]):  # Limit per page to avoid overload
                    try:
                        item_data = self.extract_enhanced_item_data(item)
                        if item_data and self.is_valid_item(item_data):
                            all_items.append(item_data)
                            page_items.append(item_data)
                            print(f"✓ Extracted: {item_data.get('title', 'Unknown')[:50]}...")
                    except Exception as e:
                        print(f"Error extracting item {i}: {e}")
                        continue
                
                print(f"Found {len(page_items)} valid items on page {page}")
                
                if len(page_items) == 0:
                    print("No valid items found, trying next page...")
                    if page == 1:  # If first page fails, continue to see if other pages work
                        continue
                    else:
                        break
                
            except requests.RequestException as e:
                print(f"Error fetching page {page}: {e}")
                break
        
        return all_items

    def extract_enhanced_item_data(self, item):
        """Enhanced item data extraction with multiple fallback methods"""
        try:
            data = {}
            
            # Title extraction with multiple selectors
            title = self.extract_title(item)
            if not title or title in ['N/A', '', 'Shop on eBay', 'Opens in a new window or tab']:
                return None
            
            data['title'] = title
            
            # Price extraction
            price_text, price = self.extract_price_info(item)
            data['price'] = price
            data['price_text'] = price_text
            
            # Shipping
            data['shipping'] = self.extract_shipping(item)
            
            # Condition
            data['condition'] = self.extract_condition(item)
            
            # Location
            data['location'] = self.extract_location(item)
            
            # Seller
            data['seller'] = self.extract_seller(item)
            
            # Link
            data['link'] = self.extract_link(item)
            
            # Image
            data['image_url'] = self.extract_image(item)
            
            # Additional enhanced details
            data['watchers'] = self.extract_watchers(item)
            data['sold_count'] = self.extract_sold_count(item)
            data['time_left'] = self.extract_time_left(item)
            data['buy_it_now'] = self.extract_buy_it_now(item)
            data['free_shipping'] = self.check_free_shipping(item)
            data['best_offer'] = self.check_best_offer(item)
            data['auction'] = self.check_auction(item)
            
            # Item specifics
            specifics = self.get_item_specifics(item)
            data.update(specifics)
            
            # Add timestamp
            data['scraped_at'] = datetime.now().isoformat()
            
            return data
            
        except Exception as e:
            print(f"Error in enhanced extraction: {e}")
            return None

    def extract_title(self, item):
        """Extract title with multiple fallback methods"""
        selectors = [
            'h3.s-item__title',
            'h3[role="heading"]',
            '.s-item__title',
            'a.s-item__link',
            'h3',
            '.x-item-title-label h3',
            '[data-testid="item-title"]'
        ]
        
        for selector in selectors:
            elem = item.select_one(selector)
            if elem:
                title = elem.get_text(strip=True)
                # Filter out unwanted titles
                unwanted = ['shop on ebay', 'opens in new window or tab', 'n/a', '', 'ebay']
                if title and title.lower() not in unwanted and len(title) > 10:
                    # Remove "New Listing" prefix if present
                    title = re.sub(r'^(New Listing[:\-\s]*)', '', title, flags=re.IGNORECASE)
                    return title.strip()
        
        return None

    def extract_price_info(self, item):
        """Extract price information with enhanced detection"""
        selectors = [
            '.s-item__price .notranslate',
            '.s-item__price',
            '.notranslate',
            '[data-testid="price"]',
            '.u-flL.condText',
            'span.s-item__price',
            '.price .notranslate'
        ]
        
        for selector in selectors:
            elem = item.select_one(selector)
            if elem:
                price_text = elem.get_text(strip=True)
                if price_text and any(symbol in price_text for symbol in ['$', '£', '€', '¥']):
                    return price_text, self.extract_price(price_text)
        
        return 'N/A', None

    def extract_shipping(self, item):
        """Extract shipping information"""
        selectors = [
            '.s-item__shipping',
            '.s-item__freeXDays',
            '[data-testid="shipping-cost"]',
            '.s-item__detail--primary'
        ]
        
        for selector in selectors:
            elem = item.select_one(selector)
            if elem:
                shipping = elem.get_text(strip=True)
                if 'shipping' in shipping.lower() or 'free' in shipping.lower():
                    return shipping
        
        return 'N/A'

    def extract_condition(self, item):
        """Extract item condition"""
        selectors = [
            '.s-item__subtitle .SECONDARY_INFO',
            '.s-item__subtitle',
            '.SECONDARY_INFO',
            '[data-testid="item-condition"]',
            '.s-item__condition'
        ]
        
        for selector in selectors:
            elem = item.select_one(selector)
            if elem:
                condition = elem.get_text(strip=True)
                # Check if it's actually a condition
                condition_keywords = ['new', 'used', 'refurbished', 'open box', 'pre-owned', 'brand new']
                if any(keyword in condition.lower() for keyword in condition_keywords):
                    return condition
        
        return 'N/A'

    def extract_location(self, item):
        """Extract seller location"""
        selectors = [
            '.s-item__location',
            '.s-item__itemLocation',
            '[data-testid="item-location"]'
        ]
        
        for selector in selectors:
            elem = item.select_one(selector)
            if elem:
                location = elem.get_text(strip=True)
                # Filter out non-location text
                if location and len(location) > 2 and not location.startswith('From'):
                    return location
        
        return 'N/A'

    def extract_seller(self, item):
        """Extract seller information"""
        selectors = [
            '.s-item__seller-info-text',
            '.s-item__seller',
            '[data-testid="seller-name"]'
        ]
        
        for selector in selectors:
            elem = item.select_one(selector)
            if elem:
                return elem.get_text(strip=True)
        
        return 'N/A'

    def extract_link(self, item):
        """Extract item link"""
        selectors = [
            'a.s-item__link',
            'h3 a',
            'a[href*="/itm/"]',
            'a[href*="ebay.com"]'
        ]
        
        for selector in selectors:
            elem = item.select_one(selector)
            if elem and elem.get('href'):
                href = elem.get('href')
                if href.startswith('http'):
                    return href
                elif href.startswith('/'):
                    return f"https://www.ebay.com{href}"
        
        return 'N/A'

    def extract_image(self, item):
        """Extract product image with better quality detection"""
        selectors = [
            '.s-item__image img',
            'img.s-item__image',
            'img[src*="ebayimg"]',
            'img[data-src*="ebayimg"]',
            'img[src*="i.ebayimg.com"]'
        ]
        
        for selector in selectors:
            elem = item.select_one(selector)
            if elem:
                # Try src first, then data-src
                img_url = elem.get('src') or elem.get('data-src')
                if img_url and 'ebayimg.com' in img_url:
                    # Try to get higher quality version
                    if 's-l' in img_url:
                        # Replace with higher quality
                        img_url = img_url.replace('s-l64', 's-l300').replace('s-l140', 's-l300')
                    return img_url
        
        return 'N/A'

    def extract_watchers(self, item):
        """Extract number of watchers"""
        text_content = item.get_text()
        watchers_match = re.search(r'(\d+)\s*watchers?', text_content, re.IGNORECASE)
        if watchers_match:
            return int(watchers_match.group(1))
        return 0

    def extract_sold_count(self, item):
        """Extract sold count"""
        text_content = item.get_text()
        sold_match = re.search(r'(\d+)\s*sold', text_content, re.IGNORECASE)
        if sold_match:
            return int(sold_match.group(1))
        return 0

    def extract_time_left(self, item):
        """Extract time left for auction items"""
        selectors = ['.s-item__time-left', '.s-item__timeLeft', '.s-item__time']
        
        for selector in selectors:
            elem = item.select_one(selector)
            if elem:
                time_left = elem.get_text(strip=True)
                if any(word in time_left.lower() for word in ['day', 'hour', 'minute', 'second']):
                    return time_left
        
        return 'N/A'

    def extract_buy_it_now(self, item):
        """Check if item has Buy It Now option"""
        bin_indicators = ['.s-item__purchase-options', '.s-item__buyItNowOption', 'Buy It Now']
        
        for indicator in bin_indicators:
            if indicator.startswith('.'):
                elem = item.select_one(indicator)
                if elem:
                    return True
            else:
                if indicator in item.get_text():
                    return True
        
        return False

    def check_free_shipping(self, item):
        """Check if item has free shipping"""
        text_content = item.get_text().lower()
        return 'free shipping' in text_content or 'free postage' in text_content

    def check_best_offer(self, item):
        """Check if item accepts best offers"""
        text_content = item.get_text().lower()
        return 'best offer' in text_content or 'make offer' in text_content

    def check_auction(self, item):
        """Check if item is an auction"""
        text_content = item.get_text().lower()
        return any(word in text_content for word in ['bid', 'auction', 'time left'])

    def is_valid_item(self, item_data):
        """Enhanced validation for extracted item data"""
        if not item_data:
            return False
        
        title = item_data.get('title', '')
        
        # Filter out invalid/promotional titles
        invalid_patterns = [
            r'^shop on ebay',
            r'^opens in new',
            r'^ebay$',
            r'^advertisement',
            r'^sponsored',
            r'^\s*$'
        ]
        
        for pattern in invalid_patterns:
            if re.match(pattern, title.lower().strip()):
                return False
        
        # Must have meaningful title and at least price OR link
        if len(title.strip()) < 10:
            return False
        
        has_price = item_data.get('price') is not None and item_data.get('price') > 0
        has_link = item_data.get('link') != 'N/A'
        
        return has_price or has_link

    def save_to_csv(self, items, filename='ebay_results.csv'):
        """Save scraped data to CSV file with enhanced formatting"""
        if not items:
            print("No items to save")
            return
        
        # Ensure data directory exists
        import os
        os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else '.', exist_ok=True)
        
        df = pd.DataFrame(items)
        
        # Reorder columns for better CSV layout
        preferred_order = [
            'title', 'price', 'price_text', 'condition', 'shipping', 
            'location', 'seller', 'watchers', 'sold_count', 'time_left',
            'buy_it_now', 'free_shipping', 'best_offer', 'auction',
            'link', 'image_url', 'brand', 'model', 'scraped_at'
        ]
        
        # Reorder columns that exist
        existing_cols = [col for col in preferred_order if col in df.columns]
        remaining_cols = [col for col in df.columns if col not in preferred_order]
        final_order = existing_cols + remaining_cols
        
        df = df[final_order]
        df.to_csv(filename, index=False, encoding='utf-8')
        print(f"Saved {len(items)} items to {filename}")

    def search_and_scrape(self, keyword, max_pages=3, **kwargs):
        """Main method to search and scrape eBay with enhanced output"""
        print(f"🚀 Starting Enhanced eBay scrape for: '{keyword}'")
        
        # Build search URL
        url = self.build_search_url(keyword, **kwargs)
        print(f"🔗 Search URL: {url}")
        
        # Scrape results
        items = self.scrape_search_results(url, max_pages)
        
        if not items:
            print("❌ No valid items found. Try different search terms or check your connection.")
            return []
        
        print(f"✅ Total valid items scraped: {len(items)}")
        
        # Enhanced results summary
        self.print_results_summary(items)
        
        return items

    def print_results_summary(self, items):
        """Print enhanced summary of scraped results"""
        if not items:
            return
        
        print(f"\n{'='*60}")
        print(f"📊 SCRAPING RESULTS SUMMARY")
        print(f"{'='*60}")
        
        # Basic stats
        total_items = len(items)
        items_with_price = [item for item in items if item.get('price')]
        
        if items_with_price:
            prices = [item['price'] for item in items_with_price]
            avg_price = sum(prices) / len(prices)
            min_price = min(prices)
            max_price = max(prices)
            
            print(f"💰 Price Analysis:")
            print(f"   Average: ${avg_price:.2f}")
            print(f"   Range: ${min_price:.2f} - ${max_price:.2f}")
            print(f"   Items with price: {len(items_with_price)}/{total_items}")
        
        # Condition analysis
        conditions = {}
        for item in items:
            condition = item.get('condition', 'N/A')
            conditions[condition] = conditions.get(condition, 0) + 1
        
        if len(conditions) > 1:
            print(f"\n🏷️  Condition Breakdown:")
            for condition, count in sorted(conditions.items(), key=lambda x: x[1], reverse=True):
                percentage = (count/total_items)*100
                print(f"   {condition}: {count} ({percentage:.1f}%)")
        
        # Hot items
        hot_items = [item for item in items if item.get('watchers', 0) > 5 or item.get('sold_count', 0) > 10]
        if hot_items:
            print(f"\n🔥 Hot Items ({len(hot_items)} found):")
            for item in hot_items[:3]:
                watchers = item.get('watchers', 0)
                sold = item.get('sold_count', 0)
                print(f"   • {item['title'][:50]}...")
                print(f"     Price: {item['price_text']} | Watchers: {watchers} | Sold: {sold}")
        
        # Sample results
        print(f"\n📦 Sample Results:")
        for i, item in enumerate(items[:3]):
            print(f"\n{i+1}. {item['title'][:60]}...")
            print(f"   💰 {item['price_text']} | 🚚 {item['shipping']}")
            print(f"   📍 {item['location']} | ✨ {item['condition']}")
            if item.get('watchers', 0) > 0:
                print(f"   👀 {item['watchers']} watchers")
            if item.get('sold_count', 0) > 0:
                print(f"   📦 {item['sold_count']} sold")

# Example usage with enhanced features
if __name__ == "__main__":
    # Initialize enhanced scraper
    scraper = EbayScraper()
    
    print("🎯 Testing Enhanced eBay Scraper...")
    
    # Example: Search for trending items
    items = scraper.search_and_scrape(
        keyword="iPhone 15 Pro Max",
        condition="New",
        sort_order="MostWatched",
        max_pages=2,
        price_min=800,
        price_max=1500
    )
    
    if items:
        # Save with timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"data/iphone_15_pro_max_{timestamp}.csv"
        scraper.save_to_csv(items, filename)
        
        print(f"\n🎉 Scraping completed! Check '{filename}' for full results.")
    else:
        print("❌ No results found. Try a different search term.")