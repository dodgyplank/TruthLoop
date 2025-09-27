import streamlit as st
from PIL import Image
import io
import base64
import tempfile
import os
from concurrent.futures import ThreadPoolExecutor
from agents.llm_utils import generate_narration_from_json, generate_educational_json
from agents.image_utils import encode_image_to_base64, generate_starter_frame
from agents.detect_scam import detect_scam_text, highlight_scam_text, ocr_with_openai

# -----------------------------
# Page Configuration & Styling
# -----------------------------
st.set_page_config(
    page_title="TruthLoop Educational Bot", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Dark Theme CSS with consistent styling and threat highlighting
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
    
    /* Global styling */
    .stApp {
        background-color: var(--bg-primary) !important;
        color: var(--text-primary) !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
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
    
    /* Processing indicators */
    .processing-container {
        background: var(--warning-bg);
        border: 1px solid var(--warning-border);
        border-radius: 12px;
        padding: 2rem;
        text-align: center;
        margin: 2rem 0;
        box-shadow: 0 4px 16px var(--shadow-light);
    }
    
    .processing-text {
        color: var(--warning-color) !important;
        font-weight: 500;
        font-size: 1.1rem;
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
    
    /* JSON container */
    .json-container {
        background: var(--bg-tertiary);
        border-radius: 12px;
        padding: 1.5rem;
        border-left: 3px solid var(--accent-color);
        box-shadow: inset 0 2px 8px var(--shadow-light);
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
        margin: 1.5rem 0;
        border: 1px solid var(--border-primary);
        background: var(--bg-secondary);
        padding: 0.5rem;
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
    }
    
    .stExpander [data-testid="stExpanderToggleIcon"] {
        color: var(--accent-color) !important;
    }
    
    .stProgress .st-bo {
        background: var(--bg-tertiary) !important;
        border-radius: 10px !important;
    }
    
    .stProgress .st-bp {
        background: linear-gradient(90deg, var(--accent-color), var(--primary-color)) !important;
        border-radius: 10px !important;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Smooth transitions */
    * {
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
</style>
""", unsafe_allow_html=True)

# JavaScript for enhanced threat phrase highlighting
st.markdown("""
<script>
function highlightThreatPhrases(text, threats) {
    if (!threats || threats.length === 0) return text;
    
    let highlightedText = text;
    threats.forEach(phrase => {
        const regex = new RegExp(`\\b${phrase.replace(/[.*+?^${}()|[\\]\\\\]/g, '\\\\$&')}\\b`, 'gi');
        highlightedText = highlightedText.replace(regex, `<span class="threat-phrase">${phrase}</span>`);
    });
    
    return highlightedText;
}
</script>
""", unsafe_allow_html=True)

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
st.markdown("""
<div class="upload-section">
    <h3>📸 Upload Image for Threat Analysis</h3>
    <p>
        Drag and drop or click to upload an image containing text you'd like to analyze for potential scams and threats
    </p>
</div>
""", unsafe_allow_html=True)

uploaded_file = st.file_uploader("", type=["jpg", "png", "jpeg"], label_visibility="collapsed")

if uploaded_file:
    # Display uploaded image in a clean container
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="image-container">', unsafe_allow_html=True)
        st.image(uploaded_file, caption="📤 Uploaded Image", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Read file once
    file_bytes = uploaded_file.read()

    # Save uploaded image temporarily
    temp_input = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    temp_input.write(file_bytes)
    temp_input.flush()
    input_path = temp_input.name

    # Processing indicator
    st.markdown("""
    <div class="processing-container">
        <div class="processing-text">
            🔄 Processing your image for threat analysis... This may take a few seconds
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Progress bar
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
        st.markdown('<div class="json-container">', unsafe_allow_html=True)
        st.json(scam_json)
        st.markdown('</div>', unsafe_allow_html=True)

    # Highlight scam phrases on the image
    status_text.text("🎯 Highlighting threat indicators on image...")
    progress_bar.progress(60)
    
    highlighted_image_path = highlight_scam_text(input_path, scam_phrases)
    
    st.markdown("""
    <div class="results-container">
        <div class="step-indicator">
            <div class="step-number">2</div>
            <div class="step-title">🎯 Visual Threat Indicators</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="image-container">', unsafe_allow_html=True)
        st.image(Image.open(highlighted_image_path), caption="🎯 Highlighted Threat Indicators", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # -----------------------------
    # Parallel Educational Processing
    # -----------------------------
    status_text.text("📚 Generating educational content...")
    progress_bar.progress(80)
    
    img_base64 = base64.b64encode(file_bytes).decode("utf-8")

    with ThreadPoolExecutor(max_workers=3) as executor:
        future_edu_json = executor.submit(generate_educational_json, img_base64)
        future_narration = executor.submit(generate_narration_from_json, scam_json)
        future_image = executor.submit(generate_starter_frame, extracted_text)

        edu_json = future_edu_json.result()
        narration = future_narration.result()
        edu_image_path = future_image.result()

    progress_bar.progress(100)
    status_text.text("✅ Analysis complete!")

    # -----------------------------
    # Educational Content Display
    # -----------------------------
    st.markdown("""
    <div class="results-container">
        <div class="step-indicator">
            <div class="step-number">3</div>
            <div class="step-title">🎓 Educational Resources</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Tabbed interface for educational content
    tab1, tab2, tab3 = st.tabs(["📖 Educational Explanation", "📊 Detailed Analysis", "🎨 Visual Learning Guide"])
    
    with tab1:
        st.markdown(f"""
        <div class="educational-content">
            <h4>🎓 Understanding the Threats</h4>
            <p>{narration}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with tab2:
        st.markdown('<div class="json-container">', unsafe_allow_html=True)
        st.json(edu_json)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tab3:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
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

    # -----------------------------
    # Cleanup temporary files
    # -----------------------------
    for file_path in [input_path, highlighted_image_path, edu_image_path]:
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