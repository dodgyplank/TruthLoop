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
