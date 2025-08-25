from ebay_scraper import EbayScraper

def test_basic_functionality():
    """Test basic scraper functionality"""
    print("Testing eBay Scraper...")
    
    try:
        # Initialize scraper
        scraper = EbayScraper()
        print("✓ Scraper initialized successfully")
        
        # Test URL building
        url = scraper.build_search_url("test item")
        print(f"✓ URL building works: {url[:50]}...")
        
        # Test basic search (just 1 item to be quick)
        print("Testing basic search...")
        items = scraper.search_and_scrape("phone case", max_pages=1)
        
        if items:
            print(f"✓ Successfully scraped {len(items)} items")
            print(f"✓ Sample item: {items[0]['title'][:50]}...")
            return True
        else:
            print("✗ No items found")
            return False
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

if __name__ == "__main__":
    test_basic_functionality()