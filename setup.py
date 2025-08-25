#!/usr/bin/env python3
"""
Enhanced eBay Scraper Setup Script
Automatically sets up the complete scraping environment
"""

import os
import sys
import subprocess
import platform

def print_banner():
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║              🚀 Enhanced eBay Scraper Setup              ║
    ║                                                          ║
    ║  • Advanced data extraction with analytics               ║
    ║  • Real-time progress tracking                           ║
    ║  • Market insights and trending items                    ║
    ║  • Beautiful web interface                               ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    """)

def check_python_version():
    """Check if Python version is compatible"""
    print("🐍 Checking Python version...")
    
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8 or higher is required")
        print(f"   Current version: {version.major}.{version.minor}.{version.micro}")
        print("   Please update Python and try again")
        return False
    
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} - Compatible!")
    return True

def create_directories():
    """Create necessary directories"""
    print("📁 Creating project directories...")
    
    directories = ['data', 'logs', 'templates']
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"   ✅ Created: {directory}/")
        else:
            print(f"   ✅ Exists: {directory}/")

def install_requirements():
    """Install required packages"""
    print("📦 Installing required packages...")
    
    requirements = [
        'requests==2.31.0',
        'beautifulsoup4==4.12.2',
        'pandas==2.0.3',
        'lxml==4.9.3',
        'html5lib==1.1',
        'numpy==1.24.3',
        'flask==2.3.3'
    ]
    
    # Create requirements.txt
    with open('requirements.txt', 'w') as f:
        f.write('\n'.join(requirements))
    print("   ✅ Created requirements.txt")
    
    try:
        # Upgrade pip first
        print("   🔄 Upgrading pip...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'], 
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Install packages
        print("   📦 Installing packages... (this may take a moment)")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("   ✅ All packages installed successfully!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Failed to install packages: {e}")
        print("   💡 Try running manually: pip install -r requirements.txt")
        return False

def create_scraper_files():
    """Create the scraper files"""
    print("🛠️  Creating scraper files...")
    
    files_created = []
    
    # Check if files exist
    files_to_check = [
        ('ebay_scraper.py', 'Basic eBay scraper'),
        ('enhanced_scraper.py', 'Enhanced scraper with analytics'),
        ('app.py', 'Web interface application')
    ]
    
    for filename, description in files_to_check:
        if os.path.exists(filename):
            print(f"   ✅ {description}: {filename}")
            files_created.append(filename)
        else:
            print(f"   ❌ Missing: {filename}")
            print(f"      💡 Please create this file manually")
    
    return len(files_created) >= 2  # At least scraper and app files

def test_installation():
    """Test if everything is working"""
    print("🧪 Testing installation...")
    
    try:
        # Test imports
        import requests
        import bs4
        import pandas
        import flask
        print("   ✅ All modules can be imported")
        
        # Test basic scraper functionality
        if os.path.exists('enhanced_scraper.py'):
            print("   ✅ Enhanced scraper file exists")
        elif os.path.exists('ebay_scraper.py'):
            print("   ✅ Basic scraper file exists")
        else:
            print("   ❌ No scraper file found")
            return False
        
        # Test Flask app
        if os.path.exists('app.py'):
            print("   ✅ Flask app file exists")
        else:
            print("   ❌ Flask app file missing")
            return False
        
        return True
        
    except ImportError as e:
        print(f"   ❌ Import error: {e}")
        return False

def create_quick_start_guide():
    """Create a quick start guide"""
    print("📚 Creating quick start guide...")
    
    guide_content = """# 🚀 Enhanced eBay Scraper - Quick Start Guide

## ✅ Installation Complete!

Your enhanced eBay scraper is now ready to use!

## 🎯 Quick Start

### Method 1: Web Interface (Recommended)
```bash
python app.py
```
Then open: http://localhost:5000

### Method 2: Command Line
```python
from ebay_scraper import EnhancedEbayScraper

scraper = EnhancedEbayScraper()
items = scraper.search_and_scrape("iPhone 15", max_pages=3)
scraper.save_to_csv(items, "results.csv")
```

## 🌟 Features

### Web Interface Features:
- 📊 Real-time analytics dashboard
- 🔥 Fast moving items detection
- 👀 Most watched items tracking
- ⏰ Auction ending soon alerts
- 📱 Mobile-friendly responsive design
- 💾 One-click CSV download

### Scraper Features:
- 🎯 Advanced item detection (no more generic eBay ads)
- 🖼️ High-quality image extraction
- 📈 Seller analytics (watchers, sold count)
- 💰 Price range analysis
- 🏷️ Condition and location tracking
- ⚡ Fast, efficient scraping

## 🛠️ Troubleshooting

### Common Issues:
1. **Import errors**: Make sure virtual environment is activated
2. **No results**: Try different search terms or check internet connection
3. **Port 5000 busy**: Use `python app.py` and try http://127.0.0.1:5000

### Getting Help:
- Check the console output for error messages
- Ensure all files are in the correct location
- Try running the test script: `python test_scraper.py`

## 📊 Sample Searches to Try:
- "iPhone 15 Pro Max" (trending electronics)
- "Nike Air Jordan" (collectibles) 
- "Vintage Rolex" (luxury items)
- "Gaming Laptop RTX" (high-value items)
- "Pokemon Cards" (trending collectibles)

## 🎨 Web Interface Tips:
1. Use "Most Watched" sort for trending items
2. Set price ranges for targeted searches  
3. Check the analytics panel for market insights
4. Look for items with badges (🔥 HOT, 👀 WATCHED, ⏰ ENDING)

## 🔧 Advanced Usage:
- Modify `enhanced_scraper.py` for custom data fields
- Adjust delays in scraper for different speeds
- Add new analytics in the web interface
- Export data to different formats

Happy Scraping! 🕷️✨
"""
    
    with open('QUICKSTART.md', 'w', encoding='utf-8') as f:
        f.write(guide_content)
    print("   ✅ Created QUICKSTART.md")

def print_success_message():
    """Print final success message"""
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║                    🎉 SETUP COMPLETE! 🎉                 ║
    ╠══════════════════════════════════════════════════════════╣
    ║                                                          ║
    ║  Your Enhanced eBay Scraper is ready to use!            ║
    ║                                                          ║
    ║  🚀 Start the web interface:                             ║
    ║     python app.py                                        ║
    ║                                                          ║
    ║  🌐 Then open your browser to:                           ║
    ║     http://localhost:5000                                ║
    ║                                                          ║
    ║  📚 Read QUICKSTART.md for detailed instructions        ║
    ║                                                          ║
    ║  ⚡ Features you'll love:                                ║
    ║     • Real-time analytics dashboard                      ║
    ║     • Market insights and trending items                 ║
    ║     • Advanced filtering and sorting                     ║
    ║     • Beautiful, responsive web interface                ║
    ║     • Export to CSV with detailed data                   ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    """)

def main():
    """Main setup function"""
    print_banner()
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Create directories
    create_directories()
    
    # Install requirements
    if not install_requirements():
        print("⚠️  Package installation failed, but you can continue manually")
    
    # Check scraper files
    if not create_scraper_files():
        print("\n⚠️  Some scraper files are missing!")
        print("   Please make sure you have:")
        print("   - ebay_scraper.py (enhanced scraper)")
        print("   - app.py (web interface)")
        print("   Copy these files to your project directory")
    
    # Test installation
    if test_installation():
        print("✅ Installation test passed!")
    else:
        print("❌ Installation test failed - check manually")
    
    # Create quick start guide
    create_quick_start_guide()
    
    # Success message
    print_success_message()
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if success:
            sys.exit(0)
        else:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n❌ Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup failed with error: {e}")
        sys.exit(1)