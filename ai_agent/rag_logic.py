# ai_agent/rag_logic.py
import re
from typing import List, Dict, Any
from collections import Counter

class SimpleRAG:
    def __init__(self, products: List[Dict[str, Any]]):
        self.products = products
        self.keywords = self.extract_keywords()
    
    def extract_keywords(self) -> Dict[str, List[int]]:
        """Extract keywords from products and create an inverted index"""
        keyword_index = {}
        
        for i, product in enumerate(self.products):
            # Combine all text fields
            text_fields = [
                product.get('name', ''),
                product.get('description', ''),
                product.get('price', ''),
                product.get('rating', ''),
                product.get('availability', '')
            ]
            
            combined_text = ' '.join(filter(None, text_fields)).lower()
            
            # Extract keywords (simple word extraction)
            words = re.findall(r'\b\w+\b', combined_text)
            
            for word in words:
                if len(word) > 2:  # Filter out very short words
                    if word not in keyword_index:
                        keyword_index[word] = []
                    keyword_index[word].append(i)
        
        return keyword_index
    
    def retrieve_relevant_products(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Retrieve most relevant products based on query"""
        query_words = re.findall(r'\b\w+\b', query.lower())
        
        # Score products based on keyword matches
        product_scores = Counter()
        
        for word in query_words:
            if word in self.keywords:
                for product_idx in self.keywords[word]:
                    product_scores[product_idx] += 1
        
        # Get top scored products
        top_products = []
        for product_idx, score in product_scores.most_common(top_k):
            product = self.products[product_idx].copy()
            product['relevance_score'] = score
            top_products.append(product)
        
        # If no matches found, return first few products
        if not top_products:
            return self.products[:top_k]
        
        return top_products
    
    def filter_by_criteria(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Filter products by specific criteria"""
        filtered_products = []
        
        for product in self.products:
            matches_criteria = True
            
            # Price range filtering
            if 'min_price' in criteria or 'max_price' in criteria:
                price_text = product.get('price', '')
                price_match = re.search(r'[\d,]+\.?\d*', price_text.replace(',', ''))
                
                if price_match:
                    price = float(price_match.group())
                    if 'min_price' in criteria and price < criteria['min_price']:
                        matches_criteria = False
                    if 'max_price' in criteria and price > criteria['max_price']:
                        matches_criteria = False
                else:
                    matches_criteria = False
            
            # Rating filtering
            if 'min_rating' in criteria:
                rating_text = product.get('rating', '')
                rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                
                if rating_match:
                    rating = float(rating_match.group())
                    if rating < criteria['min_rating']:
                        matches_criteria = False
                else:
                    matches_criteria = False
            
            # Availability filtering
            if 'available_only' in criteria and criteria['available_only']:
                availability = product.get('availability', '').lower()
                if 'out of stock' in availability or 'unavailable' in availability:
                    matches_criteria = False
            
            if matches_criteria:
                filtered_products.append(product)
        
        return filtered_products

def simple_retrieve(products: List[Dict[str, Any]], user_query: str) -> List[Dict[str, Any]]:
    """Simple retrieval function for backward compatibility"""
    if not products:
        return []
    
    rag = SimpleRAG(products)
    return rag.retrieve_relevant_products(user_query)

def analyze_query_intent(query: str) -> Dict[str, Any]:
    """Analyze user query to determine intent and extract criteria"""
    query_lower = query.lower()
    intent = {}
    
    # Price-related queries
    if any(word in query_lower for word in ['cheap', 'cheapest', 'lowest price', 'budget']):
        intent['sort_by'] = 'price_asc'
    elif any(word in query_lower for word in ['expensive', 'highest price', 'premium']):
        intent['sort_by'] = 'price_desc'
    
    # Rating-related queries
    if any(word in query_lower for word in ['best', 'highest rated', 'top rated', 'best rating']):
        intent['sort_by'] = 'rating_desc'
    elif any(word in query_lower for word in ['worst', 'lowest rated', 'poor rating']):
        intent['sort_by'] = 'rating_asc'
    
    # Availability queries
    if any(word in query_lower for word in ['available', 'in stock', 'buy now']):
        intent['available_only'] = True
    
    # Extract price ranges
    price_match = re.search(r'under \$?(\d+)', query_lower)
    if price_match:
        intent['max_price'] = float(price_match.group(1))
    
    price_match = re.search(r'over \$?(\d+)', query_lower)
    if price_match:
        intent['min_price'] = float(price_match.group(1))
    
    return intent
