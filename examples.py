from ebay_scraper import EbayScraper
import time

def example_basic_search():
    """Example 1: Basic search"""
    print("=== Example 1: Basic Search ===")
    scraper = EbayScraper()
    
    items = scraper.search_and_scrape(
        keyword="wireless earbuds",
        max_pages=2
    )
    
    # Show results
    print(f"Found {len(items)} items")
    for i, item in enumerate(items[:3]):  # Show first 3
        print(f"\n{i+1}. {item['title'][:60]}...")
        print(f"   Price: {item['price_text']}")
        print(f"   Shipping: {item['shipping']}")
    
    # Save results
    scraper.save_to_csv(items, 'data/wireless_earbuds.csv')
    return items

def example_filtered_search():
    """Example 2: Search with filters"""
    print("\n=== Example 2: Filtered Search ===")
    scraper = EbayScraper()
    
    items = scraper.search_and_scrape(
        keyword="laptop",
        condition="Used",
        price_min=300,
        price_max=800,
        sort_order="PricePlusShippingLowest",
        max_pages=2
    )
    
    print(f"Found {len(items)} used laptops between $300-$800")
    
    # Show cheapest items
    sorted_items = sorted([item for item in items if item['price']], 
                         key=lambda x: x['price'])
    
    for i, item in enumerate(sorted_items[:3]):
        print(f"\n{i+1}. {item['title'][:60]}...")
        print(f"   Price: ${item['price']:.2f}")
        print(f"   Condition: {item['condition']}")
    
    scraper.save_to_csv(items, 'data/used_laptops.csv')
    return items

if __name__ == "__main__":
    print("Running eBay Scraper Examples...\n")
    
    # Run examples
    example_basic_search()
    time.sleep(2)  # Brief pause between examples
    example_filtered_search()
    
    print("\n✓ Examples completed! Check the 'data' folder for CSV files.")