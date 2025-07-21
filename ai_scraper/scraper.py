# ai_scraper/scraper.py
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import json
from .utils import clean_text

class ProductScraper:
    def __init__(self):
        self.driver = None
        self.setup_driver()
    
    def setup_driver(self):
        """Setup Chrome driver with headless options"""
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        self.driver = webdriver.Chrome(options=options)
    
    def scrape_products(self, url):
        """Scrape products from the given URL"""
        try:
            self.driver.get(url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Additional wait for dynamic content
            time.sleep(3)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            products = []
            
            # Generic selectors - adapt based on target website
            product_selectors = [
                '.product-card', '.product-item', '.product', '.item',
                '[data-testid*="product"]', '.s-result-item',
                '.product-tile', '.product-box'
            ]
            
            product_elements = []
            for selector in product_selectors:
                elements = soup.select(selector)
                if elements:
                    product_elements = elements
                    break
            
            for card in product_elements[:20]:  # Limit to 20 products
                product = self.extract_product_info(card)
                if product['name']:  # Only add if name exists
                    products.append(product)
            
            return products
            
        except Exception as e:
            print(f"Error scraping products: {str(e)}")
            return []
    
    def extract_product_info(self, card):
        """Extract product information from a product card element"""
        # Name selectors
        name_selectors = [
            '.product-title', '.item-title', '.product-name',
            'h2', 'h3', '[data-testid*="title"]', '.title'
        ]
        
        # Price selectors
        price_selectors = [
            '.price', '.product-price', '.cost', '[data-testid*="price"]',
            '.price-current', '.sale-price', '.offer-price'
        ]
        
        # Rating selectors
        rating_selectors = [
            '.rating', '.product-rating', '.stars', '[data-testid*="rating"]',
            '.review-score', '.star-rating'
        ]
        
        # Description selectors
        desc_selectors = [
            '.description', '.product-desc', '.summary',
            '.product-details', '.item-description'
        ]
        
        # Availability selectors
        avail_selectors = [
            '.availability', '.in-stock', '.stock-status',
            '[data-testid*="availability"]', '.inventory-status'
        ]
        
        name = self.find_element_text(card, name_selectors)
        price = self.find_element_text(card, price_selectors)
        rating = self.find_element_text(card, rating_selectors)
        description = self.find_element_text(card, desc_selectors)
        availability = self.find_element_text(card, avail_selectors)
        
        return {
            "name": clean_text(name),
            "price": clean_text(price),
            "rating": clean_text(rating),
            "description": clean_text(description),
            "availability": clean_text(availability)
        }
    
    def find_element_text(self, parent, selectors):
        """Find element text using multiple selectors"""
        for selector in selectors:
            element = parent.select_one(selector)
            if element and element.get_text(strip=True):
                return element.get_text(strip=True)
        return None
    
    def close(self):
        """Close the browser driver"""
        if self.driver:
            self.driver.quit()

def scrape_products(url):
    """Main function to scrape products from URL"""
    scraper = ProductScraper()
    try:
        products = scraper.scrape_products(url)
        return products
    finally:
        scraper.close()
