import streamlit as st
import redis
import json
import base64
from datetime import datetime
from PIL import Image
import io

# Initialize Redis connection
@st.cache_resource
def init_redis():
    try:
        r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        r.ping()
        return r
    except:
        return None

redis_client = init_redis()

# Page configuration
st.set_page_config(
    page_title="TruthLoop - Analysis History", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS styling for history page
st.markdown("""
<style>
    /* Import the same styling as main app */
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
        --secondary-color: #1f6feb;
        --accent-color: #58a6ff;
        --danger-color: #f85149;
        --warning-color: #f0883e;
        --success-color: #56d364;
        --shadow-light: rgba(0, 0, 0, 0.12);
        --shadow-medium: rgba(0, 0, 0, 0.25);
        --shadow-heavy: rgba(0, 0, 0, 0.4);
    }
    
    .stApp {
        background-color: var(--bg-primary) !important;
        color: var(--text-primary) !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        padding-top: 80px;
    }
    
    /* Floating Navigation Bar */
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
    
    /* Header styling */
    .header-container {
        background: linear-gradient(135deg, var(--secondary-color) 0%, var(--primary-color) 100%);
        padding: 3rem 2rem;
        border-radius: 20px;
        color: var(--text-primary);
        text-align: center;
        margin-bottom: 2.5rem;
        box-shadow: 0 8px 32px var(--shadow-heavy);
        border: 1px solid var(--border-primary);
        max-width: 1200px;
        margin-left: auto;
        margin-right: auto;
        margin-bottom: 2.5rem;
    }
    
    .header-title {
        font-size: 3rem;
        font-weight: 700;
        margin-bottom: 0.75rem;
        color: var(--text-primary) !important;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }
    
    .header-subtitle {
        font-size: 1.3rem;
        opacity: 0.9;
        font-weight: 400;
        color: var(--text-primary) !important;
        letter-spacing: 0.5px;
    }
    
    /* History grid */
    .history-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
        gap: 1.5rem;
        max-width: 1200px;
        margin: 0 auto;
        padding: 0 1rem;
    }
    
    .history-card {
        background: var(--bg-card);
        border-radius: 16px;
        border: 1px solid var(--border-primary);
        overflow: hidden;
        transition: all 0.3s ease;
        cursor: pointer;
        box-shadow: 0 4px 20px var(--shadow-light);
    }
    
    .history-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 40px var(--shadow-medium);
        border-color: var(--accent-color);
    }
    
    .card-thumbnail {
        width: 100%;
        height: 200px;
        object-fit: cover;
        border-bottom: 1px solid var(--border-primary);
    }
    
    .card-content {
        padding: 1.5rem;
    }
    
    .card-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 0.5rem;
    }
    
    .card-meta {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
    }
    
    .card-date {
        color: var(--text-muted);
        font-size: 0.9rem;
    }
    
    .risk-badge {
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .risk-high {
        background: rgba(248, 81, 73, 0.2);
        color: var(--danger-color);
        border: 1px solid var(--danger-color);
    }
    
    .risk-medium {
        background: rgba(240, 136, 62, 0.2);
        color: var(--warning-color);
        border: 1px solid var(--warning-color);
    }
    
    .risk-low {
        background: rgba(86, 211, 100, 0.2);
        color: var(--success-color);
        border: 1px solid var(--success-color);
    }
    
    .card-stats {
        display: flex;
        gap: 1rem;
        font-size: 0.9rem;
        color: var(--text-secondary);
    }
    
    .stat-item {
        display: flex;
        align-items: center;
        gap: 0.25rem;
    }
    
    /* Modal styling */
    .modal-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.8);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 2000;
    }
    
    .modal-content {
        background: var(--bg-card);
        border-radius: 20px;
        max-width: 90vw;
        max-height: 90vh;
        overflow-y: auto;
        border: 1px solid var(--border-primary);
        box-shadow: 0 20px 60px var(--shadow-heavy);
    }
    
    .modal-header {
        padding: 2rem;
        border-bottom: 1px solid var(--border-primary);
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .modal-close {
        background: none;
        border: none;
        color: var(--text-secondary);
        font-size: 1.5rem;
        cursor: pointer;
        padding: 0.5rem;
        border-radius: 8px;
        transition: all 0.3s ease;
    }
    
    .modal-close:hover {
        background: var(--bg-secondary);
        color: var(--text-primary);
    }
    
    .modal-body {
        padding: 2rem;
    }
    
    /* Empty state */
    .empty-state {
        text-align: center;
        padding: 4rem 2rem;
        color: var(--text-secondary);
        background: var(--bg-secondary);
        border-radius: 16px;
        border: 1px solid var(--border-primary);
        box-shadow: 0 4px 20px var(--shadow-light);
        max-width: 600px;
        margin: 2rem auto;
    }
    
    .empty-state h3 {
        color: var(--text-primary) !important;
        margin-bottom: 1rem;
        font-size: 1.5rem;
    }
    
    .empty-state p {
        color: var(--text-secondary) !important;
        font-size: 1.1rem;
        line-height: 1.6;
    }
    
    .back-button {
        background: var(--accent-color);
        color: var(--bg-primary);
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
        margin-top: 1rem;
    }
    
    .back-button:hover {
        background: var(--primary-color);
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(88, 166, 255, 0.3);
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .nav-bar {
            position: relative;
            top: 0;
            right: 0;
            width: 100%;
            border-radius: 12px;
            margin-bottom: 1rem;
        }
        
        .stApp {
            padding-top: 20px;
        }
        
        .history-grid {
            grid-template-columns: 1fr;
            gap: 1rem;
        }
        
        .header-title {
            font-size: 2rem;
        }
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Navigation Bar
st.markdown("""
<div class="nav-bar">
    <div class="nav-item" onclick="window.open('/', '_self')">🏠 Home</div>
    <div class="nav-item" onclick="window.open('?page=what_if', '_self')">❓ What If</div>
    <div class="nav-item active">📚 History</div>
</div>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="header-container">
    <div class="header-title">📚 Analysis History</div>
    <div class="header-subtitle">Review your past threat detection analyses</div>
</div>
""", unsafe_allow_html=True)

def load_history():
    """Load analysis history from Redis"""
    if not redis_client:
        return []
    
    try:
        # Get all history IDs sorted by timestamp (newest first)
        history_ids = redis_client.zrevrange("history_index", 0, -1)
        
        history_items = []
        for history_id in history_ids:
            data = redis_client.hgetall(f"history:{history_id}")
            if data:
                # Parse the stored analysis
                analysis = json.loads(data['analysis'])
                data['analysis'] = analysis
                history_items.append(data)
        
        return history_items
    except Exception as e:
        st.error(f"Failed to load history: {str(e)}")
        return []

def display_history_grid(history_items):
    """Display history items in a grid layout"""
    if not history_items:
        st.markdown("""
        <div class="empty-state">
            <h3>📭 No Analysis History</h3>
            <p>You haven't performed any threat analyses yet.<br>
            Upload an image on the Home page to get started with threat detection.</p>
            <button class="back-button" onclick="window.open('/', '_self')">
                🏠 Go to Home
            </button>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Create grid layout using columns
    cols = st.columns(3)
    
    for i, item in enumerate(history_items):
        col_idx = i % 3
        
        with cols[col_idx]:
            # Parse timestamp for display
            try:
                timestamp = datetime.fromisoformat(item['timestamp'].replace('Z', '+00:00'))
                date_str = timestamp.strftime("%b %d, %Y")
                time_str = timestamp.strftime("%I:%M %p")
            except:
                date_str = "Unknown Date"
                time_str = ""
            
            # Get risk level styling
            risk_level = item['risk_level']
            risk_class = f"risk-{risk_level.lower()}"
            
            # Decode and display thumbnail
            try:
                image_data = base64.b64decode(item['image_data'])
                image = Image.open(io.BytesIO(image_data))
                
                # Create a unique key for each item
                button_key = f"history_item_{item['id']}"
                
                if st.button(f"📊 Analysis from {date_str}", key=button_key, use_container_width=True):
                    show_analysis_detail(item)
                
                # Display thumbnail
                st.image(image, use_container_width=True)
                
                # Display metadata
                st.markdown(f"""
                <div style="padding: 1rem; background: var(--bg-secondary); border-radius: 8px; margin-top: 0.5rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                        <span style="color: var(--text-muted); font-size: 0.9rem;">{time_str}</span>
                        <span class="risk-badge {risk_class}">{risk_level}</span>
                    </div>
                    <div style="color: var(--text-secondary); font-size: 0.9rem;">
                        <span>⚠️ {item['threat_count']} threats detected</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"Failed to load analysis: {str(e)}")

def show_analysis_detail(item):
    """Show detailed analysis in an expander"""
    analysis = item['analysis']
    
    st.markdown(f"""
    ### 🔍 Detailed Analysis - {datetime.fromisoformat(item['timestamp'].replace('Z', '+00:00')).strftime("%B %d, %Y at %I:%M %p")}
    """)
    
    # Display metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("🚨 Risk Level", analysis.get('risk_level', 'Unknown'))
    
    with col2:
        st.metric("⚠️ Threats Detected", len(analysis.get('scam_phrases', [])))
    
    with col3:
        st.metric("🎯 Confidence", f"{analysis.get('confidence', 0)}%")
    
    # Display image
    try:
        image_data = base64.b64decode(item['image_data'])
        image = Image.open(io.BytesIO(image_data))
        st.image(image, caption="Original Image", use_container_width=True)
    except:
        st.error("Failed to load image")
    
    # Display threat phrases if any
    scam_phrases = analysis.get('scam_phrases', [])
    if scam_phrases:
        st.markdown("#### 🚨 Detected Threat Phrases:")
        for phrase in scam_phrases:
            st.markdown(f"- `{phrase}`")
    
    # Display full analysis
    with st.expander("🔍 View Complete Analysis Data"):
        st.json(analysis)

# Main content
if redis_client:
    # Load and display history
    history_items = load_history()
    
    # Display statistics
    if history_items:
        total_analyses = len(history_items)
        high_risk_count = sum(1 for item in history_items if item['risk_level'] == 'High')
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📊 Total Analyses", total_analyses)
        with col2:
            st.metric("🚨 High Risk Detected", high_risk_count)
        with col3:
            st.metric("📈 Success Rate", f"{max(0, 100 - (high_risk_count/total_analyses*100) if total_analyses > 0 else 0):.1f}%")
        
        st.markdown("---")
    
    # Display history grid
    display_history_grid(history_items)
    
else:
    st.markdown("""
    <div class="empty-state">
        <h3>⚠️ History Unavailable</h3>
        <p>Redis connection is required to store and retrieve analysis history.<br>
        Please ensure Redis is running and properly configured.</p>
        <button class="back-button" onclick="window.open('/', '_self')">
            🏠 Go to Home
        </button>
    </div>
    """, unsafe_allow_html=True)

# Footer
st.markdown("""
<div style="text-align: center; padding: 2rem; color: var(--text-muted); border-top: 1px solid var(--border-primary); margin-top: 3rem;">
    <p>🛡️ TruthLoop Educational Bot | Analysis History</p>
</div>
""", unsafe_allow_html=True)