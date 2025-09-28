import streamlit as st
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
from agents.llm_utils import generate_narration_from_json
from agents.image_utils import encode_image_to_base64, generate_starter_frame
from agents.detect_scam import detect_scam_text, ocr_with_openai
import urllib.parse

def main():
    """Main router function to handle navigation between pages"""

    # Initialize Redis connection
    # -----------------------------
    @st.cache_resource
    def init_redis():
        try:
            r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
            r.ping()
            return r
        except:
            st.error("⚠️ Redis connection failed. History feature will be disabled.")
            return None

    redis_client = init_redis()

    # -----------------------------
    # Page Configuration
    # -----------------------------
    st.set_page_config(
        page_title="TruthLoop Educational Bot",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    # -----------------------------
    # Initialize session state for page
    # -----------------------------
    if "page" not in st.session_state:
        st.session_state["page"] = st.query_params.get("page", ["home"])[0]

    # -----------------------------
    # Navigation Bar using buttons
    # -----------------------------
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("🏠 Home", key="home_nav"):
            st.session_state["page"] = "home"
    with col2:
        if st.button("❓ What If", key="what_if_nav"):
            st.session_state["page"] = "what_if"
    with col3:
        if st.button("📚 History", key="history_nav"):
            st.session_state["page"] = "history"

    # -----------------------------
    # Route to the appropriate page
    # -----------------------------
    page = st.session_state["page"]

    if page == "history":
        try:
            show_history_page()
        except NameError:
            st.error("History page not found.")
            show_home_page()
    elif page == "what_if":
        try:
            show_what_if()
        except NameError:
            st.error("What If page not found.")
            show_home_page()
    else:
        show_home_page()


def show_what_if():
    import streamlit as st
    import random
    from PIL import Image, ImageDraw, ImageFont
    import io

    # Page configuration
    st.set_page_config(
        page_title="TruthLoop - What If Scenarios", 
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    # CSS styling for what-if page
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
            --danger-bg: #2d1117;
            --danger-border: #5d1a21;
            --warning-color: #f0883e;
            --warning-bg: #2d1b0e;
            --warning-border: #5d2f0e;
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
            background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
            padding: 3rem 2rem;
            border-radius: 20px;
            color: var(--text-primary);
            text-align: center;
            margin-bottom: 2.5rem;
            box-shadow: 0 8px 32px var(--shadow-heavy);
            border: 1px solid var(--danger-border);
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
        
        /* Scenario cards */
        .scenario-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 2rem;
            max-width: 1200px;
            margin: 0 auto 3rem auto;
            padding: 0 1rem;
        }
        
        .scenario-card {
            background: var(--bg-card);
            border-radius: 20px;
            border: 1px solid var(--border-primary);
            overflow: hidden;
            transition: all 0.3s ease;
            box-shadow: 0 4px 20px var(--shadow-light);
            cursor: pointer;
        }
        
        .scenario-card:hover {
            transform: translateY(-8px);
            box-shadow: 0 16px 48px var(--shadow-medium);
            border-color: var(--danger-color);
        }
        
        .scenario-header {
            padding: 2rem;
            background: var(--danger-bg);
            border-bottom: 1px solid var(--danger-border);
        }
        
        .scenario-icon {
            font-size: 3rem;
            margin-bottom: 1rem;
            display: block;
        }
        
        .scenario-title {
            font-size: 1.4rem;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: 0.5rem;
        }
        
        .scenario-subtitle {
            color: var(--text-secondary);
            font-size: 1rem;
        }
        
        .scenario-body {
            padding: 2rem;
        }
        
        .scenario-description {
            color: var(--text-secondary);
            line-height: 1.6;
            margin-bottom: 2rem;
            font-size: 1.1rem;
        }
        
        .consequence-item {
            display: flex;
            align-items: flex-start;
            margin-bottom: 1rem;
            padding: 1rem;
            background: var(--bg-secondary);
            border-radius: 12px;
            border-left: 4px solid var(--danger-color);
        }
        
        .consequence-icon {
            font-size: 1.2rem;
            margin-right: 0.75rem;
            margin-top: 0.2rem;
            flex-shrink: 0;
        }
        
        .consequence-text {
            color: var(--text-primary);
            font-weight: 500;
        }
        
        .severity-badge {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 12px;
            font-size: 0.8rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-left: auto;
        }
        
        .severity-high {
            background: rgba(248, 81, 73, 0.2);
            color: var(--danger-color);
            border: 1px solid var(--danger-color);
        }
        
        .severity-medium {
            background: rgba(240, 136, 62, 0.2);
            color: var(--warning-color);
            border: 1px solid var(--warning-color);
        }
        
        .severity-low {
            background: rgba(86, 211, 100, 0.2);
            color: var(--success-color);
            border: 1px solid var(--success-color);
        }
        
        /* Interactive scenario modal */
        .scenario-modal {
            background: var(--bg-card);
            border-radius: 20px;
            border: 1px solid var(--border-primary);
            box-shadow: 0 20px 60px var(--shadow-heavy);
            max-width: 800px;
            margin: 2rem auto;
        }
        
        .modal-header {
            padding: 2rem;
            background: var(--danger-bg);
            border-bottom: 1px solid var(--danger-border);
            border-radius: 20px 20px 0 0;
        }
        
        .modal-body {
            padding: 2rem;
        }
        
        .timeline-container {
            position: relative;
            margin: 2rem 0;
        }
        
        .timeline-item {
            display: flex;
            margin-bottom: 2rem;
            position: relative;
        }
        
        .timeline-marker {
            width: 40px;
            height: 40px;
            background: var(--danger-color);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            margin-right: 1.5rem;
            flex-shrink: 0;
            position: relative;
            z-index: 1;
        }
        
        .timeline-content {
            flex-grow: 1;
            background: var(--bg-secondary);
            padding: 1.5rem;
            border-radius: 12px;
            border: 1px solid var(--border-primary);
        }
        
        .timeline-title {
            font-size: 1.1rem;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 0.5rem;
        }
        
        .timeline-description {
            color: var(--text-secondary);
            line-height: 1.5;
        }
        
        /* Prevention tips */
        .prevention-container {
            background: var(--success-bg);
            border: 1px solid var(--success-color);
            border-radius: 16px;
            padding: 2rem;
            margin: 2rem auto;
            max-width: 800px;
        }
        
        .prevention-title {
            color: var(--success-color);
            font-size: 1.4rem;
            font-weight: 700;
            margin-bottom: 1.5rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .prevention-list {
            list-style: none;
            padding: 0;
            margin: 0;
        }
        
        .prevention-item {
            display: flex;
            align-items: flex-start;
            margin-bottom: 1rem;
            color: var(--text-primary);
        }
        
        .prevention-icon {
            color: var(--success-color);
            margin-right: 0.75rem;
            margin-top: 0.2rem;
        }
        
        /* Statistics */
        .stats-container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1.5rem;
            margin: 2rem auto;
            max-width: 800px;
        }
        
        .stat-card {
            background: var(--bg-secondary);
            padding: 2rem;
            border-radius: 16px;
            border: 1px solid var(--border-primary);
            text-align: center;
            transition: all 0.3s ease;
        }
        
        .stat-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 12px 32px var(--shadow-medium);
        }
        
        .stat-value {
            font-size: 2.5rem;
            font-weight: 700;
            color: var(--danger-color);
            margin-bottom: 0.5rem;
            display: block;
        }
        
        .stat-label {
            color: var(--text-secondary);
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        /* Action buttons */
        .action-buttons {
            display: flex;
            justify-content: center;
            gap: 1rem;
            margin: 2rem 0;
            flex-wrap: wrap;
        }
        
        .action-btn {
            padding: 1rem 2rem;
            border-radius: 12px;
            border: none;
            font-weight: 600;
            font-size: 1rem;
            cursor: pointer;
            transition: all 0.3s ease;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .primary-btn {
            background: var(--accent-color);
            color: var(--bg-primary);
        }
        
        .primary-btn:hover {
            background: var(--primary-color);
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(88, 166, 255, 0.3);
        }
        
        .secondary-btn {
            background: var(--bg-secondary);
            color: var(--text-primary);
            border: 1px solid var(--border-primary);
        }
        
        .secondary-btn:hover {
            background: var(--bg-elevated);
            border-color: var(--accent-color);
            transform: translateY(-2px);
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
            
            .scenario-grid {
                grid-template-columns: 1fr;
                gap: 1.5rem;
            }
            
            .header-title {
                font-size: 2rem;
            }
            
            .stats-container {
                grid-template-columns: 1fr;
            }
            
            .action-buttons {
                flex-direction: column;
                align-items: center;
            }
            
            .action-btn {
                width: 100%;
                max-width: 300px;
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
        <div class="nav-item active">❓ What If</div>
        <div class="nav-item" onclick="window.open('?page=history', '_self')">📚 History</div>
    </div>
    """, unsafe_allow_html=True)

    # Header
    st.markdown("""
    <div class="header-container">
        <div class="header-title">❓ What If You Fall For It?</div>
        <div class="header-subtitle">Understanding the real-world consequences of scams and cyber threats</div>
    </div>
    """, unsafe_allow_html=True)

    # Scam scenarios data
    SCAM_SCENARIOS = {
        "phishing": {
            "icon": "🎣",
            "title": "Phishing Email Scam",
            "subtitle": "Clicking that suspicious link",
            "description": "You receive an urgent email claiming to be from your bank, asking you to verify your account by clicking a link and entering your credentials.",
            "consequences": [
                {"icon": "💳", "text": "Bank account drained within hours", "severity": "high"},
                {"icon": "🆔", "text": "Identity stolen and used for fraud", "severity": "high"},
                {"icon": "📧", "text": "Email account compromised and used to scam friends", "severity": "medium"},
                {"icon": "🏠", "text": "Personal information sold on dark web", "severity": "medium"},
                {"icon": "📱", "text": "Phone bombarded with scam calls", "severity": "low"}
            ],
            "timeline": [
                {"step": 1, "title": "Initial Click", "desc": "You click the malicious link and enter your login credentials"},
                {"step": 2, "title": "Account Compromise", "desc": "Scammers immediately access your accounts and gather personal information"},
                {"step": 3, "title": "Financial Theft", "desc": "Money is transferred out of your accounts to untraceable locations"},
                {"step": 4, "title": "Identity Theft", "desc": "Your personal information is used to open new accounts and make purchases"},
                {"step": 5, "title": "Long-term Impact", "desc": "Credit score damaged, ongoing financial recovery, and emotional stress"}
            ],
            "stats": [
                {"value": "$4.2B", "label": "Lost to phishing in 2022"},
                {"value": "90%", "label": "Data breaches start with phishing"},
                {"value": "6 months", "label": "Average recovery time"}
            ]
        },
        "romance": {
            "icon": "💕",
            "title": "Romance Scam",
            "subtitle": "Falling for fake love online",
            "description": "You meet someone attractive online who quickly professes love and then asks for money due to an emergency or travel expenses.",
            "consequences": [
                {"icon": "💰", "text": "Life savings completely drained", "severity": "high"},
                {"icon": "💔", "text": "Severe emotional trauma and depression", "severity": "high"},
                {"icon": "👥", "text": "Embarrassment affects relationships with family/friends", "severity": "medium"},
                {"icon": "🏥", "text": "Need for professional counseling", "severity": "medium"},
                {"icon": "⚖️", "text": "Legal complications if used as money mule", "severity": "high"}
            ],
            "timeline": [
                {"step": 1, "title": "Initial Contact", "desc": "Scammer creates fake profile and initiates romantic conversation"},
                {"step": 2, "title": "Love Bombing", "desc": "Excessive attention and declarations of love build emotional dependency"},
                {"step": 3, "title": "First Request", "desc": "Small financial request for 'emergency' to test willingness"},
                {"step": 4, "title": "Escalation", "desc": "Larger requests for travel, visas, or family emergencies"},
                {"step": 5, "title": "Devastating Loss", "desc": "Victim realizes the truth after losing thousands of dollars"}
            ],
            "stats": [
                {"value": "$547M", "label": "Lost to romance scams in 2021"},
                {"value": "24,000", "label": "Victims reported in 2021"},
                {"value": "$2,400", "label": "Median loss per victim"}
            ]
        },
        "investment": {
            "icon": "📈",
            "title": "Investment Scam",
            "subtitle": "Too-good-to-be-true returns",
            "description": "You're offered an exclusive investment opportunity promising guaranteed high returns with minimal risk.",
            "consequences": [
                {"icon": "🏠", "text": "Retirement funds completely lost", "severity": "high"},
                {"icon": "👨‍👩‍👧‍👦", "text": "Family's financial security destroyed", "severity": "high"},
                {"icon": "🎓", "text": "Children's college funds gone", "severity": "high"},
                {"icon": "😰", "text": "Stress leads to health problems", "severity": "medium"},
                {"icon": "💼", "text": "Forced to work years past retirement", "severity": "medium"}
            ],
            "timeline": [
                {"step": 1, "title": "Initial Pitch", "desc": "Convincing presentation of exclusive investment opportunity"},
                {"step": 2, "title": "Small Success", "desc": "Small initial returns build confidence and trust"},
                {"step": 3, "title": "Pressure to Invest More", "desc": "Urgency tactics used to get larger investments"},
                {"step": 4, "title": "Maximum Investment", "desc": "Life savings and borrowed money invested"},
                {"step": 5, "title": "Scheme Collapse", "desc": "Scammers disappear with all invested money"}
            ],
            "stats": [
                {"value": "$3.8B", "label": "Lost to investment fraud in 2022"},
                {"value": "67", "label": "Median age of victims"},
                {"value": "$70K", "label": "Average loss per victim"}
            ]
        },
        "tech_support": {
            "icon": "💻",
            "title": "Tech Support Scam",
            "subtitle": "Fake computer virus warnings",
            "description": "You receive a pop-up warning about viruses on your computer and call the provided number for help.",
            "consequences": [
                {"icon": "🔐", "text": "Complete access to your computer given to criminals", "severity": "high"},
                {"icon": "📸", "text": "Personal photos and documents stolen", "severity": "medium"},
                {"icon": "🏪", "text": "Online shopping accounts compromised", "severity": "medium"},
                {"icon": "💾", "text": "Malware installed for ongoing monitoring", "severity": "high"},
                {"icon": "💳", "text": "Expensive fake software purchases", "severity": "medium"}
            ],
            "timeline": [
                {"step": 1, "title": "Fake Warning", "desc": "Pop-up appears claiming your computer is infected"},
                {"step": 2, "title": "Phone Call", "desc": "You call the number and speak to fake tech support"},
                {"step": 3, "title": "Remote Access", "desc": "Scammer convinces you to install remote access software"},
                {"step": 4, "title": "Fake Fix", "desc": "Scammer pretends to fix problems while stealing data"},
                {"step": 5, "title": "Ongoing Exploitation", "desc": "Your computer remains compromised for future attacks"}
            ],
            "stats": [
                {"value": "143,000", "label": "Tech support scam victims in 2021"},
                {"value": "$347M", "label": "Total losses in 2021"},
                {"value": "60+", "label": "Primary age group targeted"}
            ]
        }
    }

    def display_scenario_card(scenario_type, scenario_data):
        """Display an individual scenario card"""
        
        # Create columns for the card layout
        card_container = st.container()
        
        with card_container:
            # Use expander for interactive experience
            with st.expander(f"{scenario_data['icon']} {scenario_data['title']} - Click to explore consequences"):
                
                # Scenario description
                st.markdown(f"""
                <div class="scenario-description">
                    <strong>The Scenario:</strong> {scenario_data['description']}
                </div>
                """, unsafe_allow_html=True)
                
                # Consequences
                st.markdown("### 🚨 What Could Happen:")
                
                for consequence in scenario_data['consequences']:
                    severity_class = f"severity-{consequence['severity']}"
                    st.markdown(f"""
                    <div class="consequence-item">
                        <span class="consequence-icon">{consequence['icon']}</span>
                        <span class="consequence-text">{consequence['text']}</span>
                        <span class="severity-badge {severity_class}">{consequence['severity'].upper()}</span>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Timeline
                st.markdown("### ⏱️ How It Unfolds:")
                
                for timeline_item in scenario_data['timeline']:
                    st.markdown(f"""
                    <div class="timeline-item">
                        <div class="timeline-marker">{timeline_item['step']}</div>
                        <div class="timeline-content">
                            <div class="timeline-title">{timeline_item['title']}</div>
                            <div class="timeline-description">{timeline_item['desc']}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Statistics
                st.markdown("### 📊 Real-World Impact:")
                
                cols = st.columns(len(scenario_data['stats']))
                for i, stat in enumerate(scenario_data['stats']):
                    with cols[i]:
                        st.metric(stat['label'], stat['value'])

    # Main content - Display all scenarios
    st.markdown("## 🎭 Common Scam Scenarios")
    st.markdown("Explore these real-world scenarios to understand the devastating impact of falling for scams:")

    # Display scenarios in a grid
    col1, col2 = st.columns(2)

    scenarios = list(SCAM_SCENARIOS.items())
    for i, (scenario_type, scenario_data) in enumerate(scenarios):
        target_col = col1 if i % 2 == 0 else col2
        
        with target_col:
            display_scenario_card(scenario_type, scenario_data)

    # Prevention tips section
    st.markdown("""
    <div class="prevention-container">
        <div class="prevention-title">
            🛡️ How to Protect Yourself
        </div>
        <ul class="prevention-list">
            <li class="prevention-item">
                <span class="prevention-icon">✅</span>
                <strong>Verify independently:</strong> Always check claims through official channels
            </li>
            <li class="prevention-item">
                <span class="prevention-icon">✅</span>
                <strong>Think before you click:</strong> Hover over links to see the real destination
            </li>
            <li class="prevention-item">
                <span class="prevention-icon">✅</span>
                <strong>Trust your instincts:</strong> If something feels too good to be true, it probably is
            </li>
            <li class="prevention-item">
                <span class="prevention-icon">✅</span>
                <strong>Enable 2FA:</strong> Use two-factor authentication on all important accounts
            </li>
            <li class="prevention-item">
                <span class="prevention-icon">✅</span>
                <strong>Stay educated:</strong> Keep up with the latest scam tactics and warnings
            </li>
            <li class="prevention-item">
                <span class="prevention-icon">✅</span>
                <strong>Ask for help:</strong> Consult trusted friends or family before making financial decisions
            </li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    # Action buttons
    st.markdown("""
    <div class="action-buttons">
        <button class="action-btn primary-btn" onclick="window.open('/', '_self')">
            🏠 Test Your Images for Scams
        </button>
        <button class="action-btn secondary-btn" onclick="window.open('?page=history', '_self')">
            📚 View Your Analysis History
        </button>
    </div>
    """, unsafe_allow_html=True)

    # Footer with emergency resources
    st.markdown("""
    ---

    ### 🚨 If You've Been Scammed:

    **Immediate Actions:**
    - Contact your bank and credit card companies immediately
    - File a report with the FTC at reportfraud.ftc.gov
    - Report to your local police department
    - Change all passwords and enable 2FA
    - Monitor your credit reports closely

    **Support Resources:**
    - **AARP Fraud Watch Network:** 1-877-908-3360
    - **FTC Consumer Sentinel:** consumer.ftc.gov
    - **FBI Internet Crime Complaint Center:** ic3.gov
    - **Crisis Text Line:** Text HOME to 741741

    Remember: Being scammed is not your fault, and help is available.
    """)

    # Footer
    st.markdown("""
    <div style="text-align: center; padding: 2rem; color: var(--text-muted); border-top: 1px solid var(--border-primary); margin-top: 3rem;">
        <p>🛡️ TruthLoop Educational Bot | Understanding Scam Consequences</p>
    </div>
    """, unsafe_allow_html=True)

def show_history_page():
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

def show_home_page():

        # Enhanced CSS with navigation bar and sharing buttons
        st.markdown("""
        <style>
            /* Import modern font */
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
            
            /* Dark theme color palette */
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
            
            /* Floating Navigation Bar */
            .nav-bar {
                position: fixed;
                bottom: 20px;       /* move to bottom */
                left: 50%;          /* center horizontally */
                transform: translateX(-50%);
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
                

            /* Global styling */
            .stApp {
                background-color: var(--bg-primary) !important;
                color: var(--text-primary) !important;
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
                padding-top: 80px; /* Space for nav bar */
            }
            
            .main {
                padding: 1.5rem 2rem;
                background-color: var(--bg-primary);
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
            
            /* Upload section styling */
            .upload-section {
                background: var(--bg-secondary);
                color: var(--text-primary);
                padding: 3rem 2rem;
                border-radius: 16px;
                border: 2px dashed var(--border-primary);
                text-align: center;
                margin-bottom: 2rem;
                transition: all 0.3s ease;
                box-shadow: 0 4px 20px var(--shadow-light);
            }
            
            .upload-section:hover {
                border-color: var(--accent-color);
                background: var(--bg-tertiary);
                box-shadow: 0 8px 32px var(--shadow-medium);
                transform: translateY(-2px);
            }
            
            .upload-section h3 {
                color: var(--text-primary) !important;
                margin-bottom: 1rem;
                font-weight: 600;
                font-size: 1.5rem;
            }
            
            .upload-section p {
                color: var(--text-secondary) !important;
                font-size: 1.1rem;
                line-height: 1.5;
            }
            
            /* Card containers */
            .results-container, .metric-container, .content-card {
                background: var(--bg-card);
                color: var(--text-primary);
                border-radius: 16px;
                box-shadow: 0 4px 20px var(--shadow-light);
                border: 1px solid var(--border-primary);
                transition: all 0.3s ease;
                margin: 0 auto; /* Center the cards */
                max-width: 1200px; /* Limit maximum width */
            }
            
            .results-container {
                padding: 2rem;
                margin-bottom: 2rem;
                border-left: 4px solid var(--accent-color);
            }
            
            .results-container:hover {
                box-shadow: 0 8px 32px var(--shadow-medium);
                transform: translateY(-2px);
            }
            
            /* Action buttons container */
            .action-buttons {
                display: flex;
                justify-content: center;
                gap: 1rem;
                margin: 2rem 0;
                flex-wrap: wrap;
            }
            
            .action-btn {
                padding: 12px 24px;
                border-radius: 12px;
                border: none;
                font-weight: 600;
                font-size: 1rem;
                cursor: pointer;
                transition: all 0.3s ease;
                text-decoration: none;
                display: inline-flex;
                align-items: center;
                gap: 8px;
                min-width: 140px;
                justify-content: center;
            }
            
            .post-btn {
                background: linear-gradient(135deg, #25D366 0%, #128C7E 100%);
                color: white;
            }
            
            .post-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 24px rgba(37, 211, 102, 0.3);
            }
            
            .save-btn {
                background: var(--accent-color);
                color: var(--bg-primary);
            }
            
            .save-btn:hover {
                background: var(--primary-color);
                transform: translateY(-2px);
                box-shadow: 0 8px 24px rgba(88, 166, 255, 0.3);
            }
            
            .share-options {
                background: var(--bg-secondary);
                border-radius: 12px;
                padding: 1.5rem;
                margin: 1rem 0;
                border: 1px solid var(--border-primary);
                text-align: center;
            }
            
            .share-btn {
                margin: 0 8px;
                padding: 10px 20px;
                border-radius: 8px;
                border: none;
                font-weight: 500;
                cursor: pointer;
                transition: all 0.3s ease;
                text-decoration: none;
                display: inline-flex;
                align-items: center;
                gap: 6px;
            }
            
            .telegram-btn {
                background: #0088cc;
                color: white;
            }
            
            .whatsapp-btn {
                background: #25D366;
                color: white;
            }
            
            .instagram-btn {
                background: linear-gradient(45deg, #f09433 0%,#e6683c 25%,#dc2743 50%,#cc2366 75%,#bc1888 100%);
                color: white;
            }
            
            .share-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            }
            
            /* Step indicators */
            .step-indicator {
                display: flex;
                align-items: center;
                margin-bottom: 1.5rem;
            }
            
            .step-number {
                background: var(--accent-color);
                color: var(--bg-primary);
                border-radius: 50%;
                width: 36px;
                height: 36px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: 700;
                margin-right: 1rem;
                font-size: 1rem;
                box-shadow: 0 4px 12px rgba(88, 166, 255, 0.3);
            }
            
            .step-title {
                font-size: 1.5rem;
                font-weight: 600;
                color: var(--text-primary) !important;
                letter-spacing: 0.3px;
            }
            
            /* Success indicators */
            .success-container {
                background: var(--success-bg);
                border: 1px solid var(--success-border);
                border-radius: 12px;
                padding: 2rem;
                text-align: center;
                margin: 2rem 0;
                box-shadow: 0 4px 16px var(--shadow-light);
                max-width: 800px;
                margin-left: auto;
                margin-right: auto;
            }
            
            .success-container h3 {
                color: var(--success-color) !important;
                font-size: 1.5rem;
                margin-bottom: 0.5rem;
            }
            
            .success-container p {
                color: var(--text-secondary) !important;
                font-size: 1.1rem;
            }
            
            /* Metric cards */
            .metric-container {
                padding: 2rem 1.5rem;
                text-align: center;
                margin: 0.75rem;
                background: var(--bg-elevated);
                border: 1px solid var(--border-secondary);
            }
            
            .metric-container:hover {
                border-color: var(--accent-color);
                box-shadow: 0 8px 24px var(--shadow-medium);
                transform: translateY(-3px);
            }
            
            .metric-value {
                font-size: 2.5rem;
                font-weight: 700;
                margin-bottom: 0.5rem;
                background: linear-gradient(135deg, var(--accent-color), var(--primary-color));
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }
            
            .metric-label {
                color: var(--text-secondary) !important;
                font-size: 0.9rem;
                text-transform: uppercase;
                letter-spacing: 1px;
                font-weight: 500;
            }
            
            /* Threat detection specific styling */
            .threat-metrics .metric-container {
                border: 2px solid var(--danger-border);
                background: var(--danger-bg);
            }
            
            .threat-metrics .metric-value.high-risk {
                color: var(--danger-color) !important;
                text-shadow: 0 0 10px rgba(248, 81, 73, 0.3);
            }
            
            .threat-metrics .metric-value.medium-risk {
                color: var(--warning-color) !important;
                text-shadow: 0 0 10px rgba(240, 136, 62, 0.3);
            }
            
            .threat-metrics .metric-value.low-risk {
                color: var(--success-color) !important;
                text-shadow: 0 0 10px rgba(86, 211, 100, 0.3);
            }
            
            /* Threat phrase highlighting */
            .threat-phrase {
                background: var(--threat-bg) !important;
                color: var(--threat-highlight) !important;
                padding: 0.2rem 0.4rem;
                border-radius: 6px;
                border: 1px solid var(--threat-border);
                font-weight: 600;
                text-shadow: 0 0 8px rgba(255, 107, 107, 0.4);
                box-shadow: 0 2px 8px rgba(255, 107, 107, 0.2);
                animation: subtle-pulse 2s infinite;
            }
            
            @keyframes subtle-pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.8; }
            }
            
            /* Educational content */
            .educational-content {
                background: var(--bg-secondary);
                color: var(--text-primary);
                padding: 2rem;
                border-radius: 12px;
                border-left: 4px solid var(--primary-color);
                margin: 1rem 0;
                box-shadow: 0 4px 16px var(--shadow-light);
            }
            
            .educational-content h4 {
                color: var(--text-primary) !important;
                margin-bottom: 1.5rem;
                font-size: 1.3rem;
                font-weight: 600;
            }
            
            .educational-content p {
                color: var(--text-secondary) !important;
                line-height: 1.7;
                font-size: 1.1rem;
            }
            
            /* Image containers */
            .image-container {
                border-radius: 16px;
                overflow: hidden;
                box-shadow: 0 8px 32px var(--shadow-heavy);
                margin: 1.5rem auto;
                border: 1px solid var(--border-primary);
                background: var(--bg-secondary);
                padding: 0.5rem;
                max-width: 800px;
            }
            
            /* Instructions */
            .instructions-container {
                text-align: center;
                padding: 4rem 2rem;
                color: var(--text-secondary);
                background: var(--bg-secondary);
                border-radius: 16px;
                border: 1px solid var(--border-primary);
                box-shadow: 0 4px 20px var(--shadow-light);
                max-width: 800px;
                margin: 0 auto;
            }
            
            .instructions-container h3 {
                color: var(--text-primary) !important;
                margin-bottom: 1.5rem;
                font-size: 1.8rem;
                font-weight: 600;
            }
            
            .instructions-container p {
                color: var(--text-secondary) !important;
                font-size: 1.2rem;
                line-height: 1.6;
                max-width: 600px;
                margin: 0 auto;
            }
            
            .instructions-container strong {
                color: var(--text-primary) !important;
                font-weight: 600;
            }
            
            /* Footer */
            .footer-container {
                text-align: center;
                padding: 2.5rem;
                color: var(--text-muted);
                border-top: 1px solid var(--border-primary);
                margin-top: 3rem;
                background: var(--bg-secondary);
                border-radius: 16px 16px 0 0;
                max-width: 1200px;
                margin-left: auto;
                margin-right: auto;
                margin-top: 3rem;
            }
            
            .footer-container p {
                color: var(--text-muted) !important;
                font-size: 1rem;
            }
            
            /* Streamlit component overrides */
            .stTabs [data-baseweb="tab-list"] {
                gap: 8px;
                background: var(--bg-secondary);
                border-radius: 12px;
                padding: 0.5rem;
                justify-content: center;
            }
            
            .stTabs [data-baseweb="tab"] {
                background: var(--bg-tertiary) !important;
                border: 1px solid var(--border-primary) !important;
                border-radius: 8px !important;
                color: var(--text-secondary) !important;
                padding: 0.75rem 1.5rem !important;
                font-weight: 500 !important;
            }
            
            .stTabs [data-baseweb="tab"]:hover {
                background: var(--bg-elevated) !important;
                border-color: var(--accent-color) !important;
                color: var(--text-primary) !important;
            }
            
            .stTabs [aria-selected="true"] {
                background: var(--accent-color) !important;
                color: var(--bg-primary) !important;
                border-color: var(--accent-color) !important;
            }
            
            .stExpander {
                background: var(--bg-card) !important;
                border: 1px solid var(--border-primary) !important;
                border-radius: 12px !important;
                max-width: 1000px;
                margin: 0 auto;
            }
            
            .stExpander [data-testid="stExpanderToggleIcon"] {
                color: var(--accent-color) !important;
            }
            
            /* Hide Streamlit branding */
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            
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
                
                .action-buttons {
                    flex-direction: column;
                    align-items: center;
                }
                
                .action-btn {
                    width: 100%;
                    max-width: 300px;
                }
                
                .header-title {
                    font-size: 2rem;
                }
            }
            
            /* Smooth transitions */
            * {
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            }
        </style>
        """, unsafe_allow_html=True)


        # Helper function to save analysis to Redis
        def save_to_history(analysis_data, image_data):
            if not redis_client:
                return False
            
            try:
                # Create unique ID based on timestamp and content hash
                timestamp = datetime.now().isoformat()
                content_hash = hashlib.md5(json.dumps(analysis_data, sort_keys=True).encode()).hexdigest()[:8]
                analysis_id = f"analysis_{timestamp}_{content_hash}"
                
                # Prepare data for storage
                storage_data = {
                    'id': analysis_id,
                    'timestamp': timestamp,
                    'analysis': json.dumps(analysis_data),
                    'image_data': base64.b64encode(image_data).decode('utf-8'),
                    'risk_level': analysis_data.get('risk_level', 'Unknown'),
                    'threat_count': len(analysis_data.get('scam_phrases', []))
                }
                
                # Save to Redis with expiration (30 days)
                redis_client.hset(f"history:{analysis_id}", mapping=storage_data)
                redis_client.expire(f"history:{analysis_id}", 30 * 24 * 60 * 60)  # 30 days
                
                # Add to index
                redis_client.zadd("history_index", {analysis_id: datetime.now().timestamp()})
                
                return True
            except Exception as e:
                st.error(f"Failed to save to history: {str(e)}")
                return False

        # Helper function to create share URLs
        def create_share_urls(analysis_data, extracted_text):
            # Create a summary for sharing
            risk_level = analysis_data.get('risk_level', 'Unknown')
            threat_count = len(analysis_data.get('scam_phrases', []))
            
            share_text = f"🛡️ TruthLoop Analysis Results:\n\n"
            share_text += f"🚨 Risk Level: {risk_level}\n"
            share_text += f"⚠️ Threats Detected: {threat_count}\n\n"
            share_text += f"Analyzed with TruthLoop - Advanced Scam Detection\n"
            share_text += f"#ScamAwareness #CyberSecurity #TruthLoop"
            
            # URL encode the text
            encoded_text = urllib.parse.quote(share_text)
            
            return {
                'telegram': f"https://t.me/share/url?url=https://truthloop.app&text={encoded_text}",
                'whatsapp': f"https://wa.me/?text={encoded_text}",
                'instagram': f"https://www.instagram.com/create/story" # Instagram stories require app
            }

        # -----------------------------
        # Header Section
        # -----------------------------
        st.markdown("""
        <div class="header-container">
            <div class="header-title">🛡️ TruthLoop</div>
            <div class="header-subtitle">Advanced Educational Scam Detection & Analysis</div>
        </div>
        """, unsafe_allow_html=True)

        # -----------------------------
        # Upload Section
        # -----------------------------
        uploaded_home = st.file_uploader("Upload an image", type=["jpg", "png", "jpeg"], label_visibility="collapsed")

        if uploaded_home:
            # Display uploaded image in a clean container
            st.markdown('<div class="image-container">', unsafe_allow_html=True)
            st.image(uploaded_home, caption="📤 Uploaded Image", use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

            # Read file once
            file_bytes = uploaded_.read()

            # Save uploaded image temporarily
            temp_input = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            temp_input.write(file_bytes)
            temp_input.flush()
            input_path = temp_input.name

            # Progress bar (no processing message after completion)
            progress_bar = st.progress(0)
            status_text = st.empty()

            # -----------------------------
            # OCR + Scam Detection
            # -----------------------------
            status_text.text("🔍 Extracting text from image...")
            progress_bar.progress(20)
            
            extracted_text = ocr_with_openai(file_bytes)
            
            status_text.text("🚨 Analyzing for threat indicators...")
            progress_bar.progress(40)
            
            scam_json = detect_scam_text(extracted_text)
            scam_phrases = scam_json.get("scam_phrases", [])
            risk_level = scam_json.get("risk_level", "Low")
            confidence = scam_json.get("confidence", 0)

            status_text.text("📚 Generating educational content...")
            progress_bar.progress(80)
            
            img_base64 = base64.b64encode(file_bytes).decode("utf-8")

            with ThreadPoolExecutor(max_workers=3) as executor:
                future_narration = executor.submit(generate_narration_from_json, scam_json)
                future_image = executor.submit(generate_starter_frame, extracted_text)

                narration = future_narration.result()
                edu_image_path = future_image.result()

            progress_bar.progress(100)
            
            # Clear processing indicators
            status_text.empty()
            progress_bar.empty()

            # Display threat detection results
            st.markdown("""
            <div class="results-container">
                <div class="step-indicator">
                    <div class="step-number">1</div>
                    <div class="step-title">🚨 Threat Detection Results</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Create threat-specific metrics
            col1, col2, col3 = st.columns(3)
            
            risk_class = f"{risk_level.lower()}-risk"
            risk_colors = {
                "High": "#f85149",
                "Medium": "#f0883e", 
                "Low": "#56d364"
            }
            
            with col1:
                st.markdown(f"""
                <div class="threat-metrics">
                    <div class="metric-container">
                        <div class="metric-value">{len(scam_phrases)}</div>
                        <div class="metric-label">Threat Phrases Detected</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="threat-metrics">
                    <div class="metric-container">
                        <div class="metric-value {risk_class}" style="color: {risk_colors.get(risk_level, '#56d364')} !important;">{risk_level}</div>
                        <div class="metric-label">Risk Level</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                <div class="threat-metrics">
                    <div class="metric-container">
                        <div class="metric-value">{confidence}%</div>
                        <div class="metric-label">Confidence Score</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # Display extracted text with highlighted threat phrases
            if extracted_text:
                st.markdown("""
                <div class="results-container">
                    <div class="step-indicator">
                        <div class="step-number">📝</div>
                        <div class="step-title">Extracted Text with Threat Highlighting</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Highlight threat phrases in the extracted text
                highlighted_text = extracted_text
                for phrase in scam_phrases:
                    if phrase and phrase.strip():
                        # Case-insensitive replacement with threat highlighting
                        import re
                        pattern = re.compile(re.escape(phrase), re.IGNORECASE)
                        highlighted_text = pattern.sub(f'<span class="threat-phrase">{phrase}</span>', highlighted_text)
                
                st.markdown(f"""
                <div class="content-card" style="padding: 1.5rem; margin: 1rem 0; background: var(--bg-secondary); border-radius: 12px; border: 1px solid var(--border-primary);">
                    <div style="color: var(--text-secondary); font-family: 'Courier New', monospace; line-height: 1.6; font-size: 1rem;">
                        {highlighted_text.replace(chr(10), '<br>')}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # Expandable detailed analysis
            with st.expander("🔍 View Detailed Threat Analysis", expanded=False):
                st.json(scam_json)

            # -----------------------------
            # Educational Content Display
            # -----------------------------
            st.markdown("""
            <div class="results-container">
                <div class="step-indicator">
                    <div class="step-number">2</div>
                    <div class="step-title">🎓 Educational Resources</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Tabbed interface for educational content
            tab1, tab2= st.tabs(["📖 Educational Explanation", "🎨 Visual Learning Guide"])
            
            with tab1:
                st.markdown(f"""
                <div class="educational-content">
                    <h4>🎓 Understanding the Threats</h4>
                    <p>{narration}</p>
                </div>
                """, unsafe_allow_html=True)
            
            with tab2:
                st.markdown('<div class="image-container">', unsafe_allow_html=True)
                st.image(Image.open(edu_image_path), caption="🎨 Educational Visual Guide", use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

            # Success message
            st.markdown("""
            <div class="success-container">
                <h3>🎉 Threat Analysis Complete!</h3>
                <p>Your image has been successfully analyzed for potential scams and threats. Review the highlighted indicators above to enhance your cybersecurity awareness.</p>
            </div>
            """, unsafe_allow_html=True)


                # Action buttons for Post and Save
            share_urls = create_share_urls(scam_json, extracted_text)
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📤 Share Analysis", key="post_btn", use_container_width=True):
                    st.markdown(f"""
                    <div class="share-options">
                        <h4 style="color: var(--text-primary); margin-bottom: 1rem;">Share Your Analysis</h4>
                        <a href="{share_urls['telegram']}" target="_blank" class="share-btn telegram-btn">
                            📱 Telegram
                        </a>
                        <a href="{share_urls['whatsapp']}" target="_blank" class="share-btn whatsapp-btn">
                            💬 WhatsApp
                        </a>
                        <a href="{share_urls['instagram']}" target="_blank" class="share-btn instagram-btn">
                            📸 Instagram
                        </a>
                    </div>
                    """, unsafe_allow_html=True)
            
            with col2:
                if st.button("💾 Save to History", key="save_btn", use_container_width=True):
                    if save_to_history(scam_json, file_bytes):
                        st.success("✅ Analysis saved to history!")
                    else:
                        st.error("❌ Failed to save to history. Redis connection required.")
            # -----------------------------
            # Cleanup temporary files
            # -----------------------------
            for file_path in [input_path, edu_image_path]:
                try:
                    os.unlink(file_path)
                except Exception:
                    pass

        else:
            # Instructions when no file is uploaded
            st.markdown("""
            <div class="instructions-container">
                <h3>🛡️ Get Started with Threat Detection</h3>
                <p>
                    Upload an image containing text to begin comprehensive scam and threat analysis.<br>
                    Our advanced AI will extract text, identify potential threats, and provide educational resources to enhance your cybersecurity awareness.
                </p>
                <div style="margin-top: 2rem;">
                    <strong>Supported formats:</strong> JPG, PNG, JPEG<br>
                    <strong>Max file size:</strong> 200MB<br>
                    <strong>Detection capabilities:</strong> Phishing, Scams, Social Engineering, Fraud
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Footer
        st.markdown("""
        <div class="footer-container">
            <p>🛡️ TruthLoop Educational Bot | Advanced Cybersecurity Threat Detection & Education</p>
        </div>
        """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()