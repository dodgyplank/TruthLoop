import streamlit as st
import sys
import os

# Add the current directory to Python path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

def main():
    """Main router function to handle navigation between pages"""
    
    # Get page parameter from URL
    query_params = st.experimental_get_query_params()
    page = query_params.get("page", ["home"])[0]
    
    # Route to appropriate page
    if page == "history":
        # Import and run history page
        try:
            import history
        except ImportError:
            st.error("History page not found. Please ensure history.py is in the same directory.")
            show_home_page()
    elif page == "what_if":
        # Import and run what-if page
        try:
            import what_if
        except ImportError:
            st.error("What If page not found. Please ensure what_if.py is in the same directory.")
            show_home_page()
    else:
        # Show home page (main analysis page)
        show_home_page()

def show_home_page():
    """Display the main TruthLoop analysis page"""
    # This is the main page content from your original file
    # You can either import it or include the code directly
    
    from PIL import Image
    import io
    import base64
    import tempfile
    import os
    import json
    import redis
    import hashlib
    from datetime import datetime
    from concurrent.futures import ThreadPoolExecutor
    
    # Import your existing modules
    try:
        from agents.llm_utils import generate_narration_from_json
        from agents.image_utils import encode_image_to_base64, generate_starter_frame
        from agents.detect_scam import detect_scam_text, ocr_with_openai
    except ImportError as e:
        st.error(f"Required modules not found: {e}")
        st.stop()
    
    import urllib.parse

    # Initialize Redis connection
    @st.cache_resource
    def init_redis():
        try:
            r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
            r.ping()
            return r
        except:
            st.warning("⚠️ Redis connection failed. History feature will be disabled.")
            return None

    redis_client = init_redis()

    # Page Configuration & Styling
    st.set_page_config(
        page_title="TruthLoop Educational Bot", 
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    # Include all the CSS and JavaScript from your original file
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        :root {
            --bg-primary: #0d1117;
            --bg-secondary: #161b22;
            --bg-tertiary: #21262d;
            --bg-card: #1c2128;
            --bg-elevated: #262c36;
            --text-primary: #f0f6fc;
            --text-secondary: #8b949e;
            --text-muted: #6e7681;
            --text-accent: #58a6ff;
            --border-primary: #30363d;
            --border-secondary: #21262d;
            --primary-color: #238636;
            --primary-hover: #2ea043;
            --secondary-color: #1f6feb;
            --accent-color: #58a6ff;
            --danger-color: #f85149;
            --danger-bg: #2d1117;
            --danger-border: #5d1a21;
            --warning-color: #f0883e;
            --warning-bg: #2d1b0e;
            --warning-border: #5d2f0e;
            --success-color: #56d364;
            --success-bg: #0d2818;
            --success-border: #1a5a2e;
            --threat-highlight: #ff6b6b;
            --threat-bg: rgba(255, 107, 107, 0.1);
            --threat-border: #ff4757;
            --shadow-light: rgba(0, 0, 0, 0.12);
            --shadow-medium: rgba(0, 0, 0, 0.25);
            --shadow-heavy: rgba(0, 0, 0, 0.4);
        }
        
        .nav-bar {
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 1000;
            background: var(--bg-card);
            border-radius: 25px;
            padding: 8px;
            border: 1px solid var(--border-primary);
            box-shadow: 0 8px 32px var(--shadow-heavy);
            display: flex;
            gap: 8px;
        }
        
        .nav-item {
            padding: 12px 18px;
            background: var(--bg-secondary);
            border: 1px solid var(--border-primary);
            border-radius: 18px;
            color: var(--text-secondary);
            text-decoration: none;
            font-weight: 500;
            font-size: 0.9rem;
            transition: all 0.3s ease;
            cursor: pointer;
        }
        
        .nav-item:hover, .nav-item.active {
            background: var(--accent-color);
            color: var(--bg-primary);
            border-color: var(--accent-color);
            transform: translateY(-2px);
            box-shadow: 0 4px 16px rgba(88, 166, 255, 0.3);
        }
        
        .stApp {
            background-color: var(--bg-primary) !important;
            color: var(--text-primary) !important;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            padding-top: 80px;
        }
        
        /* Add all other styles from your original CSS here */
        
    </style>
    """, unsafe_allow_html=True)

    # Navigation Bar with proper routing
    st.markdown("""
    <div class="nav-bar">
        <div class="nav-item active" onclick="window.location.href = '/'">🏠 Home</div>
        <div class="nav-item" onclick="window.location.href = '?page=what_if'">❓ What If</div>
        <div class="nav-item" onclick="window.location.href = '?page=history'">📚 History</div>
    </div>
    """, unsafe_allow_html=True)

    # Helper functions (include all from your original file)
    def save_to_history(analysis_data, image_data):
        if not redis_client:
            return False
        
        try:
            timestamp = datetime.now().isoformat()
            content_hash = hashlib.md5(json.dumps(analysis_data, sort_keys=True).encode()).hexdigest()[:8]
            analysis_id = f"analysis_{timestamp}_{content_hash}"
            
            storage_data = {
                'id': analysis_id,
                'timestamp': timestamp,
                'analysis': json.dumps(analysis_data),
                'image_data': base64.b64encode(image_data).decode('utf-8'),
                'risk_level': analysis_data.get('risk_level', 'Unknown'),
                'threat_count': len(analysis_data.get('scam_phrases', []))
            }
            
            redis_client.hset(f"history:{analysis_id}", mapping=storage_data)
            redis_client.expire(f"history:{analysis_id}", 30 * 24 * 60 * 60)
            redis_client.zadd("history_index", {analysis_id: datetime.now().timestamp()})
            
            return True
        except Exception as e:
            st.error(f"Failed to save to history: {str(e)}")
            return False

    def create_share_urls(analysis_data, extracted_text):
        risk_level = analysis_data.get('risk_level', 'Unknown')
        threat_count = len(analysis_data.get('scam_phrases', []))
        
        share_text = f"🛡️ TruthLoop Analysis Results:\n\n"
        share_text += f"🚨 Risk Level: {risk_level}\n"
        share_text += f"⚠️ Threats Detected: {threat_count}\n\n"
        share_text += f"Analyzed with TruthLoop - Advanced Scam Detection\n"
        share_text += f"#ScamAwareness #CyberSecurity #TruthLoop"