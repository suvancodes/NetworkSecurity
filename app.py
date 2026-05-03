import streamlit as st
import pandas as pd
import joblib
import logging
from pathlib import Path
from urllib.parse import urlparse
import textwrap  # <-- add this

# --- Local Imports (Ensure these files are in the root directory) ---
try:
    from feature_extractor import extract_features_from_url, FEATURES
    from NetworkSecurity.utils.ml_utils.model.estimator import NetworkModel
except ImportError as e:
    st.error(f"Fatal Error: Could not import local Python modules. Please ensure 'feature_extractor.py' and 'estimator.py' are in the same directory as 'app.py'. Details: {e}")
    st.stop()

# --- Page Configuration ---
st.set_page_config(
    page_title="SafeLink Inspector",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS for the new UI ---
st.markdown("""
<style>
    /* App background (adds depth) */
    .stApp {
        background:
            radial-gradient(1200px 600px at 15% 10%, rgba(79,139,249,0.18), transparent 55%),
            radial-gradient(900px 500px at 85% 20%, rgba(46,204,113,0.12), transparent 55%),
            radial-gradient(900px 500px at 75% 85%, rgba(243,156,18,0.10), transparent 55%),
            linear-gradient(180deg, #0B1020 0%, #070A12 100%);
    }

    /* Main container */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2.5rem;
        padding-left: 5rem;
        padding-right: 5rem;
        max-width: 1200px;
    }

    /* Sidebar padding (stable selector) */
    section[data-testid="stSidebar"] > div {
        padding: 2rem 1rem;
    }

    /* Result Card */
    .result-card {
        background: rgba(14, 17, 23, 0.72);
        border-radius: 18px;
        padding: 26px;
        margin-top: 18px;
        border: 1px solid rgba(79, 139, 249, 0.55);
        box-shadow: 0 18px 50px rgba(0,0,0,0.35);
        backdrop-filter: blur(10px);
    }

    /* Progress bar rounding */
    .stProgress > div > div > div > div {
        border-radius: 10px;
    }

    /* =========================
       Landing (front page) styles
       ========================= */
    .hero {
        position: relative;
        padding: 34px 30px;
        border-radius: 22px;
        border: 1px solid rgba(79, 139, 249, 0.55);
        background: linear-gradient(135deg,
            rgba(79,139,249,0.18) 0%,
            rgba(46,204,113,0.10) 35%,
            rgba(14,17,23,0.75) 70%,
            rgba(14,17,23,0.65) 100%
        );
        box-shadow: 0 22px 60px rgba(0,0,0,0.40);
        overflow: hidden;
        backdrop-filter: blur(10px);
    }

    .hero::before {
        content: "";
        position: absolute;
        inset: -2px;
        background: radial-gradient(600px 220px at 25% 20%, rgba(79,139,249,0.35), transparent 55%),
                    radial-gradient(520px 220px at 70% 70%, rgba(46,204,113,0.22), transparent 58%),
                    radial-gradient(420px 180px at 85% 25%, rgba(243,156,18,0.20), transparent 60%);
        filter: blur(12px);
        opacity: 0.75;
        animation: heroGlow 7s ease-in-out infinite;
        pointer-events: none;
    }

    @keyframes heroGlow {
        0%, 100% { transform: translateY(0px); opacity: 0.70; }
        50%      { transform: translateY(-8px); opacity: 0.90; }
    }

    .hero-inner {
        position: relative;
        z-index: 2;
    }

    .hero-title {
        font-size: 2.1rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        margin: 0 0 10px 0;
        color: #F3F6FF;
    }

    .hero-subtitle {
        margin: 0 0 18px 0;
        font-size: 1.05rem;
        color: rgba(230,240,255,0.82);
        line-height: 1.5;
        max-width: 900px;
    }

    .pill-row {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin-top: 14px;
        margin-bottom: 14px;
    }

    .pill {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 8px 12px;
        border-radius: 999px;
        font-size: 0.95rem;
        color: rgba(243,246,255,0.92);
        border: 1px solid rgba(255,255,255,0.10);
        background: rgba(15, 23, 42, 0.35);
        box-shadow: 0 10px 22px rgba(0,0,0,0.22);
    }

    .grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 14px;
        margin-top: 16px;
    }

    .card {
        border-radius: 18px;
        padding: 16px 16px;
        border: 1px solid rgba(255,255,255,0.10);
        background: rgba(8, 10, 18, 0.55);
        box-shadow: 0 18px 50px rgba(0,0,0,0.28);
        transition: transform 180ms ease, border-color 180ms ease, background 180ms ease;
        animation: floatIn 520ms ease both;
    }

    @keyframes floatIn {
        from { transform: translateY(10px); opacity: 0.0; }
        to   { transform: translateY(0px); opacity: 1.0; }
    }

    .card:hover {
        transform: translateY(-3px);
        border-color: rgba(79,139,249,0.45);
        background: rgba(8, 10, 18, 0.68);
    }

    .card h4 {
        margin: 0 0 8px 0;
        font-size: 1.05rem;
        color: rgba(243,246,255,0.95);
    }

    .card p {
        margin: 0;
        color: rgba(230,240,255,0.78);
        line-height: 1.45;
        font-size: 0.98rem;
    }

    .cta {
        margin-top: 14px;
        padding: 12px 14px;
        border-radius: 14px;
        border: 1px dashed rgba(79,139,249,0.45);
        background: rgba(15, 23, 42, 0.25);
        color: rgba(230,240,255,0.85);
        font-size: 0.98rem;
    }

    /* Responsive grid */
    @media (max-width: 1050px) {
        .main .block-container { padding-left: 2rem; padding-right: 2rem; }
        .grid { grid-template-columns: 1fr; }
        .hero-title { font-size: 1.8rem; }
    }

    /* Respect reduced motion */
    @media (prefers-reduced-motion: reduce) {
        .hero::before { animation: none; }
        .card { animation: none; }
        .card:hover { transform: none; }
    }

    /* =========================
       FIX: Make the ">" sidebar toggle look like a real button
       ========================= */

    div[data-testid="collapsedControl"] {
        position: fixed;
        top: 16px;
        left: 16px;
        z-index: 9999;
        width: 46px;
        height: 46px;
        border-radius: 12px;
        background: rgba(15, 23, 42, 0.85);
        border: 1px solid rgba(79, 139, 249, 0.85);
        box-shadow: 0 10px 25px rgba(0,0,0,0.35);
        display: flex;
        align-items: center;
        justify-content: center;
        backdrop-filter: blur(6px);
    }
    div[data-testid="collapsedControl"] button {
        width: 46px !important;
        height: 46px !important;
        border-radius: 12px !important;
        padding: 0 !important;
    }
    div[data-testid="collapsedControl"] button span {
        font-size: 26px !important;
        line-height: 1 !important;
        font-weight: 800 !important;
        color: #E6F0FF !important;
    }

    button[data-testid="stSidebarCollapseButton"] {
        width: 44px !important;
        height: 44px !important;
        border-radius: 12px !important;
        border: 1px solid rgba(79, 139, 249, 0.65) !important;
        background: rgba(15, 23, 42, 0.55) !important;
    }
    button[data-testid="stSidebarCollapseButton"] span {
        font-size: 22px !important;
        font-weight: 800 !important;
        color: #E6F0FF !important;
    }

    /* FIX: Streamlit Cloud header overlaps the sidebar toggle.
       Push it down and keep it above everything. */
    div[data-testid="collapsedControl"] {
        position: fixed !important;
        top: 72px !important;     /* was 16px */
        left: 16px !important;
        z-index: 100000 !important;
        width: 46px;
        height: 46px;
        border-radius: 12px;
        background: rgba(15, 23, 42, 0.85);
        border: 1px solid rgba(79, 139, 249, 0.85);
        box-shadow: 0 10px 25px rgba(0,0,0,0.35);
        display: flex !important;
        align-items: center;
        justify-content: center;
        backdrop-filter: blur(6px);
    }
    div[data-testid="collapsedControl"] button {
        width: 46px !important;
        height: 46px !important;
        border-radius: 12px !important;
        padding: 0 !important;
    }
    div[data-testid="collapsedControl"] button span {
        font-size: 26px !important;
        font-weight: 800 !important;
        color: #E6F0FF !important;
    }

    /* Optional: also keep the collapse button visible when sidebar is open */
    button[data-testid="stSidebarCollapseButton"] {
        z-index: 100000 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- Configuration & Setup ---
logging.basicConfig(level=logging.INFO)
BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "final_model" / "model.pkl"
PREPROCESSOR_PATH = BASE_DIR / "final_model" / "preprocessor.pkl"

# --- Trusted Domain Lists ---
TRUSTED_DOMAINS = [
    "google.com","youtube.com","gmail.com","facebook.com","instagram.com","whatsapp.com",
    "x.com","twitter.com","linkedin.com","microsoft.com","live.com","outlook.com",
    "github.com","openai.com","apple.com","icloud.com","amazon.com","aws.amazon.com",
    "netflix.com","paypal.com","wikipedia.org","reddit.com","quora.com","stackoverflow.com"
]
INDIA_DOMAINS = [
    "irctc.co.in","sbi.co.in","onlinesbi.sbi","hdfcbank.com","icicibank.com","axisbank.com",
    "kotak.com","upi.gov.in","uidai.gov.in","digilocker.gov.in","incometax.gov.in",
    "gst.gov.in","licindia.in","paytm.com","phonepe.com","bharatpe.com"
]

# --- Model Loading ---
@st.cache_resource
def load_model():
    try:
        preprocessor = joblib.load(PREPROCESSOR_PATH)
        model = joblib.load(MODEL_PATH)
        return NetworkModel(preprocessor=preprocessor, model=model)
    except Exception as e:
        st.sidebar.error(f"Model loading failed: {e}")
        return None

network_model = load_model()

# --- Helper Functions ---
def prediction_label(pred):
    return "Legitimate" if int(float(pred)) == 1 else "Phishing"

def get_risk_level(confidence, prediction):
    if prediction == "Legitimate":
        if confidence >= 90: return "Very Low Risk"
        if confidence >= 70: return "Low Risk"
        return "Uncertain"
    else: # Phishing
        if confidence >= 90: return "High Risk"
        if confidence >= 70: return "Medium Risk"
        return "Suspicious"

def get_prediction_confidence(df, raw_pred):
    if hasattr(network_model.model, "predict_proba"):
        proba = network_model.model.predict_proba(network_model.preprocessor.transform(df))[0]
        class_index = list(network_model.model.classes_).index(raw_pred)
        return round(float(proba[class_index]) * 100, 2)
    return 100.0

def _get_hostname(url: str) -> str:
    try: return urlparse(url).hostname or url.lower()
    except Exception: return url.lower()

def _is_trusted_hostname(hostname: str) -> bool:
    if not hostname: return False
    all_trusted = TRUSTED_DOMAINS + INDIA_DOMAINS
    for d in all_trusted:
        if hostname == d.lower() or hostname.endswith("." + d.lower()): return True
    return False

def enforce_trusted_override(pred_label: str, confidence: float, url: str):
    host = _get_hostname(url)
    if _is_trusted_hostname(host):
        forced_conf = max(confidence, 95.0)
        return "Legitimate", round(forced_conf, 2)
    return pred_label, round(confidence, 2)

# --- Dictionaries for descriptive text (global scope) ---
feature_options = {
    "having_IP_Address": {"Uses Domain Name": 1, "Uses IP Address": -1},
    "URL_Length": {"Short (<54 chars)": 1, "Average (54-75)": 0, "Long (>75)": -1},
    "Shortining_Service": {"Full-length URL": 1, "Uses a URL Shortener": -1},
    "having_At_Symbol": {"No '@' Symbol Present": 1, "Contains '@' Symbol": -1},
    "double_slash_redirecting": {"Path is Standard": 1, "Redirects using '//' in path": -1},
    "Prefix_Suffix": {"Domain is clean": 1, "Domain contains '-' prefix/suffix": -1},
    "having_Sub_Domain": {"Standard (e.g., www)": 1, "Suspicious (e.g., multiple dots)": 0, "Known Phishing Pattern": -1},
    "SSLfinal_State": {"Has a Valid, Trusted SSL Certificate": 1, "SSL has Issues (e.g., wrong host)": 0, "No SSL Certificate": -1},
    "Domain_registeration_length": {"Domain registered for over a year": 1, "Domain registered for less than a year": -1},
    "Favicon": {"Favicon loaded from same domain": 1, "Favicon loaded from different domain": -1},
    "HTTPS_token": {"'https' not in domain name": 1, "'https' appears in domain name": -1},
    "Request_URL": {"Most content from same domain": 1, "Many requests to external domains": 0, "Vast majority of requests are external": -1},
    "URL_of_Anchor": {"Anchor links point to safe domains": 1, "Some anchor links are suspicious": 0, "Most anchor links are suspicious": -1},
    "Links_in_tags": {"Links in <meta>, <script> are safe": 1, "Some suspicious links in tags": 0, "Many suspicious links in tags": -1},
    "SFH": {"Form submissions are secure and local": 1, "Form handler is suspicious": 0, "Form submits to a different domain": -1},
    "Submitting_to_email": {"Does not submit forms via 'mailto:'": 1, "Submits forms via 'mailto:'": -1},
    "Abnormal_URL": {"Domain name matches site identity": 1, "Domain name does not match site identity": -1},
    "Redirect": {"Uses few or no redirects": 1, "Uses a moderate number of redirects": 0, "Uses many redirects": -1},
    "on_mouseover": {"Status bar is not modified on hover": 1, "Status bar is modified on hover": -1},
    "RightClick": {"Right-click is enabled": 1, "Right-click is disabled": -1},
    "popUpWidnow": {"Does not use malicious pop-ups": 1, "Uses pop-ups with text fields": -1},
    "Iframe": {"Does not use iFrames": 1, "Uses iFrames (can hide content)": -1},
    "age_of_domain": {"Domain is older than 6 months": 1, "Domain is newer than 6 months": -1},
    "DNSRecord": {"DNS record exists and is valid": 1, "No DNS record found": -1},
    "web_traffic": {"High Traffic Rank (Top 100k)": 1, "Medium Traffic Rank": 0, "Low or No Traffic Rank": -1},
    "Page_Rank": {"PageRank is high (>0.2)": 1, "PageRank is low (<0.2)": -1},
    "Google_Index": {"Site is indexed by Google": 1, "Site is not indexed by Google": -1},
    "Links_pointing_to_page": {"Has a normal number of backlinks": 1, "Has very few or zero backlinks": -1},
    "Statistical_report": {"Host is not on phishing lists": 1, "Host is on known phishing lists": -1},
}
default_options = {"Safe / Normal": 1, "Suspicious": 0, "Phishing / Abnormal": -1}

# --- UI Rendering ---

# --- Sidebar for Inputs ---
with st.sidebar:
    st.title("🛡️ SafeLink Inspector")
    st.markdown("Provide the details below to analyze a website's risk level.")

    analysis_mode = st.radio(
        "Choose Analysis Mode",
        ("🔗 URL Scanner", "✍️ Manual Feature Input"),
        key="analysis_mode"
    )
    st.markdown("---")

    if analysis_mode == "🔗 URL Scanner":
        st.header("URL Scanner")
        url_to_scan = st.text_input("Enter the full URL to scan", placeholder="e.g., https://www.google.com")
        analyze_button = st.button("Analyze URL", type="primary", use_container_width=True)

    else: # Manual Feature Input
        st.header("Manual Analysis")
        with st.expander("Enter Website Features", expanded=True):
            manual_features_text = {}
            for feature in FEATURES:
                current_options = feature_options.get(feature, default_options)
                manual_features_text[feature] = st.selectbox(
                    label=feature.replace("_", " ").title(),
                    options=list(current_options.keys()),
                    key=f"manual_{feature}"
                )
        analyze_button = st.button("Predict from Features", type="primary", use_container_width=True)


# --- Main Panel for Results ---
if not analyze_button:
    landing_html = """
    <div class="hero">
      <div class="hero-inner">
        <div class="hero-title">SafeLink Inspector</div>
        <div class="hero-subtitle">
          Scan a website URL or manually describe its behavior to detect phishing signals.
          Built to be fast, readable, and transparent—so you can see <b>why</b> a link looks risky.
        </div>
        <div class="pill-row">
          <div class="pill">🔗 URL Scanner</div>
          <div class="pill">✍️ Manual Feature Input</div>
          <div class="pill">📊 Confidence + Risk Level</div>
          <div class="pill">🧾 Explainable Feature Report</div>
        </div>
        <div class="cta">
          <b>Start here:</b> Open the sidebar (top-left button), choose an analysis mode, then click <b>Analyze URL</b>.
        </div>
        <div class="grid">
          <div class="card">
            <h4>Real‑time URL inspection</h4>
            <p>Extracts phishing-related signals from the URL and page behavior (when available) and predicts legitimacy.</p>
          </div>
          <div class="card">
            <h4>Human‑friendly explanations</h4>
            <p>Every feature is shown as <b>Safe / Suspicious / Phishing</b> text—no confusing -1/0/1 in the report.</p>
          </div>
          <div class="card">
            <h4>Safer confidence display</h4>
            <p>Confidence is visualized clearly, and trusted domains can be forced to a higher confidence threshold.</p>
          </div>
        </div>
      </div>
    </div>
    """
    landing_html = "\n".join(
        line for line in textwrap.dedent(landing_html).splitlines()
        if line.strip()  # removes blank lines that break HTML blocks in Streamlit markdown
    )
    st.markdown(landing_html, unsafe_allow_html=True)

else:
    # Prepare DataFrame based on analysis mode
    if analysis_mode == "🔗 URL Scanner":
        if not url_to_scan:
            st.warning("Please enter a URL to analyze.")
            st.stop()
        with st.spinner(f"Inspecting {url_to_scan}..."):
            try:
                normalized_url = url_to_scan if url_to_scan.startswith(("http://", "https://")) else f"https://{url_to_scan}"
                extracted_data, risk_reasons, scan_meta = extract_features_from_url(normalized_url, FEATURES)
                df = pd.DataFrame([extracted_data], columns=FEATURES)
            except Exception as e:
                st.error(f"Could not extract features from URL. Error: {e}")
                st.stop()
    else: # Manual
        manual_features_numerical = {}
        for feature, text_value in manual_features_text.items():
            current_options = feature_options.get(feature, default_options)
            manual_features_numerical[feature] = current_options[text_value]
        df = pd.DataFrame([manual_features_numerical], columns=FEATURES)

    # --- Prediction Logic ---
    raw_pred = network_model.predict(df)[0]
    label = prediction_label(raw_pred)
    confidence = get_prediction_confidence(df, raw_pred)
    
    # --- FIX: Apply trusted domain override for URL scans ---
    if analysis_mode == "🔗 URL Scanner":
        label, confidence = enforce_trusted_override(label, confidence, normalized_url)

    risk_level = get_risk_level(confidence, label)

    # --- Display Results in a Card ---
    with st.container():
        st.markdown('<div class="result-card">', unsafe_allow_html=True)
        st.subheader("📊 Prediction Results")
        
        # Determine color based on risk
        if "High" in risk_level: bar_color = "red"
        elif "Medium" in risk_level: bar_color = "orange"
        elif "Low" in risk_level: bar_color = "green"
        else: bar_color = "blue"

        # Display Verdict and Risk Level
        col1, col2 = st.columns(2)
        col1.markdown(f"**Verdict:** <span style='color:{bar_color}; font-size:1.5rem; font-weight:bold;'>{label}</span>", unsafe_allow_html=True)
        col2.markdown(f"**Assessed Risk Level:** <span style='color:{bar_color}; font-size:1.5rem; font-weight:bold;'>{risk_level}</span>", unsafe_allow_html=True)
        
        # --- FIX: Use Streamlit's native progress bar for better UI ---
        st.progress(int(confidence), text=f"Confidence: {confidence}%")
        
        st.markdown("---")
        
        # Display Confidence Metrics
        m_col1, m_col2 = st.columns(2)
        m_col1.metric(label="Model Confidence", value=f"{confidence}%")
        phishing_prob = 100 - confidence if label == 'Legitimate' else confidence
        m_col2.metric(label="Phishing Probability", value=f"{phishing_prob:.1f}%")

        # --- FIX: Restore Feature Analysis for URL Scans ---
        if analysis_mode == "🔗 URL Scanner":
            with st.expander("View Full Feature Report"):
                feature_options_reversed = {
                    feature: {v: k for k, v in opts.items()}
                    for feature, opts in feature_options.items()
                }
                default_options_reversed = {v: k for k, v in default_options.items()}

                report_cols = st.columns(2)
                for i, (feature, value) in enumerate(extracted_data.items()):
                    target_col = report_cols[0] if i < len(FEATURES) / 2 else report_cols[1]
                    rev_map = feature_options_reversed.get(feature, default_options_reversed)
                    description = rev_map.get(value, "N/A")
                    icon = "✅" if value == 1 else ("⚠️" if value == 0 else "❌")
                    
                    target_col.markdown(f"**{feature.replace('_', ' ').title()}**")
                    target_col.markdown(f"> {icon} _{description}_")

        st.markdown('</div>', unsafe_allow_html=True)