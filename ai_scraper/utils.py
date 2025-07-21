# ai_scraper/utils.py
import re
import json
from datetime import datetime

def clean_text(text):
    """Clean and normalize text"""
    if not text:
        return None
    
    # Remove extra whitespaces and normalize
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Remove special characters that might interfere
    text = re.sub(r'[^\w\s\.\-\$\€\£\%\(\)]', '', text)
    
    return text if text else None

def extract_price(price_text):
    """Extract numeric price from price string"""
    if not price_text:
        return None
    
    # Remove currency symbols and extract number
    price_match = re.search(r'[\d,]+\.?\d*', price_text.replace(',', ''))
    return float(price_match.group()) if price_match else None

def extract_rating(rating_text):
    """Extract numeric rating from rating string"""
    if not rating_text:
        return None
    
    # Extract rating number (e.g., "4.5 out of 5" -> 4.5)
    rating_match = re.search(r'(\d+\.?\d*)', rating_text)
    return float(rating_match.group()) if rating_match else None

def save_products_to_json(products, filepath):
    """Save products to JSON file"""
    try:
        data = {
            'scraped_at': datetime.now().isoformat(),
            'total_products': len(products),
            'products': products
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return True
    except Exception as e:
        print(f"Error saving products: {str(e)}")
        return False

def load_products_from_json(filepath):
    """Load products from JSON file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return data.get('products', [])
    except Exception as e:
        print(f"Error loading products: {str(e)}")
        return []

def wait_for_element_load():
    """Standard wait time for elements to load"""
    import time
    time.sleep(2)
