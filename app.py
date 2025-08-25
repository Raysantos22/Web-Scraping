from flask import Flask, render_template, request, jsonify, send_file
from ebay_scraper import EbayScraper  # Import our enhanced scraper
import json
import os
import threading
import time
from datetime import datetime

app = Flask(__name__)

# Global variables to track scraping progress
scraping_progress = {
    'status': 'idle',
    'current_page': 0,
    'total_pages': 0,
    'items_found': 0,
    'current_item': '',
    'items': [],
    'error_message': '',
    'start_time': None,
    'analytics': {
        'avg_price': 0,
        'price_range': {'min': 0, 'max': 0},
        'top_conditions': [],
        'fast_moving': [],
        'auction_ending_soon': [],
        'most_watched': []
    }
}

def update_progress(status, **kwargs):
    """Update scraping progress"""
    global scraping_progress
    scraping_progress['status'] = status
    for key, value in kwargs.items():
        scraping_progress[key] = value

def analyze_items(items):
    """Analyze scraped items for insights"""
    if not items:
        return {}
    
    # Price analysis
    prices = [item['price'] for item in items if item.get('price')]
    avg_price = sum(prices) / len(prices) if prices else 0
    price_range = {'min': min(prices), 'max': max(prices)} if prices else {'min': 0, 'max': 0}
    
    # Condition analysis
    conditions = {}
    for item in items:
        condition = item.get('condition', 'N/A')
        conditions[condition] = conditions.get(condition, 0) + 1
    
    top_conditions = sorted(conditions.items(), key=lambda x: x[1], reverse=True)[:3]
    
    # Fast moving items (high sold count or watchers)
    fast_moving = sorted([item for item in items if item.get('sold_count', 0) > 0 or item.get('watchers', 0) > 5], 
                        key=lambda x: (x.get('sold_count', 0) + x.get('watchers', 0)), reverse=True)[:10]
    
    # Auction ending soon
    auction_ending_soon = [item for item in items if item.get('time_left') and item['time_left'] != 'N/A'][:10]
    
    # Most watched
    most_watched = sorted([item for item in items if item.get('watchers', 0) > 0], 
                         key=lambda x: x.get('watchers', 0), reverse=True)[:10]
    
    return {
        'avg_price': round(avg_price, 2),
        'price_range': price_range,
        'top_conditions': top_conditions,
        'fast_moving': fast_moving,
        'auction_ending_soon': auction_ending_soon,
        'most_watched': most_watched
    }

class WebEnhancedScraper(EbayScraper):
    """Enhanced scraper with progress tracking for web interface"""
    
    def scrape_search_results(self, url, max_pages=3):
        """Override to add progress tracking"""
        all_items = []
        update_progress('running', total_pages=max_pages, start_time=datetime.now())
        
        for page in range(1, max_pages + 1):
            update_progress('running', current_page=page)
            print(f"Scraping page {page}...")
            
            page_url = f"{url}&_pgn={page}"
            
            try:
                time.sleep(random.uniform(2, 4))
                
                response = self.session.get(page_url)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find items using multiple selectors
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
                    if found_items:
                        items = found_items
                        break
                
                page_items = []
                for i, item in enumerate(items[:60]):
                    try:
                        item_data = self.extract_enhanced_item_data(item)
                        if item_data and self.is_valid_item(item_data):
                            all_items.append(item_data)
                            page_items.append(item_data)
                            
                            # Update progress with current item and analytics
                            analytics = analyze_items(all_items)
                            update_progress('running', 
                                          items_found=len(all_items),
                                          current_item=item_data.get('title', 'Unknown item')[:50],
                                          analytics=analytics)
                    except Exception as e:
                        print(f"Error extracting item {i}: {e}")
                        continue
                
                print(f"Found {len(page_items)} valid items on page {page}")
                
                if len(page_items) == 0:
                    break
                
            except Exception as e:
                print(f"Error fetching page {page}: {e}")
                update_progress('error', error_message=str(e))
                break
        
        final_analytics = analyze_items(all_items)
        update_progress('completed', items=all_items, items_found=len(all_items), analytics=final_analytics)
        return all_items

def scrape_in_background(keyword, max_pages, filters):
    """Run scraping in background thread"""
    global scraping_progress
    
    try:
        scraper = WebEnhancedScraper()
        
        # Build search with filters
        search_params = {'keyword': keyword}
        if filters.get('condition'):
            search_params['condition'] = filters['condition']
        if filters.get('price_min'):
            search_params['price_min'] = float(filters['price_min'])
        if filters.get('price_max'):
            search_params['price_max'] = float(filters['price_max'])
        if filters.get('sort_order'):
            search_params['sort_order'] = filters['sort_order']
        
        url = scraper.build_search_url(**search_params)
        items = scraper.scrape_search_results(url, max_pages)
        
        # Save results
        if items:
            filename = f"{keyword.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            filepath = os.path.join('data', filename)
            scraper.save_to_csv(items, filepath)
            scraping_progress['filename'] = filename
        
    except Exception as e:
        update_progress('error', error_message=str(e))

@app.route('/')
def index():
    return render_template('enhanced_index.html')

@app.route('/start_scrape', methods=['POST'])
def start_scrape():
    """Start scraping process"""
    global scraping_progress
    
    if scraping_progress['status'] == 'running':
        return jsonify({'error': 'Scraping already in progress'})
    
    data = request.json
    keyword = data.get('keyword', '').strip()
    max_pages = int(data.get('max_pages', 2))
    filters = data.get('filters', {})
    
    if not keyword:
        return jsonify({'error': 'Search keyword is required'})
    
    # Reset progress
    scraping_progress = {
        'status': 'idle',
        'current_page': 0,
        'total_pages': 0,
        'items_found': 0,
        'current_item': '',
        'items': [],
        'error_message': '',
        'start_time': None,
        'analytics': {
            'avg_price': 0,
            'price_range': {'min': 0, 'max': 0},
            'top_conditions': [],
            'fast_moving': [],
            'auction_ending_soon': [],
            'most_watched': []
        }
    }
    
    # Start scraping in background
    thread = threading.Thread(target=scrape_in_background, args=(keyword, max_pages, filters))
    thread.daemon = True
    thread.start()
    
    return jsonify({'message': 'Scraping started'})

@app.route('/progress')
def get_progress():
    """Get current scraping progress"""
    return jsonify(scraping_progress)

@app.route('/download/<filename>')
def download_file(filename):
    """Download CSV file"""
    file_path = os.path.join('data', filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return jsonify({'error': 'File not found'}), 404

def create_templates():
    """Create templates directory and enhanced HTML template"""
    os.makedirs('templates', exist_ok=True)
    os.makedirs('data', exist_ok=True)
    
    # Enhanced HTML template with analytics dashboard
    html_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Enhanced eBay Scraper with Analytics</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .main-content {
            padding: 30px;
        }
        
        .dashboard-grid {
            display: grid;
            grid-template-columns: 1fr 2fr;
            gap: 30px;
            margin-bottom: 30px;
        }
        
        .search-form {
            background: #f8f9fa;
            padding: 25px;
            border-radius: 10px;
        }
        
        .analytics-panel {
            background: #f8f9fa;
            padding: 25px;
            border-radius: 10px;
        }
        
        .analytics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        
        .metric-card {
            background: white;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            border-left: 4px solid #667eea;
        }
        
        .metric-value {
            font-size: 1.5em;
            font-weight: bold;
            color: #667eea;
        }
        
        .metric-label {
            font-size: 0.9em;
            color: #666;
            margin-top: 5px;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: 600;
            color: #333;
        }
        
        input, select {
            width: 100%;
            padding: 12px;
            border: 2px solid #e9ecef;
            border-radius: 8px;
            font-size: 16px;
            transition: border-color 0.3s;
        }
        
        input:focus, select:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .form-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }
        
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s;
        }
        
        .btn:hover {
            transform: translateY(-2px);
        }
        
        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
        .progress-section {
            background: #f8f9fa;
            padding: 25px;
            border-radius: 10px;
            margin-bottom: 30px;
            display: none;
        }
        
        .progress-bar {
            width: 100%;
            height: 20px;
            background: #e9ecef;
            border-radius: 10px;
            overflow: hidden;
            margin: 20px 0;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            width: 0%;
            transition: width 0.3s;
        }
        
        .status-info {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        
        .status-card {
            background: white;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }
        
        .status-card h4 {
            color: #667eea;
            margin-bottom: 5px;
        }
        
        .insights-section {
            margin-top: 30px;
        }
        
        .insights-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        
        .insight-panel {
            background: white;
            border: 1px solid #e9ecef;
            border-radius: 10px;
            padding: 20px;
        }
        
        .insight-panel h4 {
            color: #667eea;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .insight-list {
            max-height: 300px;
            overflow-y: auto;
        }
        
        .insight-item {
            padding: 10px;
            border-bottom: 1px solid #f0f0f0;
            transition: background-color 0.2s;
        }
        
        .insight-item:hover {
            background-color: #f8f9fa;
        }
        
        .insight-item:last-child {
            border-bottom: none;
        }
        
        .item-title {
            font-weight: 600;
            margin-bottom: 5px;
            color: #333;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }
        
        .item-meta {
            font-size: 0.9em;
            color: #666;
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
        }
        
        .results-section {
            margin-top: 30px;
        }
        
        .results-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        
        .result-card {
            background: white;
            border: 1px solid #e9ecef;
            border-radius: 10px;
            padding: 15px;
            transition: transform 0.2s, box-shadow 0.2s;
            position: relative;
        }
        
        .result-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        }
        
        .result-badges {
            position: absolute;
            top: 10px;
            right: 10px;
            display: flex;
            flex-direction: column;
            gap: 5px;
        }
        
        .badge {
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 0.7em;
            font-weight: bold;
            color: white;
        }
        
        .badge.hot { background: #ff6b35; }
        .badge.watched { background: #4ecdc4; }
        .badge.ending { background: #f39c12; }
        
        .result-image {
            width: 100%;
            height: 160px;
            object-fit: cover;
            border-radius: 8px;
            margin-bottom: 12px;
        }
        
        .result-title {
            font-weight: 600;
            margin-bottom: 10px;
            color: #333;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }
        
        .result-price {
            font-size: 1.3em;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 8px;
        }
        
        .result-details {
            font-size: 0.9em;
            color: #666;
        }
        
        .result-stats {
            display: flex;
            gap: 15px;
            margin-top: 10px;
            font-size: 0.8em;
            color: #888;
        }
        
        .error {
            background: #ffe6e6;
            color: #d00;
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
        }
        
        .success {
            background: #e6ffe6;
            color: #060;
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
        }
        
        @media (max-width: 1200px) {
            .dashboard-grid {
                grid-template-columns: 1fr;
            }
        }
        
        @media (max-width: 768px) {
            .form-row {
                grid-template-columns: 1fr;
            }
            
            .container {
                margin: 10px;
            }
            
            .header h1 {
                font-size: 2em;
            }
            
            .analytics-grid {
                grid-template-columns: repeat(2, 1fr);
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Enhanced eBay Scraper</h1>
            <p>Advanced data extraction with real-time analytics and insights</p>
        </div>
        
        <div class="main-content">
            <div class="dashboard-grid">
                <div class="search-form">
                    <h2>Search Configuration</h2>
                    
                    <div class="form-group">
                        <label for="keyword">Search Keyword *</label>
                        <input type="text" id="keyword" placeholder="e.g., iPhone 15, vintage watch, trending gadgets" required>
                    </div>
                    
                    <div class="form-row">
                        <div class="form-group">
                            <label for="max-pages">Max Pages</label>
                            <select id="max-pages">
                                <option value="2">2 Pages (~120 items)</option>
                                <option value="3" selected>3 Pages (~180 items)</option>
                                <option value="5">5 Pages (~300 items)</option>
                                <option value="10">10 Pages (~600 items)</option>
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label for="condition">Condition</label>
                            <select id="condition">
                                <option value="">Any Condition</option>
                                <option value="New">New</option>
                                <option value="Used">Used</option>
                                <option value="Refurbished">Refurbished</option>
                            </select>
                        </div>
                    </div>
                    
                    <div class="form-row">
                        <div class="form-group">
                            <label for="price-min">Min Price ($)</label>
                            <input type="number" id="price-min" placeholder="e.g., 50">
                        </div>
                        
                        <div class="form-group">
                            <label for="price-max">Max Price ($)</label>
                            <input type="number" id="price-max" placeholder="e.g., 500">
                        </div>
                    </div>
                    
                    <div class="form-group">
                        <label for="sort-order">Sort By</label>
                        <select id="sort-order">
                            <option value="">Best Match</option>
                            <option value="MostWatched">Most Watched (Trending)</option>
                            <option value="PricePlusShippingLowest">Price: Low to High</option>
                            <option value="PricePlusShipping">Price: High to Low</option>
                            <option value="EndTimeSoonest">Ending Soon</option>
                            <option value="NewestFirst">Newly Listed</option>
                        </select>
                    </div>
                    
                    <button class="btn" id="start-btn" onclick="startScraping()">
                        🚀 Start Advanced Scraping
                    </button>
                </div>
                
                <div class="analytics-panel">
                    <h3>📊 Real-time Analytics</h3>
                    <div class="analytics-grid" id="analytics-grid">
                        <div class="metric-card">
                            <div class="metric-value" id="total-items">0</div>
                            <div class="metric-label">Items Found</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value" id="avg-price">$0</div>
                            <div class="metric-label">Avg Price</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value" id="price-range">$0-$0</div>
                            <div class="metric-label">Price Range</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value" id="hot-items">0</div>
                            <div class="metric-label">Hot Items</div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="progress-section" id="progress-section">
                <h3>Scraping Progress</h3>
                <div class="progress-bar">
                    <div class="progress-fill" id="progress-fill"></div>
                </div>
                
                <div class="status-info">
                    <div class="status-card">
                        <h4>Status</h4>
                        <span id="status">Idle</span>
                    </div>
                    <div class="status-card">
                        <h4>Current Page</h4>
                        <span id="current-page">0/0</span>
                    </div>
                    <div class="status-card">
                        <h4>Items Found</h4>
                        <span id="items-found">0</span>
                    </div>
                    <div class="status-card">
                        <h4>Current Item</h4>
                        <span id="current-item">-</span>
                    </div>
                </div>
            </div>
            
            <div class="insights-section" id="insights-section" style="display: none;">
                <h3>🔥 Market Insights</h3>
                <div class="insights-grid">
                    <div class="insight-panel">
                        <h4>🚀 Fast Moving Items</h4>
                        <div class="insight-list" id="fast-moving-list">
                            <div class="insight-item">Start scraping to see insights...</div>
                        </div>
                    </div>
                    
                    <div class="insight-panel">
                        <h4>👀 Most Watched</h4>
                        <div class="insight-list" id="most-watched-list">
                            <div class="insight-item">Start scraping to see insights...</div>
                        </div>
                    </div>
                    
                    <div class="insight-panel">
                        <h4>⏰ Ending Soon</h4>
                        <div class="insight-list" id="ending-soon-list">
                            <div class="insight-item">Start scraping to see insights...</div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="results-section" id="results-section">
                <h3>📦 Scraped Results</h3>
                <div id="results-grid" class="results-grid">
                    <!-- Results will be populated here -->
                </div>
            </div>
        </div>
    </div>

    <script>
        let progressInterval;
        
        async function startScraping() {
            const keyword = document.getElementById('keyword').value.trim();
            if (!keyword) {
                alert('Please enter a search keyword');
                return;
            }
            
            const maxPages = parseInt(document.getElementById('max-pages').value);
            const filters = {
                condition: document.getElementById('condition').value,
                price_min: document.getElementById('price-min').value,
                price_max: document.getElementById('price-max').value,
                sort_order: document.getElementById('sort-order').value
            };
            
            // UI updates
            document.getElementById('start-btn').disabled = true;
            document.getElementById('start-btn').textContent = '⏳ Initializing...';
            document.getElementById('progress-section').style.display = 'block';
            document.getElementById('insights-section').style.display = 'block';
            document.getElementById('results-grid').innerHTML = '';
            
            try {
                const response = await fetch('/start_scrape', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        keyword: keyword,
                        max_pages: maxPages,
                        filters: filters
                    })
                });
                
                const result = await response.json();
                
                if (result.error) {
                    throw new Error(result.error);
                }
                
                // Start progress monitoring
                progressInterval = setInterval(updateProgress, 1000);
                
            } catch (error) {
                alert('Error: ' + error.message);
                resetUI();
            }
        }
        
        async function updateProgress() {
            try {
                const response = await fetch('/progress');
                const progress = await response.json();
                
                // Update progress bar
                const progressPercent = progress.total_pages > 0 ? 
                    (progress.current_page / progress.total_pages) * 100 : 0;
                document.getElementById('progress-fill').style.width = progressPercent + '%';
                
                // Update status info
                document.getElementById('status').textContent = progress.status;
                document.getElementById('current-page').textContent = 
                    progress.current_page + '/' + progress.total_pages;
                document.getElementById('items-found').textContent = progress.items_found;
                document.getElementById('current-item').textContent = 
                    progress.current_item || '-';
                
                // Update analytics
                if (progress.analytics) {
                    updateAnalytics(progress.analytics);
                }
                
                // Update results
                if (progress.items && progress.items.length > 0) {
                    displayResults(progress.items);
                    updateInsights(progress.analytics);
                }
                
                // Handle completion or error
                if (progress.status === 'completed') {
                    clearInterval(progressInterval);
                    document.getElementById('start-btn').textContent = '✅ Completed!';
                    setTimeout(() => {
                        resetUI();
                    }, 3000);
                    
                    if (progress.filename) {
                        showDownloadLink(progress.filename);
                    }
                } else if (progress.status === 'error') {
                    clearInterval(progressInterval);
                    alert('Scraping error: ' + progress.error_message);
                    resetUI();
                }
                
            } catch (error) {
                console.error('Error updating progress:', error);
            }
        }
        
        function updateAnalytics(analytics) {
            document.getElementById('total-items').textContent = 
                document.getElementById('items-found').textContent;
            document.getElementById('avg-price').textContent = 
                analytics.avg_price ? '$' + analytics.avg_price : '$0';
            document.getElementById('price-range').textContent = 
                analytics.price_range ? '$' + analytics.price_range.min + '-$' + analytics.price_range.max : '$0-$0';
            document.getElementById('hot-items').textContent = 
                analytics.fast_moving ? analytics.fast_moving.length : '0';
        }
        
        function updateInsights(analytics) {
            if (!analytics) return;
            
            // Fast moving items
            updateInsightList('fast-moving-list', analytics.fast_moving, (item) => `
                <div class="item-title">${item.title}</div>
                <div class="item-meta">
                    <span>💰 ${item.price_text}</span>
                    ${item.sold_count ? `<span>📦 ${item.sold_count} sold</span>` : ''}
                    ${item.watchers ? `<span>👀 ${item.watchers} watching</span>` : ''}
                </div>
            `);
            
            // Most watched items
            updateInsightList('most-watched-list', analytics.most_watched, (item) => `
                <div class="item-title">${item.title}</div>
                <div class="item-meta">
                    <span>💰 ${item.price_text}</span>
                    <span>👀 ${item.watchers} watchers</span>
                    <span>📍 ${item.location}</span>
                </div>
            `);
            
            // Ending soon items
            updateInsightList('ending-soon-list', analytics.auction_ending_soon, (item) => `
                <div class="item-title">${item.title}</div>
                <div class="item-meta">
                    <span>💰 ${item.price_text}</span>
                    <span>⏰ ${item.time_left}</span>
                    <span>📍 ${item.location}</span>
                </div>
            `);
        }
        
        function updateInsightList(listId, items, formatter) {
            const list = document.getElementById(listId);
            if (!items || items.length === 0) {
                list.innerHTML = '<div class="insight-item">No items found yet...</div>';
                return;
            }
            
            list.innerHTML = items.slice(0, 10).map(item => `
                <div class="insight-item">
                    ${formatter(item)}
                </div>
            `).join('');
        }
        
        function displayResults(items) {
            const grid = document.getElementById('results-grid');
            grid.innerHTML = '';
            
            items.slice(0, 30).forEach(item => {
                const card = document.createElement('div');
                card.className = 'result-card';
                
                // Generate badges
                let badges = '';
                if (item.sold_count > 10) badges += '<span class="badge hot">🔥 HOT</span>';
                if (item.watchers > 10) badges += '<span class="badge watched">👀 WATCHED</span>';
                if (item.time_left && item.time_left !== 'N/A') badges += '<span class="badge ending">⏰ ENDING</span>';
                
                card.innerHTML = `
                    ${badges ? `<div class="result-badges">${badges}</div>` : ''}
                    ${item.image_url !== 'N/A' ? 
                        `<img src="${item.image_url}" class="result-image" alt="Product image" onerror="this.src='data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 width=%22320%22 height=%22160%22><rect width=%22100%25%22 height=%22100%25%22 fill=%22%23f0f0f0%22/><text x=%2250%25%22 y=%2250%25%22 text-anchor=%22middle%22 dy=%22.3em%22 fill=%22%23999%22>No Image</text></svg>'">` : 
                        '<div style="height: 160px; background: #f0f0f0; border-radius: 8px; display: flex; align-items: center; justify-content: center; margin-bottom: 12px; color: #999;">📷 No Image</div>'
                    }
                    <div class="result-title">${item.title}</div>
                    <div class="result-price">${item.price_text}</div>
                    <div class="result-details">
                        <div>📦 Shipping: ${item.shipping}</div>
                        <div>✨ Condition: ${item.condition}</div>
                        <div>📍 Location: ${item.location}</div>
                    </div>
                    ${(item.watchers || item.sold_count || item.time_left !== 'N/A') ? `
                        <div class="result-stats">
                            ${item.watchers ? `<span>👀 ${item.watchers}</span>` : ''}
                            ${item.sold_count ? `<span>📦 ${item.sold_count} sold</span>` : ''}
                            ${item.time_left !== 'N/A' ? `<span>⏰ ${item.time_left}</span>` : ''}
                        </div>
                    ` : ''}
                `;
                
                // Add click handler to open eBay link
                if (item.link !== 'N/A') {
                    card.style.cursor = 'pointer';
                    card.onclick = () => window.open(item.link, '_blank');
                }
                
                grid.appendChild(card);
            });
        }
        
        function showDownloadLink(filename) {
            const resultsSection = document.getElementById('results-section');
            const downloadDiv = document.createElement('div');
            downloadDiv.className = 'success';
            downloadDiv.innerHTML = `
                <h4>✅ Scraping Completed Successfully!</h4>
                <p><strong>${document.getElementById('items-found').textContent}</strong> items found and analyzed</p>
                <div style="margin-top: 15px;">
                    <a href="/download/${filename}" class="btn" style="display: inline-block; text-decoration: none; margin-right: 10px;">
                        📥 Download CSV File
                    </a>
                    <button class="btn" onclick="resetUI()" style="background: #28a745;">
                        🔄 Search Again
                    </button>
                </div>
                <div style="margin-top: 10px; font-size: 0.9em; color: #666;">
                    💡 Tip: CSV file contains all ${document.getElementById('items-found').textContent} items with detailed information including prices, watchers, sold counts, and more!
                </div>
            `;
            resultsSection.insertBefore(downloadDiv, resultsSection.firstChild);
        }
        
        function resetUI() {
            document.getElementById('start-btn').disabled = false;
            document.getElementById('start-btn').textContent = '🚀 Start Advanced Scraping';
            document.getElementById('progress-section').style.display = 'none';
            
            // Clear success messages
            const successDivs = document.querySelectorAll('.success');
            successDivs.forEach(div => div.remove());
        }
        
        // Add some sample trending searches
        const trendingSearches = [
            'iPhone 15 Pro Max', 'Gaming Laptop RTX 4080', 'Stanley Cup 40oz',
            'Nike Air Jordan', 'Pokemon Cards', 'Vintage Rolex',
            'MacBook Pro M3', 'Sony PlayStation 5', 'Nintendo Switch OLED'
        ];
        
        function addTrendingSearches() {
            const keywordInput = document.getElementById('keyword');
            keywordInput.placeholder = `Try: ${trendingSearches[Math.floor(Math.random() * trendingSearches.length)]}`;
            
            // Rotate placeholder every 3 seconds
            setInterval(() => {
                keywordInput.placeholder = `Try: ${trendingSearches[Math.floor(Math.random() * trendingSearches.length)]}`;
            }, 3000);
        }
        
        // Initialize trending searches
        addTrendingSearches();
        
        // Add Enter key support for search
        document.getElementById('keyword').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                startScraping();
            }
        });
    </script>
</body>
</html>'''
    
    with open('templates/enhanced_index.html', 'w', encoding='utf-8') as f:
        f.write(html_content)

if __name__ == '__main__':
    # Import required modules for enhanced scraper
    import random
    from bs4 import BeautifulSoup
    
    # Create templates and directories on startup
    create_templates()
    print("🚀 Starting Enhanced eBay Scraper Web Interface...")
    print("📱 Open your browser and go to: http://localhost:5000")
    print("💡 Features: Real-time analytics, market insights, trending items")
    print("💡 Use Ctrl+C to stop the server")
    
    app.run(debug=True, host='0.0.0.0', port=5000)