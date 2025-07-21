# app.py
import streamlit as st
import json
import os
from datetime import datetime
from ai_scraper.scraper import scrape_products
from ai_scraper.utils import save_products_to_json, load_products_from_json
from ai_agent.llm_query import query_llm, format_products_for_context
from ai_agent.rag_logic import simple_retrieve, analyze_query_intent

# Configure Streamlit page
st.set_page_config(
    page_title="🛒 Smart AI Shopping Assistant",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Constants
DATA_PATH = "data/scraped.json"

# Initialize session state
if 'products' not in st.session_state:
    st.session_state.products = []
if 'scraping_status' not in st.session_state:
    st.session_state.scraping_status = None
if 'query_history' not in st.session_state:
    st.session_state.query_history = []

# Main title and description
st.title("🛒 Smart AI Shopping Assistant")
st.markdown("""
Welcome to your intelligent shopping companion! Enter any e-commerce URL to scrape product data, 
then ask natural language questions about the products.
""")

# Sidebar for configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # API Configuration
    st.subheader("🔑 API Settings")
    api_key = st.text_input("LLM API Key", type="password", help="Enter your Gemini or Groq API key")
    model_type = st.selectbox("Select LLM Model", ["gemini", "groq"], index=0)
    
    if api_key:
        os.environ['LLM_API_KEY'] = api_key
        os.environ['LLM_MODEL'] = model_type
        st.success("✅ API key configured!")
    
    st.divider()
    
    # Scraping Options
    st.subheader("🕷️ Scraping Options")
    max_products = st.slider("Max products to scrape", 5, 50, 20)
    
    # Load existing data
    if st.button("📁 Load Existing Data"):
        if os.path.exists(DATA_PATH):
            st.session_state.products = load_products_from_json(DATA_PATH)
            st.success(f"Loaded {len(st.session_state.products)} products")
        else:
            st.warning("No existing data found")
    
    # Clear data
    if st.button("🗑️ Clear All Data"):
        st.session_state.products = []
        st.session_state.query_history = []
        if os.path.exists(DATA_PATH):
            os.remove(DATA_PATH)
        st.success("Data cleared!")

# Main content area
col1, col2 = st.columns([1, 1])

with col1:
    st.header("🌐 Product Scraping")
    
    # URL input
    url = st.text_input(
        "Enter E-commerce URL",
        placeholder="https://example.com/products",
        help="Enter the URL of a product listing page"
    )
    
    # Scraping button
    if st.button("🚀 Scrape Products", disabled=not url):
        if not api_key:
            st.error("Please enter your API key in the sidebar first!")
        else:
            with st.spinner("Scraping products... This may take a moment."):
                try:
                    # Create data directory if it doesn't exist
                    os.makedirs("data", exist_ok=True)
                    
                    # Scrape products
                    products = scrape_products(url)
                    
                    if products:
                        # Limit products based on user setting
                        products = products[:max_products]
                        
                        # Save to session state and file
                        st.session_state.products = products
                        save_products_to_json(products, DATA_PATH)
                        
                        st.success(f"✅ Successfully scraped {len(products)} products!")
                        st.session_state.scraping_status = "success"
                    else:
                        st.warning("⚠️ No products found. The website might use different selectors or have anti-scraping measures.")
                        st.session_state.scraping_status = "no_products"
                        
                except Exception as e:
                    st.error(f"❌ Error scraping products: {str(e)}")
                    st.session_state.scraping_status = "error"

with col2:
    st.header("🤖 AI Assistant")
    
    if st.session_state.products:
        # Query input
        query = st.text_input(
            "Ask about the products:",
            placeholder="Which product has the best rating?",
            help="Ask natural language questions about the scraped products"
        )
        
        # Predefined example queries
        st.markdown("**Example queries:**")
        example_queries = [
            "Which product has the best rating?",
            "Show me the cheapest products",
            "What products are available?",
            "Compare the top 3 products",
            "Which product offers the best value?"
        ]
        
        selected_query = st.selectbox("Or select an example:", [""] + example_queries)
        if selected_query:
            query = selected_query
        
        # Query button
        if st.button("💬 Ask Assistant") and query:
            if not api_key:
                st.error("Please enter your API key in the sidebar first!")
            else:
                with st.spinner("Thinking... 🤔"):
                    try:
                        # Analyze query intent
                        intent = analyze_query_intent(query)
                        
                        # Retrieve relevant products
                        relevant_products = simple_retrieve(st.session_state.products, query)
                        
                        # Format context for LLM
                        context = format_products_for_context(relevant_products or st.session_state.products)
                        
                        # Query LLM
                        answer = query_llm(context, query)
                        
                        # Display answer
                        st.markdown("### 🎯 Answer")
                        st.info(answer)
                        
                        # Save to history
                        st.session_state.query_history.append({
                            "query": query,
                            "answer": answer,
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        })
                        
                    except Exception as e:
                        st.error(f"❌ Error processing query: {str(e)}")
    else:
        st.info("👆 Please scrape some products first to start asking questions!")

# Product preview section
if st.session_state.products:
    st.header("📦 Product Preview")
    
    # Display statistics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Products", len(st.session_state.products))
    with col2:
        products_with_price = [p for p in st.session_state.products if p.get('price')]
        st.metric("Products with Price", len(products_with_price))
    with col3:
        products_with_rating = [p for p in st.session_state.products if p.get('rating')]
        st.metric("Products with Rating", len(products_with_rating))
    
    # Display products in expandable cards
    for idx, product in enumerate(st.session_state.products[:10]):  # Show first 10
        with st.expander(f"📦 {product.get('name', f'Product {idx+1}')}"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                if product.get('description'):
                    st.markdown(f"**Description:** {product['description']}")
                if product.get('availability'):
                    st.markdown(f"**Availability:** {product['availability']}")
            
            with col2:
                if product.get('price'):
                    st.markdown(f"**💰 Price:** {product['price']}")
                if product.get('rating'):
                    st.markdown(f"**⭐ Rating:** {product['rating']}")

# Query history section
if st.session_state.query_history:
    st.header("📜 Query History")
    
    with st.expander("View Previous Queries", expanded=False):
        for i, entry in enumerate(reversed(st.session_state.query_history[-5:])):  # Show last 5
            st.markdown(f"**Q{len(st.session_state.query_history)-i}:** {entry['query']}")
            st.markdown(f"**A:** {entry['answer']}")
            st.markdown(f"*Asked at: {entry['timestamp']}*")
            st.divider()

# Footer
st.markdown("---")
st.markdown(
    "Built with ❤️ using Streamlit, Selenium, BeautifulSoup, and AI. "
    "Make sure to respect website terms of service when scraping."
)
