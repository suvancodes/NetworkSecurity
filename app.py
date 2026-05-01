import os
import requests
import traceback
import logging
from pathlib import Path
from urllib.parse import urlparse
from flask import Flask, render_template, request, redirect, url_for, jsonify
import joblib
import pandas as pd

# --- Local Imports ---
from NetworkSecurity.utils.ml_utils.model.estimator import NetworkModel
from feature_extractor import extract_features_from_url, FEATURES

# --- Configuration & Setup ---
logging.basicConfig(level=logging.INFO)

# Get the absolute path to the directory containing this script (app.py)
BASE_DIR = Path(__file__).resolve().parent

# Define absolute paths for the model and preprocessor
MODEL_PATH = BASE_DIR / "final_model" / "model.pkl"
PREPROCESSOR_PATH = BASE_DIR / "final_model" / "preprocessor.pkl"

# Trusted domain lists
TRUSTED_DOMAINS = [
    "google.com","youtube.com","gmail.com","facebook.com","instagram.com","whatsapp.com",
    "x.com","twitter.com","linkedin.com","microsoft.com","live.com","outlook.com",
    "github.com","openai.com","apple.com","icloud.com","amazon.com","aws.amazon.com",
    "netflix.com","paypal.com","wikipedia.org","reddit.com","quora.com","stackoverflow.com",
    "adobe.com","canva.com","zoom.us","dropbox.com","notion.so","oracle.com","ibm.com",
    "intel.com","nvidia.com","samsung.com","mi.com","flipkart.com","myntra.com","snapdeal.com",
    "ajio.com","zomato.com","swiggy.com","ola.com","uber.com","airbnb.com","booking.com"
]
INDIA_DOMAINS = [
    "irctc.co.in","sbi.co.in","onlinesbi.sbi","hdfcbank.com","icicibank.com","axisbank.com",
    "kotak.com","upi.gov.in","uidai.gov.in","digilocker.gov.in","incometax.gov.in",
    "gst.gov.in","licindia.in","paytm.com","phonepe.com","bharatpe.com"
]

# --- Model Loading ---
network_model = None
try:
    preprocessor = joblib.load(PREPROCESSOR_PATH)
    model = joblib.load(MODEL_PATH)
    network_model = NetworkModel(preprocessor=preprocessor, model=model)
    logging.info("Model and preprocessor loaded successfully.")
except Exception as e:
    logging.error(f"FATAL: Could not load model or preprocessor from {MODEL_PATH} or {PREPROCESSOR_PATH}")
    logging.error(traceback.format_exc())

# --- Initialize Flask App ---
app = Flask(__name__)

# --- Helper Functions ---
def _get_hostname(url: str) -> str:
    try:
        return urlparse(url).hostname or url.lower()
    except Exception:
        return url.lower()

def _is_trusted_hostname(hostname: str) -> bool:
    if not hostname:
        return False
    all_trusted = TRUSTED_DOMAINS + INDIA_DOMAINS
    for d in all_trusted:
        if hostname == d.lower() or hostname.endswith("." + d.lower()):
            return True
    return False

def _enforce_trusted_override(pred_label: str, confidence: float, url: str):
    host = _get_hostname(url)
    if _is_trusted_hostname(host):
        forced_conf = max(confidence or 0.0, 95.0)
        logging.info(f"[trusted-override] {host} matched trusted list - forcing Legitimate @ {forced_conf}%")
        return "Legitimate", round(forced_conf, 2)
    return pred_label, round(confidence or 0.0, 2)

def prediction_label(pred):
    pred_int = int(float(pred))
    return "Legitimate" if pred_int == 1 else "Phishing"

def get_prediction_confidence(df, raw_pred):
    try:
        if hasattr(network_model.model, "predict_proba"):
            proba = network_model.model.predict_proba(network_model.preprocessor.transform(df))[0]
            class_index = list(network_model.model.classes_).index(raw_pred)
            return round(float(proba[class_index]) * 100, 2)
    except Exception as e:
        logging.error(f"Confidence calculation error: {e}")
    return 100.0

def get_risk_level(confidence, prediction):
    if prediction == "Legitimate":
        if confidence >= 90: return "Likely Safe"
        if confidence >= 70: return "Probably Safe / Use Caution"
        if confidence >= 40: return "Uncertain / Needs Review"
        return "Suspicious"
    else:  # Phishing
        if confidence >= 90: return "High Risk Phishing"
        if confidence >= 70: return "Likely Phishing"
        if confidence >= 40: return "Uncertain / Needs Review"
        return "Suspicious"

def get_risk_category(risk_level):
    risk_map = {
        "Likely Safe": "safe", "Probably Safe / Use Caution": "caution",
        "Uncertain / Needs Review": "uncertain", "Suspicious": "suspicious",
        "Likely Phishing": "phishing", "High Risk Phishing": "high-risk",
    }
    return risk_map.get(risk_level, "uncertain")

# --- Routes ---
@app.route("/")
def home():
    return render_template("home.html")

@app.route("/detect")
def detect():
    return render_template("detect.html", features=FEATURES)

@app.route("/threat-scanner")
def threat_scanner():
    return render_template("threat_scanner.html")

@app.route("/threat-analysis", methods=["GET", "POST"])
def threat_analysis():
    context = {
        "scanned_url": None, "final_url": None, "status_code": None,
        "prediction": None, "risk_level": None, "risk_category": None,
        "raw_prediction": None, "confidence": None, "risk_reasons": [],
        "data": {}, "scan_meta": {}, "error_message": None, "internal_error": None
    }
    if request.method == "GET":
        return render_template("threat_analysis.html", **context)

    try:
        scanned_url = request.form.get("website_url", "").strip()
        context["scanned_url"] = scanned_url
        if not scanned_url:
            context["error_message"] = "Enter a valid URL."
        elif not network_model:
            context["error_message"] = "Model is not loaded. Cannot perform analysis."
        else:
            normalized_url = scanned_url if scanned_url.startswith(("http://", "https://")) else f"https://{scanned_url}"
            
            extracted_data, risk_reasons, scan_meta = extract_features_from_url(normalized_url, FEATURES)
            df = pd.DataFrame([extracted_data], columns=FEATURES)
            y_pred = network_model.predict(df)
            
            raw_pred = y_pred[0] if y_pred.size > 0 else 0.0
            label = prediction_label(raw_pred)
            confidence = get_prediction_confidence(df, raw_pred)
            label, confidence = _enforce_trusted_override(label, confidence, normalized_url)
            
            context.update({
                "prediction": label,
                "confidence": confidence,
                "risk_level": get_risk_level(confidence, label),
                "risk_category": get_risk_category(get_risk_level(confidence, label)),
                "final_url": scan_meta.get("final_url", normalized_url),
                "status_code": scan_meta.get("status_code"),
                "raw_prediction": raw_pred,
                "risk_reasons": risk_reasons,
                "data": extracted_data,
                "scan_meta": scan_meta,
            })

    except Exception as e:
        logging.exception("threat-analysis failure")
        context["error_message"] = f"Analysis failed: {str(e)}"
        context["internal_error"] = traceback.format_exc()

    return render_template("threat_analysis.html", **context)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)