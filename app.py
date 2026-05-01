import os
import requests
from pathlib import Path
from urllib.parse import urlparse

import joblib
import pandas as pd
from flask import Flask, render_template, request

from NetworkSecurity.utils.ml_utils.model.estimator import NetworkModel
from feature_extractor import extract_features_from_url

app = Flask(__name__)

FEATURES = [
    "having_IP_Address",
    "URL_Length",
    "Shortining_Service",
    "having_At_Symbol",
    "double_slash_redirecting",
    "Prefix_Suffix",
    "having_Sub_Domain",
    "SSLfinal_State",
    "Domain_registeration_length",
    "Favicon",
    "port",
    "HTTPS_token",
    "Request_URL",
    "URL_of_Anchor",
    "Links_in_tags",
    "SFH",
    "Submitting_to_email",
    "Abnormal_URL",
    "Redirect",
    "on_mouseover",
    "RightClick",
    "popUpWidnow",
    "Iframe",
    "age_of_domain",
    "DNSRecord",
    "web_traffic",
    "Page_Rank",
    "Google_Index",
    "Links_pointing_to_page",
    "Statistical_report",
]

FEATURE_LABELS = {
    "having_IP_Address": "Uses IP Address in URL",
    "URL_Length": "URL Length",
    "Shortining_Service": "Uses URL Shortener",
    "having_At_Symbol": "Contains @ Symbol",
    "double_slash_redirecting": "Double Slash Redirecting",
    "Prefix_Suffix": "Uses Hyphen in Domain",
    "having_Sub_Domain": "Subdomain Count",
    "SSLfinal_State": "SSL Final State",
    "Domain_registeration_length": "Domain Registration Length",
    "Favicon": "Favicon Source",
    "port": "Uses Non-standard Port",
    "HTTPS_token": "HTTPS Token in Domain",
    "Request_URL": "Request URL",
    "URL_of_Anchor": "URL of Anchor Tags",
    "Links_in_tags": "Links in Tags",
    "SFH": "Server Form Handler",
    "Submitting_to_email": "Submits to Email",
    "Abnormal_URL": "Abnormal URL",
    "Redirect": "Redirect Count",
    "on_mouseover": "On Mouse Over",
    "RightClick": "Right Click Disabled",
    "popUpWidnow": "Popup Window",
    "Iframe": "Iframe",
    "age_of_domain": "Age of Domain",
    "DNSRecord": "DNS Record",
    "web_traffic": "Web Traffic",
    "Page_Rank": "Page Rank",
    "Google_Index": "Google Index",
    "Links_pointing_to_page": "Links Pointing to Page",
    "Statistical_report": "Statistical Report",
}

FEATURE_GROUPS = {
    "URL-Based Features": [
        "having_IP_Address",
        "URL_Length",
        "Shortining_Service",
        "having_At_Symbol",
        "double_slash_redirecting",
        "Prefix_Suffix",
        "HTTPS_token",
        "port",
    ],
    "Host & Domain Features": [
        "having_Sub_Domain",
        "SSLfinal_State",
        "Domain_registeration_length",
        "age_of_domain",
        "DNSRecord",
        "Google_Index",
    ],
    "Content Features": [
        "Favicon",
        "Request_URL",
        "URL_of_Anchor",
        "Links_in_tags",
        "SFH",
        "Submitting_to_email",
        "Abnormal_URL",
        "Iframe",
    ],
    "Behavior / Traffic Features": [
        "Redirect",
        "on_mouseover",
        "RightClick",
        "popUpWidnow",
        "web_traffic",
        "Page_Rank",
        "Links_pointing_to_page",
        "Statistical_report",
    ],
}

MODEL_PATH = Path("final_model/model.pkl")
PREP_PATH = Path("final_model/preprocessor.pkl")

# Trusted domain lists (from your prompt)
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


def _download_file(url: str, dst: Path) -> bool:
    try:
        dst.parent.mkdir(parents=True, exist_ok=True)
        with requests.get(url, stream=True, timeout=30) as r:
            r.raise_for_status()
            with open(dst, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        print(f"Downloaded {url} -> {dst}")
        return True
    except Exception as e:
        print("Download failed:", e)
        return False

def _get_hostname(url: str) -> str:
    try:
        parsed = urlparse(url)
        host = parsed.hostname or url
        return host.lower()
    except Exception:
        return url.lower()

def _is_trusted_hostname(hostname: str) -> bool:
    if not hostname:
        return False
    for d in TRUSTED_DOMAINS + INDIA_DOMAINS:
        d = d.lower()
        if hostname == d or hostname.endswith("." + d):
            return True
    return False

def _enforce_trusted_override(pred_label: str, confidence: float, url: str):
    """
    If URL hostname matches a trusted domain, force the label to Legitimate
    and ensure confidence is at least 95.0 (or higher if already higher).
    """
    host = _get_hostname(url)
    if _is_trusted_hostname(host):
        forced_conf = max(confidence or 0.0, 95.0)
        print(f"[trusted-override] {host} matched trusted list - forcing Legitimate @ {forced_conf}%")
        return "Legitimate", round(forced_conf, 2)
    return pred_label, round(confidence or 0.0, 2)

def ensure_models_from_env():
    model_url = os.getenv("MODEL_URL")
    prep_url = os.getenv("PREPROCESSOR_URL")

    if model_url and not MODEL_PATH.exists():
        _download_file(model_url, MODEL_PATH)

    if prep_url and not PREP_PATH.exists():
        _download_file(prep_url, PREP_PATH)

# call early, before loading model
ensure_models_from_env()

model = joblib.load(MODEL_PATH)
preprocessor = joblib.load(PREP_PATH)
network_model = NetworkModel(model=model, preprocessor=preprocessor)


def prediction_label(pred):
    print("Raw prediction:", pred)
    print("Model classes:", getattr(model, "classes_", None))

    pred_int = int(float(pred))

    # 0 = Phishing / Unsafe, 1 = Legitimate / Safe
    if pred_int == 1:
        return "Legitimate"
    if pred_int == 0:
        return "Phishing"
    return str(pred_int)


def get_prediction_confidence(df, raw_pred):
    try:
        transformed_data = preprocessor.transform(df)

        if hasattr(model, "predict_proba"):
            proba = model.predict_proba(transformed_data)[0]
            class_values = [float(x) for x in model.classes_]
            class_index = class_values.index(float(raw_pred))
            return round(float(proba[class_index]) * 100, 2)

    except Exception as e:
        print("Confidence error:", e)

    return 100.0


def get_risk_level(confidence, prediction):
    """
    Map confidence percentage to risk level based on prediction type.
    """
    if prediction == "Legitimate":
        if confidence >= 90:
            return "Likely Safe"
        elif confidence >= 70:
            return "Probably Safe / Use Caution"
        elif confidence >= 40:
            return "Uncertain / Needs Review"
        else:
            return "Suspicious"
    else:  # Phishing
        if confidence >= 90:
            return "High Risk Phishing"
        elif confidence >= 70:
            return "Likely Phishing"
        elif confidence >= 40:
            return "Uncertain / Needs Review"
        else:
            return "Suspicious"


def get_risk_category(risk_level):
    """
    Return CSS class for risk level styling.
    """
    risk_map = {
        "Likely Safe": "safe",
        "Probably Safe / Use Caution": "caution",
        "Uncertain / Needs Review": "uncertain",
        "Suspicious": "suspicious",
        "Likely Phishing": "phishing",
        "High Risk Phishing": "high-risk",
    }
    return risk_map.get(risk_level, "uncertain")


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/detect")
def detect():
    return render_template(
        "detect.html",
        features=FEATURES,
        feature_labels=FEATURE_LABELS,
        feature_groups=FEATURE_GROUPS,
    )


@app.route("/predict", methods=["POST"])
def predict():
    try:
        data = {}
        for feature in FEATURES:
            value = request.form.get(feature)
            if value is None or value == "":
                return f"Missing value for: {feature}", 400
            data[feature] = int(float(value))

        df = pd.DataFrame([data], columns=FEATURES)

        y_pred = network_model.predict(df)
        raw_pred = y_pred[0]
        label = prediction_label(raw_pred)
        confidence = get_prediction_confidence(df, raw_pred)
        risk_level = get_risk_level(confidence, label)
        risk_category = get_risk_category(risk_level)

        return render_template(
            "result.html",
            risk_level=risk_level,
            risk_category=risk_category,
            prediction=label,
            raw_prediction=raw_pred,
            confidence=confidence,
            scanned_url=None,
            risk_reasons=[],
            data=data,
            error_message=None,
        )

    except Exception as e:
        return f"Prediction error: {str(e)}", 500


@app.route("/scan", methods=["POST"])
def scan():
    scanned_url = request.form.get("website_url", "").strip()

    if not scanned_url:
        return render_template(
            "result.html",
            prediction=None,
            risk_level=None,
            risk_category=None,
            raw_prediction=None,
            confidence=None,
            scanned_url=None,
            risk_reasons=[],
            data=None,
            error_message="Enter a valid URL.",
        )

    try:
        normalized_url = scanned_url
        if not normalized_url.startswith(("http://", "https://")):
            normalized_url = f"https://{normalized_url}"

        extracted_data, risk_reasons, scan_meta = extract_features_from_url(
            normalized_url, FEATURES
        )

        df = pd.DataFrame([extracted_data], columns=FEATURES)

        y_pred = network_model.predict(df)
        raw_pred = y_pred[0]
        label = prediction_label(raw_pred)
        confidence = get_prediction_confidence(df, raw_pred)

        # enforce trusted-domain override using the normalized URL
        label, confidence = _enforce_trusted_override(label, confidence, normalized_url)

        # recompute risk level/category after override
        risk_level = get_risk_level(confidence, label)
        risk_category = get_risk_category(risk_level)

        return render_template(
            "result.html",
            risk_level=risk_level,
            risk_category=risk_category,
            prediction=label,
            raw_prediction=raw_pred,
            confidence=confidence,
            scanned_url=normalized_url,
            risk_reasons=risk_reasons,
            data=extracted_data,
            error_message=None,
            scan_meta=scan_meta,
        )

    except Exception as e:
        return render_template(
            "result.html",
            prediction=None,
            risk_level=None,
            risk_category=None,
            raw_prediction=None,
            confidence=None,
            scanned_url=scanned_url,
            risk_reasons=[],
            data=None,
            error_message=str(e),
        )


@app.route("/threat-scanner")
def threat_scanner():
    return render_template("threat_scanner.html")


@app.route("/threat-analysis", methods=["POST"])
def threat_analysis():
    scanned_url = request.form.get("website_url", "").strip()

    if not scanned_url:
        return render_template(
            "threat_analysis.html",
            error_message="Enter a valid URL.",
            scanned_url=None,
            final_url=None,
            status_code=None,
            prediction=None,
            risk_level=None,
            risk_category=None,
            confidence=None,
            risk_reasons=[],
            data=None,
            scan_meta={},
        )

    try:
        normalized_url = scanned_url
        if not normalized_url.startswith(("http://", "https://")):
            normalized_url = f"https://{normalized_url}"

        extracted_data, risk_reasons, scan_meta = extract_features_from_url(
            normalized_url, FEATURES
        )

        df = pd.DataFrame([extracted_data], columns=FEATURES)

        y_pred = network_model.predict(df)
        raw_pred = y_pred[0]
        label = prediction_label(raw_pred)
        confidence = get_prediction_confidence(df, raw_pred)

        # enforce trusted-domain override using normalized URL
        label, confidence = _enforce_trusted_override(label, confidence, normalized_url)

        # recompute risk level/category after override
        risk_level = get_risk_level(confidence, label)
        risk_category = get_risk_category(risk_level)

        return render_template(
            "threat_analysis.html",
            scanned_url=normalized_url,
            final_url=scan_meta.get("final_url", normalized_url),
            status_code=scan_meta.get("status_code"),
            prediction=label,
            risk_level=risk_level,
            risk_category=risk_category,
            raw_prediction=raw_pred,
            confidence=confidence,
            risk_reasons=risk_reasons,
            data=extracted_data,
            scan_meta=scan_meta,
            error_message=None,
        )

    except Exception as e:
        return render_template(
            "threat_analysis.html",
            error_message=f"Analysis failed: {str(e)}",
            scanned_url=scanned_url,
            final_url=None,
            status_code=None,
            prediction=None,
            risk_level=None,
            risk_category=None,
            confidence=None,
            risk_reasons=[],
            data=None,
            scan_meta={},
        )


if __name__ == "__main__":
    print("Starting Flask app on http://127.0.0.1:5000...")
    app.run(debug=True)