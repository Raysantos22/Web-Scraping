# C:\Users\ADMIN\ebay-scraper\ebay_scraper.py

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
from urllib.parse import urlencode, quote_plus
import re
import json
from datetime import datetime
import threading

class EbayScraper:
    def __init__(self):
        self.base_url = "https://www.ebay.com/sch/i.html"
        self.trending_urls = {
            'most_watched': 'https://www.ebay.com/sch/i.html?_sop=7&_nkw=*',  # Most watched
            'ending_soon': 'https://www.ebay.com/sch/i.html?_sop=1&_nkw=*',   # Ending soon
            'newly_listed': 'https://www.ebay.com/sch/i.html?_sop=10&_nkw=*', # Newly listed
            'best_selling': 'https://www.ebay.com/sch/i.html?_sop=12&LH_Sold=1&_nkw=*', # Best selling
        }
        
        # Popular categories for trending items
        self.trending_categories = {
            'Electronics': '293',
            'Fashion': '11450', 
            'Home & Garden': '11700',
            'Collectibles': '1',
            'Motors': '6000',
            'Sports': '888',
            'Health & Beauty': '26395',
            'Toys': '220',
            'Business': '12576',
            'Music': '11233'
        }
        
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
            '_from': 'R40',
            '_trksid': 'p2334524.m570.l1313'
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

    def build_trending_url(self, trend_type, category=None, price_min=None, price_max=None):
        """Build URL for trending items discovery"""
        base_params = {
            '_from': 'R40',
            '_trksid': 'p2334524.m570.l1313'
        }
        
        # Add trending-specific parameters
        if trend_type == 'most_watched':
            base_params.update({
                '_sop': '7',  # Sort by most watched
                '_nkw': '*'   # All items
            })
        elif trend_type == 'ending_soon':
            base_params.update({
                '_sop': '1',  # Sort by ending soonest
                '_nkw': '*',
                'LH_Auction': '1'  # Auctions only
            })
        elif trend_type == 'newly_listed':
            base_params.update({
                '_sop': '10',  # Sort by newly listed
                '_nkw': '*'
            })
        elif trend_type == 'best_selling':
            base_params.update({
                '_sop': '12',  # Best match (but with sold filter)
                'LH_Sold': '1',  # Sold listings
                '_nkw': '*'
            })
        elif trend_type == 'hot_deals':
            base_params.update({
                '_sop': '16',  # Price + shipping lowest
                '_nkw': '*',
                'LH_BIN': '1',  # Buy it now
                'rt': 'nc'      # New condition
            })
        
        # Add category filter
        if category and category in self.trending_categories:
            base_params['_sacat'] = self.trending_categories[category]
        else:
            base_params['_sacat'] = '0'  # All categories
        
        # Add price filters
        if price_min:
            base_params['_udlo'] = str(price_min)
        if price_max:
            base_params['_udhi'] = str(price_max)
            
        return f"{self.base_url}?{urlencode(base_params)}"

    def scrape_trending_items(self, trend_type='most_watched', category=None, max_pages=5, price_min=None, price_max=None):
        """Scrape trending/fast-moving items from eBay"""
        print(f"🔥 Discovering {trend_type.replace('_', ' ').title()} items...")
        
        url = self.build_trending_url(trend_type, category, price_min, price_max)
        print(f"🔗 Trending URL: {url}")
        
        return self.scrape_search_results(url, max_pages)

    def scrape_all_trending_categories(self, trend_type='most_watched', max_pages=3, price_min=None, price_max=None):
        """Scrape trending items from ALL categories"""
        print(f"🌟 Scraping {trend_type.replace('_', ' ').title()} items from ALL categories...")
        print("This will take longer but get you EVERYTHING trending!")
        
        all_trending_items = []
        
        # Scrape each category
        for category_name, category_id in self.trending_categories.items():
            print(f"\n📂 Scraping {category_name} category...")
            
            try:
                # Build category-specific trending URL
                url = self.build_trending_url(trend_type, category_name, price_min, price_max)
                category_items = self.scrape_search_results(url, max_pages)
                
                # Add category info to each item
                for item in category_items:
                    item['category'] = category_name
                    item['trend_type'] = trend_type
                
                all_trending_items.extend(category_items)
                print(f"✅ Found {len(category_items)} trending items in {category_name}")
                
                # Small delay between categories
                time.sleep(random.uniform(2, 4))
                
            except Exception as e:
                print(f"❌ Error scraping {category_name}: {e}")
                continue
        
        print(f"\n🎉 Total trending items found: {len(all_trending_items)}")
        return all_trending_items

    def scrape_multiple_trending_types(self, max_pages=3, categories=None):
        """Scrape multiple types of trending items at once"""
        print("🚀 Scraping ALL types of trending items...")
        
        trending_types = ['most_watched', 'ending_soon', 'newly_listed', 'best_selling']
        all_items = []
        
        for trend_type in trending_types:
            print(f"\n{'='*50}")
            print(f"🔍 Now scraping: {trend_type.replace('_', ' ').title()}")
            print('='*50)
            
            if categories:
                # Scrape specific categories
                for category in categories:
                    items = self.scrape_trending_items(trend_type, category, max_pages)
                    for item in items:
                        item['category'] = category
                        item['trend_type'] = trend_type
                    all_items.extend(items)
            else:
                # Scrape all categories
                items = self.scrape_all_trending_categories(trend_type, max_pages)
                all_items.extend(items)
        
        return all_items

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

    def scrape_search_results(self, url, max_pages=3):
        """Scrape eBay search results with enhanced extraction"""
        all_items = []
        
        for page in range(1, max_pages + 1):
            print(f"   📄 Scraping page {page}...")
            
            # Add page parameter
            page_url = f"{url}&_pgn={page}"
            
            try:
                # Random delay
                time.sleep(random.uniform(2, 4))
                
                response = self.session.get(page_url)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Multiple selectors to find items
                items = []
                selectors = [
                    'div.s-item__wrapper',
                    'div.s-item',
                    '.srp-results .s-item',
                    '[data-testid="item-card"]',
                    '.srp-river-results .s-item'
                ]
                
                for selector in selectors:
                    found_items = soup.select(selector)
                    if found_items and len(found_items) > 5:
                        items = found_items
                        break
                
                page_items = []
                for i, item in enumerate(items[:60]):
                    try:
                        item_data = self.extract_enhanced_item_data(item)
                        if item_data and self.is_valid_item(item_data):
                            # Filter for truly trending items
                            if self.is_trending_item(item_data):
                                all_items.append(item_data)
                                page_items.append(item_data)
                    except Exception as e:
                        continue
                
                print(f"   ✅ Found {len(page_items)} trending items on page {page}")
                
                if len(page_items) == 0 and page > 1:
                    break
                
            except requests.RequestException as e:
                print(f"   ❌ Error fetching page {page}: {e}")
                break
        
        return all_items

    def is_trending_item(self, item_data):
        """Check if an item is truly trending/fast-moving"""
        # Must have watchers OR sold count OR ending soon
        has_watchers = item_data.get('watchers', 0) > 2
        has_sales = item_data.get('sold_count', 0) > 5
        ending_soon = item_data.get('time_left', 'N/A') != 'N/A'
        has_price = item_data.get('price', 0) > 0
        
        # At least one trending indicator + valid price
        return (has_watchers or has_sales or ending_soon) and has_price

    def extract_enhanced_item_data(self, item):
        """Enhanced item data extraction"""
        try:
            data = {}
            
            # Title
            title = self.extract_title(item)
            if not title:
                return None
            data['title'] = title
            
            # Price
            price_text, price = self.extract_price_info(item)
            data['price'] = price
            data['price_text'] = price_text
            
            # Basic details
            data['shipping'] = self.extract_shipping(item)
            data['condition'] = self.extract_condition(item)
            data['location'] = self.extract_location(item)
            data['seller'] = self.extract_seller(item)
            data['link'] = self.extract_link(item)
            data['image_url'] = self.extract_image(item)
            
            # Trending indicators
            data['watchers'] = self.extract_watchers(item)
            data['sold_count'] = self.extract_sold_count(item)
            data['time_left'] = self.extract_time_left(item)
            data['buy_it_now'] = self.extract_buy_it_now(item)
            data['free_shipping'] = self.check_free_shipping(item)
            data['best_offer'] = self.check_best_offer(item)
            data['auction'] = self.check_auction(item)
            
            # Calculate trending score
            data['trending_score'] = self.calculate_trending_score(data)
            
            data['scraped_at'] = datetime.now().isoformat()
            
            return data
            
        except Exception as e:
            return None

    def calculate_trending_score(self, item_data):
        """Calculate a trending score for sorting"""
        score = 0
        
        # Watchers contribute to score
        watchers = item_data.get('watchers', 0)
        score += watchers * 2
        
        # Sold count contributes more
        sold_count = item_data.get('sold_count', 0)
        score += sold_count * 3
        
        # Ending soon adds urgency
        if item_data.get('time_left', 'N/A') != 'N/A':
            score += 10
            
        # Free shipping adds appeal
        if item_data.get('free_shipping'):
            score += 5
            
        # Best offer adds flexibility
        if item_data.get('best_offer'):
            score += 3
        
        return score

    # Include all the extraction methods from the previous scraper
    def extract_title(self, item):
        """Extract title with multiple fallback methods"""
        selectors = [
            'h3.s-item__title',
            'h3[role="heading"]',
            '.s-item__title',
            'a.s-item__link',
            'h3'
        ]
        
        for selector in selectors:
            elem = item.select_one(selector)
            if elem:
                title = elem.get_text(strip=True)
                unwanted = ['shop on ebay', 'opens in new window or tab', 'n/a', '', 'ebay']
                if title and title.lower() not in unwanted and len(title) > 10:
                    title = re.sub(r'^(New Listing[:\-\s]*)', '', title, flags=re.IGNORECASE)
                    return title.strip()
        return None

    def extract_price_info(self, item):
        """Extract price information"""
        selectors = [
            '.s-item__price .notranslate',
            '.s-item__price',
            '.notranslate'
        ]
        
        for selector in selectors:
            elem = item.select_one(selector)
            if elem:
                price_text = elem.get_text(strip=True)
                if price_text and '$' in price_text:
                    return price_text, self.extract_price(price_text)
        return 'N/A', None

    def extract_shipping(self, item):
        """Extract shipping information"""
        elem = item.select_one('.s-item__shipping')
        return elem.get_text(strip=True) if elem else 'N/A'

    def extract_condition(self, item):
        """Extract item condition"""
        elem = item.select_one('.s-item__subtitle')
        if elem:
            condition = elem.get_text(strip=True)
            condition_keywords = ['new', 'used', 'refurbished', 'open box', 'pre-owned']
            if any(keyword in condition.lower() for keyword in condition_keywords):
                return condition
        return 'N/A'

    def extract_location(self, item):
        """Extract seller location"""
        elem = item.select_one('.s-item__location')
        return elem.get_text(strip=True) if elem else 'N/A'

    def extract_seller(self, item):
        """Extract seller information"""
        elem = item.select_one('.s-item__seller-info-text')
        return elem.get_text(strip=True) if elem else 'N/A'

    def extract_link(self, item):
        """Extract item link"""
        elem = item.select_one('a.s-item__link')
        if elem and elem.get('href'):
            href = elem.get('href')
            return href if href.startswith('http') else f"https://www.ebay.com{href}"
        return 'N/A'

    def extract_image(self, item):
        """Extract product image"""
        elem = item.select_one('.s-item__image img')
        if elem:
            img_url = elem.get('src') or elem.get('data-src')
            if img_url and 'ebayimg.com' in img_url:
                return img_url.replace('s-l64', 's-l300').replace('s-l140', 's-l300')
        return 'N/A'

    def extract_watchers(self, item):
        """Extract number of watchers"""
        text_content = item.get_text()
        watchers_match = re.search(r'(\d+)\s*watchers?', text_content, re.IGNORECASE)
        return int(watchers_match.group(1)) if watchers_match else 0

    def extract_sold_count(self, item):
        """Extract sold count"""
        text_content = item.get_text()
        sold_match = re.search(r'(\d+)\s*sold', text_content, re.IGNORECASE)
        return int(sold_match.group(1)) if sold_match else 0

    def extract_time_left(self, item):
        """Extract time left for auction items"""
        elem = item.select_one('.s-item__time-left')
        if elem:
            time_left = elem.get_text(strip=True)
            if any(word in time_left.lower() for word in ['day', 'hour', 'minute']):
                return time_left
        return 'N/A'

    def extract_buy_it_now(self, item):
        """Check if item has Buy It Now option"""
        return 'Buy It Now' in item.get_text()

    def check_free_shipping(self, item):
        """Check if item has free shipping"""
        return 'free shipping' in item.get_text().lower()

    def check_best_offer(self, item):
        """Check if item accepts best offers"""
        return 'best offer' in item.get_text().lower()

    def check_auction(self, item):
        """Check if item is an auction"""
        text = item.get_text().lower()
        return any(word in text for word in ['bid', 'auction', 'time left'])

    def is_valid_item(self, item_data):
        """Validate extracted item data"""
        if not item_data:
            return False
        
        title = item_data.get('title', '')
        if len(title.strip()) < 10:
            return False
            
        has_price = item_data.get('price') is not None and item_data.get('price') > 0
        return has_price

    def save_to_csv(self, items, filename='trending_items.csv'):
        """Save trending items to CSV with enhanced formatting"""
        if not items:
            print("No items to save")
            return
        
        import os
        os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else '.', exist_ok=True)
        
        # Sort by trending score
        items.sort(key=lambda x: x.get('trending_score', 0), reverse=True)
        
        df = pd.DataFrame(items)
        
        # Preferred column order for trending analysis
        preferred_order = [
            'title', 'price', 'price_text', 'trending_score', 'watchers', 'sold_count', 
            'time_left', 'condition', 'category', 'trend_type', 'shipping', 'location', 
            'seller', 'buy_it_now', 'free_shipping', 'best_offer', 'auction',
            'link', 'image_url', 'scraped_at'
        ]
        
        existing_cols = [col for col in preferred_order if col in df.columns]
        remaining_cols = [col for col in df.columns if col not in preferred_order]
        final_order = existing_cols + remaining_cols
        
        df = df[final_order]
        df.to_csv(filename, index=False, encoding='utf-8')
        print(f"💾 Saved {len(items)} trending items to {filename}")

    def search_and_scrape(self, keyword, max_pages=3, **kwargs):
        """Regular search functionality"""
        print(f"🔍 Searching for: '{keyword}'")
        url = self.build_search_url(keyword, **kwargs)
        return self.scrape_search_results(url, max_pages)

    def get_trending_summary(self, items):
        """Generate summary of trending items"""
        if not items:
            return
            
        print(f"\n{'='*60}")
        print(f"🔥 TRENDING ITEMS SUMMARY")
        print(f"{'='*60}")
        
        total_items = len(items)
        print(f"📊 Total trending items found: {total_items}")
        
        # Category breakdown
        if any('category' in item for item in items):
            categories = {}
            for item in items:
                cat = item.get('category', 'Unknown')
                categories[cat] = categories.get(cat, 0) + 1
            
            print(f"\n📂 Category Breakdown:")
            for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
                print(f"   {cat}: {count} items")
        
        # Trending type breakdown
        if any('trend_type' in item for item in items):
            trend_types = {}
            for item in items:
                trend = item.get('trend_type', 'Unknown')
                trend_types[trend] = trend_types.get(trend, 0) + 1
            
            print(f"\n🔥 Trending Type Breakdown:")
            for trend, count in trend_types.items():
                print(f"   {trend.replace('_', ' ').title()}: {count} items")
        
        # Price analysis
        items_with_price = [item for item in items if item.get('price')]
        if items_with_price:
            prices = [item['price'] for item in items_with_price]
            print(f"\n💰 Price Analysis:")
            print(f"   Average: ${sum(prices)/len(prices):.2f}")
            print(f"   Range: ${min(prices):.2f} - ${max(prices):.2f}")
        
        # Top trending items
        top_items = sorted(items, key=lambda x: x.get('trending_score', 0), reverse=True)[:5]
        print(f"\n⭐ Top 5 Trending Items:")
        for i, item in enumerate(top_items):
            print(f"{i+1}. {item['title'][:50]}...")
            print(f"   💰 {item['price_text']} | 👀 {item.get('watchers', 0)} | 📦 {item.get('sold_count', 0)}")
            print(f"   🏆 Trending Score: {item.get('trending_score', 0)}")

# Example usage
if __name__ == "__main__":
    scraper = EbayScraper()
    
    print("🚀 eBay Trending Items Scraper")
    print("Choose an option:")
    print("1. Scrape ALL trending items (most comprehensive)")
    print("2. Scrape specific trending type")
    print("3. Search for specific products")
    
    # For demo, let's scrape most watched items
    trending_items = scraper.scrape_trending_items(
        trend_type='most_watched',
        category='Electronics',
        max_pages=3
    )
    
    if trending_items:
        scraper.get_trending_summary(trending_items)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"data/trending_items_{timestamp}.csv"
        scraper.save_to_csv(trending_items, filename)