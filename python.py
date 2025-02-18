import streamlit as st
import google.generativeai as genai
import os
from newspaper import Article
import nltk
from dotenv import load_dotenv
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Download required NLTK data
try:
    nltk.download('punkt', quiet=True)
except Exception as e:
    logger.error(f"Error downloading NLTK data: {e}")

# Load environment variables and configure Gemini
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Initialize Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-pro")
else:
    st.error("⚠️ Gemini API Key not found. Please check your .env file.")
    st.stop()

# Streamlit configuration
st.set_page_config(
    page_title="AI Website Analyzer Pro",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced Custom CSS with vibrant color schemes
st.markdown("""
    <style>
    /* Global styles */
    .stApp {
        background: linear-gradient(to bottom, #E6F3FF, #FFFFFF);
    }
    
    /* Main container styling */
    .main {
        padding: 2rem;
    }
    
    /* Animated gradient header */
    .gradient-header {
        background: linear-gradient(-45deg, #FF6B6B, #4ECDC4, #45B7D1, #6C63FF);
        background-size: 400% 400%;
        animation: gradient 15s ease infinite;
        color: white;
        padding: 2rem;
        border-radius: 1rem;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15);
    }
    
    @keyframes gradient {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    /* Enhanced chat message styling */
    .chat-message {
        padding: 1.5rem;
        border-radius: 1rem;
        margin: 1rem 0;
        max-width: 85%;
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.1);
        transition: transform 0.2s ease;
    }
    
    .chat-message:hover {
        transform: translateY(-2px);
    }
    
    .user-message {
        background: linear-gradient(135deg, #6C63FF 0%, #4834DF 100%);
        color: white;
        margin-left: auto;
    }
    
    .assistant-message {
        background: linear-gradient(135deg, #FFFFFF 0%, #F0F7FF 100%);
        border: 2px solid #E1E8FF;
        color: #2D3748;
        margin-right: auto;
    }
    
    /* Animated key points box */
    .key-points {
        background: white;
        border-radius: 1rem;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 6px 18px rgba(108, 99, 255, 0.15);
        border-left: 4px solid #6C63FF;
        transition: all 0.3s ease;
    }
    
    .key-points:hover {
        transform: scale(1.02);
        box-shadow: 0 8px 24px rgba(108, 99, 255, 0.2);
    }
    
    /* Enhanced stats box */
    .stats-box {
        background: linear-gradient(135deg, #FF6B6B 0%, #FF8E53 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 1rem;
        margin: 1rem 0;
        box-shadow: 0 6px 18px rgba(255, 107, 107, 0.2);
        transition: transform 0.3s ease;
    }
    
    .stats-box:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 24px rgba(255, 107, 107, 0.3);
    }
    
    /* Custom button styling */
    .custom-button {
        background: linear-gradient(135deg, #6C63FF 0%, #4834DF 100%);
        color: white;
        padding: 0.75rem 1.5rem;
        border-radius: 0.5rem;
        border: none;
        cursor: pointer;
        transition: all 0.3s ease;
        text-align: center;
        display: block;
        width: 100%;
        margin: 0.5rem 0;
        font-weight: bold;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .custom-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 18px rgba(108, 99, 255, 0.3);
    }
    
    .delete-button {
        background: linear-gradient(135deg, #FF6B6B 0%, #FF4949 100%);
    }
    
    /* URL input styling */
    .stTextInput > div > div > input {
        border: 2px solid #E1E8FF;
        border-radius: 0.5rem;
        padding: 0.75rem 1rem;
        transition: all 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #6C63FF;
        box-shadow: 0 0 0 2px rgba(108, 99, 255, 0.2);
    }
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: #F0F7FF;
        border-radius: 5px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #6C63FF;
        border-radius: 5px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #4834DF;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

def clear_chat():
    st.session_state.messages = []
    st.session_state.analytics['total_questions'] = 0

def reset_analysis():
    st.session_state.website_content = None
    st.session_state.messages = []
    st.session_state.analytics['total_questions'] = 0
    st.session_state.analytics['websites_analyzed'] = set()

def extract_website_content(url):
    """Extract content from a website URL"""
    try:
        article = Article(url)
        article.download()
        article.parse()
        
        content = {
            'text': article.text,
            'title': article.title,
            'publish_date': article.publish_date,
            'top_image': article.top_image,
            'length': len(article.text),
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        if not content['text']:
            raise ValueError("No content extracted from the website")
            
        return content
    except Exception as e:
        logger.error(f"Error extracting website content: {e}")
        return None

def generate_response(query, website_text):
    """Generate response using Gemini with context"""
    try:
        max_context_length = 5000
        truncated_text = website_text[:max_context_length] if len(website_text) > max_context_length else website_text
        
        prompt = f"""
        Based on this website content:
        {truncated_text}

        Question: {query}

        Please provide a clear and comprehensive answer based on the website content.
        Format your response with markdown for better readability.
        If the content doesn't contain relevant information, mention that and provide a general response.
        """
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logger.error(f"Error generating Gemini response: {e}")
        return "I apologize, but I encountered an error while processing your request. Please try again."

# Initialize session state
if 'website_content' not in st.session_state:
    st.session_state.website_content = None
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'analytics' not in st.session_state:
    st.session_state.analytics = {
        'total_questions': 0,
        'websites_analyzed': set(),
        'last_activity': None
    }

# Animated header
st.markdown("""
    <div class="gradient-header">
        <h1>🤖 AI ChatNexus</h1>
        <p style="font-size: 1.2rem;">Transform website content into intelligent conversations</p>
    </div>
""", unsafe_allow_html=True)

# Create two columns for main content and sidebar
col1, col2 = st.columns([2, 1])

with col1:
    # Main content area
    st.markdown("""
        <div style="padding: 1rem; background: blue; border-radius: 1rem; margin-bottom: 1rem;">
            <h3>🔍 Analyze Any Website</h3>
        </div>
    """, unsafe_allow_html=True)
    
    url = st.text_input("", placeholder="Enter website URL (e.g., https://example.com)")
    
    if url:
        if st.button("🚀 Start Analysis", use_container_width=True):
            with st.spinner("🔄 Analyzing website content..."):
                content = extract_website_content(url)
                if content:
                    st.session_state.website_content = content
                    st.session_state.analytics['websites_analyzed'].add(url)
                    st.session_state.analytics['last_activity'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    st.success(f"✅ Successfully analyzed: {content['title']}")
                else:
                    st.error("❌ Failed to analyze website. Please check the URL and try again.")

    # Chat interface
    if st.session_state.website_content:
        st.markdown("""
            <div style="padding: 1rem; background: white; border-radius: 1rem; margin: 1rem 0;">
                <h3>💬 Ask Questions</h3>
            </div>
        """, unsafe_allow_html=True)
        
        user_input = st.chat_input("Ask anything about the website content...")
        
        if user_input:
            st.session_state.analytics['total_questions'] += 1
            st.session_state.analytics['last_activity'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            st.session_state.messages.append({"role": "user", "content": user_input})
            
            with st.spinner("🤔 Analyzing..."):
                response = generate_response(user_input, st.session_state.website_content['text'])
            
            st.session_state.messages.append({"role": "assistant", "content": response})

        # Display chat history
        for message in st.session_state.messages:
            message_class = "user-message" if message["role"] == "user" else "assistant-message"
            st.markdown(f"""
                <div class="chat-message {message_class}">
                    {message["content"]}
                </div>
            """, unsafe_allow_html=True)

with col2:
    # Stats and controls
    st.markdown("""
        <div class="stats-box">
            <h3 style="margin:0">📊 Analytics Dashboard</h3>
            <p style="font-size: 2rem; margin:0">{}</p>
            <p style="margin:0">Questions Analyzed</p>
        </div>
    """.format(st.session_state.analytics['total_questions']), unsafe_allow_html=True)
    
    st.markdown("""
        <div class="stats-box">
            <h3 style="margin:0">🌐 Websites</h3>
            <p style="font-size: 2rem; margin:0">{}</p>
            <p style="margin:0">Sites Analyzed</p>
        </div>
    """.format(len(st.session_state.analytics['websites_analyzed'])), unsafe_allow_html=True)
    
    if st.session_state.website_content:
        st.markdown("""
    <div class="key-points" style="background: linear-gradient(135deg, #FF6B6B 0%, #FF8E53 100%);">
        <h3>📑 Current Analysis</h3>
        <p><strong>Title:</strong> {}</p>
        <p><strong>Content Size:</strong> {} characters</p>
        <p><strong>Last Updated:</strong> {}</p>
    </div>
""".format(
    st.session_state.website_content['title'],
    st.session_state.website_content['length'],
    st.session_state.website_content['timestamp']
), unsafe_allow_html=True)

    # Control buttons with new styling
    if st.session_state.messages:
        if st.button("🗑️ Clear Chat History", on_click=clear_chat, use_container_width=True):
            st.experimental_rerun()
    
    if st.session_state.website_content:
        if st.button("🔄 Reset Analysis", on_click=reset_analysis, use_container_width=True):
            st.experimental_rerun()

# Footer with animation
st.markdown("""
    <div style="text-align: center; margin-top: 2rem; padding: 1rem; background:linear-gradient(135deg, #6C63FF 0%, #4834DF 100%); border-radius: 1rem; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);">
        <p>Built with  AI ChatNexus</p>
    </div>
""", unsafe_allow_html=True)