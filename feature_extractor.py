import ipaddress
import re
import socket
import warnings
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

try:
    import whois  # optional
except Exception:
    whois = None

from requests.packages.urllib3.exceptions import InsecureRequestWarning

warnings.simplefilter("ignore", InsecureRequestWarning)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}

SHORTENERS = {
    "bit.ly",
    "goo.gl",
    "t.co",
    "tinyurl.com",
    "ow.ly",
    "is.gd",
    "buff.ly",
    "rebrand.ly",
    "cutt.ly",
    "rb.gy",
}

REASON_MAP = {
    "having_IP_Address": "URL uses an IP address instead of a domain name.",
    "URL_Length": "URL is unusually long.",
    "Shortining_Service": "URL shortener detected.",
    "having_At_Symbol": "URL contains an @ symbol.",
    "double_slash_redirecting": "Suspicious // pattern detected in the URL.",
    "Prefix_Suffix": "Domain contains a hyphen.",
    "having_Sub_Domain": "Too many subdomains detected.",
    "SSLfinal_State": "SSL/HTTPS looks suspicious.",
    "Domain_registeration_length": "Domain registration length looks suspicious.",
    "Favicon": "Favicon appears external or missing.",
    "port": "Non-standard port detected.",
    "HTTPS_token": "HTTPS token found in domain name.",
    "Request_URL": "External resource loading looks suspicious.",
    "URL_of_Anchor": "Anchor links look suspicious.",
    "Links_in_tags": "Script/link tags look suspicious.",
    "SFH": "Form handler looks suspicious.",
    "Submitting_to_email": "Form submits to email.",
    "Abnormal_URL": "Final URL differs from requested URL.",
    "Redirect": "Too many redirects detected.",
    "on_mouseover": "Mouse-over script detected.",
    "RightClick": "Right-click blocking detected.",
    "popUpWidnow": "Popup behavior detected.",
    "Iframe": "Iframe detected.",
    "age_of_domain": "Domain age could not be confirmed.",
    "DNSRecord": "DNS record issue detected.",
    "web_traffic": "Traffic could not be confirmed.",
    "Page_Rank": "Page rank could not be confirmed.",
    "Google_Index": "Google indexing could not be confirmed.",
    "Links_pointing_to_page": "Link volume looks suspicious.",
    "Statistical_report": "Statistical report could not be confirmed.",
}


def normalize_input_url(url: str) -> str:
    url = (url or "").strip()
    if not url:
        return ""
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    return url


def _same_host(host_a: str, host_b: str) -> bool:
    host_a = (host_a or "").lower().strip(".")
    host_b = (host_b or "").lower().strip(".")
    return host_a == host_b or host_a.endswith(f".{host_b}") or host_b.endswith(f".{host_a}")


def _is_ip_address(hostname: str) -> bool:
    try:
        ipaddress.ip_address(hostname)
        return True
    except Exception:
        return False


def _get_host(url: str) -> str:
    return urlparse(url).hostname or ""


def _ratio_value(external_count: int, total_count: int, good_threshold: float = 0.30, bad_threshold: float = 0.67) -> int:
    if total_count <= 0:
        return 0
    ratio = external_count / total_count
    if ratio <= good_threshold:
        return 1
    if ratio <= bad_threshold:
        return 0
    return -1


def _fetch_page(url: str):
    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=10,
            allow_redirects=True,
            verify=False,
        )
        return response
    except Exception:
        return None


def _whois_age_value(hostname: str) -> int:
    if not whois:
        return 0

    try:
        data = whois.whois(hostname)
        created = data.creation_date

        if isinstance(created, list):
            created = created[0] if created else None

        if not created:
            return 0

        if isinstance(created, str):
            created = datetime.fromisoformat(created.replace("Z", ""))

        if not isinstance(created, datetime):
            return 0

        days_old = (datetime.utcnow() - created).days
        if days_old >= 180:
            return 1
        if days_old >= 30:
            return 0
        return -1
    except Exception:
        return 0


def extract_features_from_url(url: str, feature_order: list[str]):
    normalized_url = normalize_input_url(url)
    parsed = urlparse(normalized_url)
    hostname = parsed.hostname or ""
    features = {feature: 0 for feature in feature_order}
    reasons = []
    scan_meta = {
        "normalized_url": normalized_url,
        "final_url": normalized_url,
        "status_code": None,
        "page_loaded": False,
    }

    response = _fetch_page(normalized_url)
    soup = None

    if response is not None:
        scan_meta["final_url"] = response.url
        scan_meta["status_code"] = response.status_code
        scan_meta["page_loaded"] = True
        if response.text:
            soup = BeautifulSoup(response.text, "html.parser")

    final_host = _get_host(scan_meta["final_url"]) or hostname

    # URL-based features
    if "having_IP_Address" in features:
        features["having_IP_Address"] = -1 if _is_ip_address(hostname) else 1

    if "URL_Length" in features:
        length = len(normalized_url)
        features["URL_Length"] = 1 if length < 54 else 0 if length <= 75 else -1

    if "Shortining_Service" in features:
        features["Shortining_Service"] = -1 if any(short in hostname.lower() for short in SHORTENERS) else 1

    if "having_At_Symbol" in features:
        features["having_At_Symbol"] = -1 if "@" in normalized_url else 1

    if "double_slash_redirecting" in features:
        tail = normalized_url.split("://", 1)[-1]
        features["double_slash_redirecting"] = -1 if "//" in tail else 1

    if "Prefix_Suffix" in features:
        features["Prefix_Suffix"] = -1 if "-" in hostname else 1

    if "having_Sub_Domain" in features:
        dots = hostname.count(".")
        features["having_Sub_Domain"] = 1 if dots <= 1 else 0 if dots == 2 else -1

    if "HTTPS_token" in features:
        features["HTTPS_token"] = -1 if "https" in hostname.lower() else 1

    if "port" in features:
        features["port"] = 1 if parsed.port in (None, 80, 443) else -1

    # Page-based features
    if soup is not None:
        base_url = scan_meta["final_url"]

        # Favicon
        if "Favicon" in features:
            icon = soup.find("link", rel=lambda v: v and "icon" in " ".join(v).lower()) if soup else None
            if icon and icon.get("href"):
                icon_url = urljoin(base_url, icon.get("href"))
                icon_host = _get_host(icon_url)
                features["Favicon"] = 1 if _same_host(icon_host, final_host) else -1
                if features["Favicon"] == -1:
                    reasons.append(REASON_MAP["Favicon"])
            else:
                features["Favicon"] = 0

        # Request_URL
        if "Request_URL" in features:
            external = 0
            total = 0
            for tag in soup.find_all(["img", "audio", "embed", "iframe", "source", "script", "link"]):
                src = tag.get("src") or tag.get("href")
                if not src:
                    continue
                total += 1
                abs_url = urljoin(base_url, src)
                if not _same_host(_get_host(abs_url), final_host):
                    external += 1
            features["Request_URL"] = _ratio_value(external, total)
            if features["Request_URL"] == -1:
                reasons.append(REASON_MAP["Request_URL"])

        # URL_of_Anchor
        if "URL_of_Anchor" in features:
            external = 0
            total = 0
            for a in soup.find_all("a", href=True):
                href = a.get("href", "").strip()
                if not href or href.startswith(("javascript:", "#", "mailto:")):
                    continue
                total += 1
                abs_url = urljoin(base_url, href)
                if not _same_host(_get_host(abs_url), final_host):
                    external += 1
            features["URL_of_Anchor"] = _ratio_value(external, total)
            if features["URL_of_Anchor"] == -1:
                reasons.append(REASON_MAP["URL_of_Anchor"])

        # Links_in_tags
        if "Links_in_tags" in features:
            external = 0
            total = 0
            for tag in soup.find_all(["script", "link", "meta"]):
                src = tag.get("src") or tag.get("href")
                if not src:
                    continue
                total += 1
                abs_url = urljoin(base_url, src)
                if not _same_host(_get_host(abs_url), final_host):
                    external += 1
            features["Links_in_tags"] = _ratio_value(external, total)
            if features["Links_in_tags"] == -1:
                reasons.append(REASON_MAP["Links_in_tags"])

        # SFH
        if "SFH" in features:
            forms = soup.find_all("form")
            if not forms:
                features["SFH"] = 0
            else:
                bad_forms = 0
                for form in forms:
                    action = (form.get("action") or "").strip()
                    if action in ("", "#", "about:blank"):
                        bad_forms += 1
                        continue
                    abs_action = urljoin(base_url, action)
                    if not _same_host(_get_host(abs_action), final_host):
                        bad_forms += 1
                if bad_forms == 0:
                    features["SFH"] = 1
                elif bad_forms == len(forms):
                    features["SFH"] = -1
                    reasons.append(REASON_MAP["SFH"])
                else:
                    features["SFH"] = 0

        # Submitting_to_email
        if "Submitting_to_email" in features:
            email_submit = False
            for form in soup.find_all("form"):
                action = (form.get("action") or "").lower()
                if "mailto:" in action:
                    email_submit = True
                    break
            features["Submitting_to_email"] = -1 if email_submit else 1 if soup.find_all("form") else 0
            if features["Submitting_to_email"] == -1:
                reasons.append(REASON_MAP["Submitting_to_email"])

        # Abnormal_URL
        if "Abnormal_URL" in features:
            features["Abnormal_URL"] = -1 if final_host and not _same_host(final_host, hostname) else 1
            if features["Abnormal_URL"] == -1:
                reasons.append(REASON_MAP["Abnormal_URL"])

        # Redirect
        if "Redirect" in features:
            redirect_count = len(response.history) if response else 0
            features["Redirect"] = 1 if redirect_count <= 1 else 0 if redirect_count == 2 else -1
            if features["Redirect"] == -1:
                reasons.append(REASON_MAP["Redirect"])

        # on_mouseover
        if "on_mouseover" in features:
            features["on_mouseover"] = -1 if soup.find(attrs={"onmouseover": True}) else 1
            if features["on_mouseover"] == -1:
                reasons.append(REASON_MAP["on_mouseover"])

        # RightClick
        if "RightClick" in features:
            html_text = soup.get_text(" ", strip=True).lower() if soup else ""
            raw_html = str(soup).lower() if soup else ""
            suspicious = ("oncontextmenu" in raw_html) or ("contextmenu" in raw_html) or ("return false" in raw_html)
            features["RightClick"] = -1 if suspicious else 1
            if features["RightClick"] == -1:
                reasons.append(REASON_MAP["RightClick"])

        # popUpWidnow
        if "popUpWidnow" in features:
            raw_html = str(soup).lower() if soup else ""
            suspicious = ("window.open(" in raw_html) or ("popup" in raw_html) or ("alert(" in raw_html)
            features["popUpWidnow"] = -1 if suspicious else 1
            if features["popUpWidnow"] == -1:
                reasons.append(REASON_MAP["popUpWidnow"])

        # Iframe
        if "Iframe" in features:
            features["Iframe"] = -1 if soup.find("iframe") else 1
            if features["Iframe"] == -1:
                reasons.append(REASON_MAP["Iframe"])

        # Links_pointing_to_page
        if "Links_pointing_to_page" in features:
            internal_links = 0
            total_links = 0
            for a in soup.find_all("a", href=True):
                href = a.get("href", "").strip()
                if not href or href.startswith(("javascript:", "#", "mailto:")):
                    continue
                total_links += 1
                abs_url = urljoin(base_url, href)
                if _same_host(_get_host(abs_url), final_host):
                    internal_links += 1
            features["Links_pointing_to_page"] = 1 if internal_links > 20 else 0 if internal_links >= 5 else -1
            if features["Links_pointing_to_page"] == -1:
                reasons.append(REASON_MAP["Links_pointing_to_page"])

    # Fallback-only features
    if "age_of_domain" in features:
        features["age_of_domain"] = _whois_age_value(hostname)
        if features["age_of_domain"] == -1:
            reasons.append(REASON_MAP["age_of_domain"])

    if "DNSRecord" in features:
        try:
            socket.gethostbyname(hostname)
            features["DNSRecord"] = 1
        except Exception:
            features["DNSRecord"] = -1
            reasons.append(REASON_MAP["DNSRecord"])

    if "web_traffic" in features:
        features["web_traffic"] = 0

    if "Page_Rank" in features:
        features["Page_Rank"] = 0

    if "Google_Index" in features:
        features["Google_Index"] = 0

    if "Statistical_report" in features:
        negative_count = sum(1 for value in features.values() if value == -1)
        features["Statistical_report"] = -1 if negative_count >= 5 else 0

    # Final cleanup for any missing feature keys
    for feature in feature_order:
        features.setdefault(feature, 0)

    return features, reasons, scan_meta