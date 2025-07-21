# ai_agent/llm_query.py
import os
import requests
import json
from typing import List, Dict, Any

class LLMQueryProcessor:
    def __init__(self):
        self.api_key = os.getenv('LLM_API_KEY')
        self.model_type = os.getenv('LLM_MODEL', 'gemini')  # 'gemini' or 'groq'
        
        if not self.api_key:
            raise ValueError("LLM_API_KEY not found in environment variables")
    
    def query_gemini(self, context: str, user_query: str) -> str:
        """Query Gemini API"""
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
        
        headers = {
            "Content-Type": "application/json",
        }
        
        prompt = f"""Based on the following product information, please answer the user's question accurately and helpfully.

Product Data:
{context}

User Question: {user_query}

Please provide a clear, concise answer based only on the provided product information. If you cannot answer based on the available data, please say so."""

        data = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": 1000,
            }
        }
        
        try:
            response = requests.post(
                f"{url}?key={self.api_key}", 
                headers=headers, 
                json=data,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            if 'candidates' in result and len(result['candidates']) > 0:
                return result['candidates'][0]['content']['parts'][0]['text']
            else:
                return "I couldn't generate a response. Please try again."
                
        except requests.exceptions.RequestException as e:
            return f"Error connecting to Gemini API: {str(e)}"
        except Exception as e:
            return f"Error processing query: {str(e)}"
    
    def query_groq(self, context: str, user_query: str) -> str:
        """Query GroqCloud API"""
        url = "https://api.groq.com/openai/v1/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        messages = [
            {
                "role": "system",
                "content": "You are a helpful shopping assistant. Answer questions about products based on the provided data."
            },
            {
                "role": "user", 
                "content": f"Product Data:\n{context}\n\nQuestion: {user_query}"
            }
        ]
        
        data = {
            "model": "mixtral-8x7b-32768",
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 1000
        }
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            return result['choices'][0]['message']['content']
            
        except requests.exceptions.RequestException as e:
            return f"Error connecting to Groq API: {str(e)}"
        except Exception as e:
            return f"Error processing query: {str(e)}"
    
    def query_llm(self, context: str, user_query: str) -> str:
        """Main method to query LLM based on configured model"""
        if self.model_type.lower() == 'groq':
            return self.query_groq(context, user_query)
        else:
            return self.query_gemini(context, user_query)

def format_products_for_context(products: List[Dict[str, Any]]) -> str:
    """Format products data for LLM context"""
    if not products:
        return "No products available."
    
    formatted_products = []
    for i, product in enumerate(products, 1):
        product_info = f"Product {i}:\n"
        product_info += f"  Name: {product.get('name', 'N/A')}\n"
        product_info += f"  Price: {product.get('price', 'N/A')}\n"
        product_info += f"  Rating: {product.get('rating', 'N/A')}\n"
        product_info += f"  Description: {product.get('description', 'N/A')}\n"
        product_info += f"  Availability: {product.get('availability', 'N/A')}\n"
        formatted_products.append(product_info)
    
    return "\n".join(formatted_products)

# Main function for backward compatibility
def query_llm(context: str, user_query: str) -> str:
    """Main function to query LLM"""
    processor = LLMQueryProcessor()
    return processor.query_llm(context, user_query)
