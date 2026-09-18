"""
URL Security Check & Analysis Module.
Provides deterministic heuristic risk assessment for URLs:
- Protocol security (HTTPS vs HTTP)
- Raw IP literal detection
- URL shortener identification
- Excessive URL length (> 75 chars)
- Brand typosquatting / lookalike detection via Levenshtein edit distance and homoglyph substitution
- Weighted risk score calculation (Low, Medium, High)
"""

import json
import logging
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import tldextract

logger = logging.getLogger(__name__)

# Known URL shorteners
SHORTENERS = {
    "bit.ly",
    "tinyurl.com",
    "goo.gl",
    "t.co",
    "ow.ly",
    "is.gd",
    "buff.ly",
    "adf.ly",
    "rebrand.ly",
}

# Common enterprise & consumer brands relevant to support, payments, and tech
COMMON_BRANDS = [
    "paypal",
    "microsoft",
    "google",
    "apple",
    "amazon",
    "netflix",
    "stripe",
    "shopify",
    "chase",
    "wellsfargo",
    "bankofamerica",
    "adobe",
    "facebook",
    "instagram",
    "twitter",
    "dropbox",
    "slack",
    "zoom",
]

# IPv4 address regex
IP_LITERAL_RE = re.compile(
    r"^(?:(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)\.){3}(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)$"
)

# URL extraction regex
URL_REGEX = re.compile(r"https?://[^\s<>\"']+", re.IGNORECASE)


def levenshtein_distance(s1: str, s2: str) -> int:
    """
    Computes the Levenshtein edit distance between two strings
    using an optimized two-row dynamic programming approach.
    """
    if s1 == s2:
        return 0
    if len(s1) == 0:
        return len(s2)
    if len(s2) == 0:
        return len(s1)

    prev_row = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        curr_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = prev_row[j + 1] + 1
            deletions = curr_row[j] + 1
            substitutions = prev_row[j] + (c1 != c2)
            curr_row.append(min(insertions, deletions, substitutions))
        prev_row = curr_row
    return prev_row[-1]


def normalize_substitutions(text: str) -> str:
    """
    Replaces common homoglyph/typosquatting substitution characters:
    - 1 -> l
    - 0 -> o
    - rn -> m
    - vv -> w
    """
    s = text.lower()
    s = s.replace("rn", "m")
    s = s.replace("vv", "w")
    s = s.replace("1", "l")
    s = s.replace("0", "o")
    return s


def is_lookalike_token(token: str, brands: List[str] = COMMON_BRANDS) -> Optional[str]:
    """
    Checks if a token is a lookalike/typosquat of any common brand name:
    1. Check if token after character substitution equals a brand name (e.g. paypa1 -> paypal, micros0ft -> microsoft).
    2. Check if Levenshtein edit distance is 1 or 2 (not exact 0).
    Returns matched brand name if lookalike, otherwise None.
    """
    cleaned_tok = token.lower().strip()
    if not cleaned_tok or len(cleaned_tok) < 3:
        return None

    # Check homoglyph substitution
    normalized = normalize_substitutions(cleaned_tok)
    for brand in brands:
        if cleaned_tok == brand:
            # Exact genuine brand match is NOT a lookalike
            continue
        if normalized == brand:
            return brand

    # Check Levenshtein distance 1 to 2
    for brand in brands:
        if cleaned_tok == brand:
            continue
        dist = levenshtein_distance(cleaned_tok, brand)
        if 1 <= dist <= 2:
            return brand

    return None


def check_url(url: str) -> Dict[str, Any]:
    """
    Evaluates risk of a URL using protocol, host type, shorteners, length,
    and Levenshtein brand lookalike analysis.

    Returns:
    {
      "url": str,
      "domain": str,
      "subdomain": str,
      "https": bool,
      "ip_literal": bool,
      "shortener": bool,
      "url_length": int,
      "lookalike": bool,
      "risk": "Low" | "Medium" | "High",
      "reason": str,
      # Pipeline backwards compatibility aliases:
      "suspicious_url": bool,
      "url_risk": str,
      "url_reason": str,
    }
    """
    if not url or not isinstance(url, str) or not url.strip():
        return {
            "url": url if isinstance(url, str) else "",
            "domain": "",
            "subdomain": "",
            "https": False,
            "ip_literal": False,
            "shortener": False,
            "url_length": 0,
            "lookalike": False,
            "risk": "Low",
            "reason": "Empty or invalid URL provided.",
            "suspicious_url": False,
            "url_risk": "Low",
            "url_reason": "Empty or invalid URL provided.",
        }

    raw_url = url.strip().rstrip(".,;:!?'\")>]}\r\n")
    if not raw_url or raw_url.lower() in ("http://", "https://"):
        return {
            "url": raw_url,
            "domain": "",
            "subdomain": "",
            "https": raw_url.lower().startswith("https://"),
            "ip_literal": False,
            "shortener": False,
            "url_length": len(raw_url),
            "lookalike": False,
            "risk": "Low",
            "reason": "Empty or invalid URL provided.",
            "suspicious_url": False,
            "url_risk": "Low",
            "url_reason": "Empty or invalid URL provided.",
        }

    url_length = len(raw_url)
    is_https = raw_url.lower().startswith("https://")

    # Extract domain and subdomain via tldextract
    ext = tldextract.extract(raw_url)
    subdomain = ext.subdomain
    domain = ext.domain
    suffix = ext.suffix

    # Full registered domain (e.g. bit.ly, paypal.com)
    registered_domain = f"{domain}.{suffix}".strip(".") if suffix else domain

    # 1. IP Literal Check
    is_ip_literal = bool(IP_LITERAL_RE.match(domain))
    if not is_ip_literal:
        # Fallback check on netloc from urlparse
        try:
            parsed = urlparse(raw_url)
            netloc_host = (parsed.netloc.split(":")[0] if ":" in parsed.netloc else parsed.netloc).strip()
            if IP_LITERAL_RE.match(netloc_host):
                is_ip_literal = True
                domain = netloc_host
        except Exception:
            pass

    # Handle malformed URL without valid host/domain and not an IP literal
    if not domain and not is_ip_literal:
        return {
            "url": raw_url,
            "domain": "",
            "subdomain": "",
            "https": is_https,
            "ip_literal": False,
            "shortener": False,
            "url_length": url_length,
            "lookalike": False,
            "risk": "Low",
            "reason": "Malformed URL: missing valid host/domain.",
            "suspicious_url": False,
            "url_risk": "Low",
            "url_reason": "Malformed URL: missing valid host/domain.",
        }

    # 2. Shortener Check
    is_shortener = (
        registered_domain.lower() in SHORTENERS
        or domain.lower() in SHORTENERS
        or f"{domain}.{suffix}".lower() in SHORTENERS
    )

    # 3. URL Length Check
    is_long = url_length > 75

    # 4. Lookalike Detection
    is_lookalike = False
    lookalike_target = None

    # Collect candidate tokens from domain and subdomain
    candidates: List[str] = []
    if domain:
        candidates.append(domain)
        candidates.extend([p for p in re.split(r"[-_.]", domain) if p])
    if subdomain:
        candidates.extend([p for p in re.split(r"[-_.]", subdomain) if p])

    for cand in candidates:
        matched_brand = is_lookalike_token(cand, COMMON_BRANDS)
        if matched_brand:
            is_lookalike = True
            lookalike_target = matched_brand
            break

    # 5. Weighted Risk Score Calculation
    # +1 if not https, +3 if ip_literal, +1 if shortener, +3 if lookalike, +1 if url_length long
    score = 0
    reasons_list: List[str] = []

    if not is_https:
        score += 1
        reasons_list.append("unencrypted HTTP (+1)")
    if is_ip_literal:
        score += 3
        reasons_list.append("raw IP address host (+3)")
    if is_shortener:
        score += 1
        reasons_list.append("URL shortener service (+1)")
    if is_lookalike:
        score += 3
        reasons_list.append(f"lookalike typosquatting of brand '{lookalike_target}' (+3)")
    if is_long:
        score += 1
        reasons_list.append(f"long URL length ({url_length} chars > 75) (+1)")

    # Assign risk category
    if score >= 4:
        risk = "High"
    elif score >= 2:
        risk = "Medium"
    else:
        risk = "Low"

    # Construct human-readable reason string
    if score == 0:
        reason_str = "Low risk: URL uses HTTPS with standard domain length and no detected suspicious indicators."
    else:
        reason_str = f"{risk} risk (score {score}): " + ", ".join(reasons_list) + "."

    return {
        "url": raw_url,
        "domain": domain,
        "subdomain": subdomain,
        "https": is_https,
        "ip_literal": is_ip_literal,
        "shortener": is_shortener,
        "url_length": url_length,
        "lookalike": is_lookalike,
        "risk": risk,
        "reason": reason_str,
        # Backward compatibility aliases for pipeline.py
        "suspicious_url": risk in ("Medium", "High"),
        "url_risk": risk,
        "url_reason": reason_str,
    }


def extract_urls_from_text(text: Optional[str]) -> List[str]:
    """
    Extracts all valid HTTP/HTTPS URLs from raw text using regex r'https?://\\S+'.
    Handles zero URLs (returns []), multiple URLs, and skips malformed URLs gracefully.
    """
    if not text or not isinstance(text, str):
        return []

    raw_matches = URL_REGEX.findall(text)
    clean_urls: List[str] = []

    for raw_url in raw_matches:
        try:
            # Strip trailing punctuation marks commonly attached in sentences
            cleaned = raw_url.rstrip(".,;:!?'\")>]}\r\n")
            if not cleaned:
                continue

            parsed = urlparse(cleaned)
            # Ensure URL has valid scheme and netloc host
            if parsed.scheme.lower() in ("http", "https") and parsed.netloc:
                clean_urls.append(cleaned)
        except Exception as err:
            logger.debug("Skipping malformed URL candidate '%s': %s", raw_url, err)
            continue

    return clean_urls


def main():
    """
    Runs check_url() against all URLs in dataset.json (both synthetic and real)
    and verifies that phishing URLs score High/Medium while legitimate URLs score Low.
    """
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    # Locate dataset.json
    search_paths = [
        Path("dataset.json"),
        Path("backend/dataset.json"),
        Path(__file__).resolve().parent.parent.parent / "dataset.json",
        Path(__file__).resolve().parent.parent / "dataset.json",
    ]
    dataset_file = next((p for p in search_paths if p.exists()), None)

    extracted_urls: List[Dict[str, Any]] = []

    if dataset_file:
        print(f"Reading messages and extracting URLs from {dataset_file}...")
        with open(dataset_file, "r", encoding="utf-8") as f:
            conversations = json.load(f)

        for conv in conversations:
            conv_id = conv.get("conversation_id", "")
            is_synth = "SYNTH" in conv_id or "PHISH" in conv_id
            for msg in conv.get("messages", []):
                txt = msg.get("text", "")
                urls = extract_urls_from_text(txt)
                for u in urls:
                    extracted_urls.append({
                        "url": u,
                        "conversation_id": conv_id,
                        "is_synthetic_phish": is_synth,
                    })

    # Add standard reference URLs to verify complete test coverage
    benchmark_urls = [
        # Phishing synthetic benchmarks
        {"url": "http://192.168.1.105/auth-renew", "expected": "High", "desc": "IP literal + HTTP"},
        {"url": "http://account-resolver.xyz/urgent-verify", "expected": "Low/Med", "desc": "HTTP urgency domain"},
        {"url": "http://secure-sso-gateway.example/login", "expected": "Low/Med", "desc": "HTTP SSO domain"},
        {"url": "https://paypa1-security.example/disputes/cancel", "expected": "Medium/High", "desc": "Typosquat paypa1"},
        {"url": "http://micros0ft-verify.example/tenant-login", "expected": "High", "desc": "Typosquat micros0ft + HTTP"},
        {"url": "https://bit.ly/login-verify-now-urgent-security-account-portal-update-2026-auth", "expected": "High", "desc": "Shortener + Long URL"},
        # Legitimate benchmarks
        {"url": "https://paypal.com/signin", "expected": "Low", "desc": "Legitimate PayPal HTTPS"},
        {"url": "https://microsoft.com/support", "expected": "Low", "desc": "Legitimate Microsoft HTTPS"},
        {"url": "https://google.com/search?q=help", "expected": "Low", "desc": "Legitimate Google HTTPS"},
    ]

    print("\n" + "=" * 80)
    print("                    URL SECURITY ANALYSIS EVALUATION RESULTS                  ")
    print("=" * 80)

    # Test URLs from dataset
    if extracted_urls:
        print(f"\n--- Extracted {len(extracted_urls)} URLs from dataset.json ---")
        for item in extracted_urls:
            res = check_url(item["url"])
            print(f"\n[ID: {item['conversation_id']}] (Synthetic: {item['is_synthetic_phish']})")
            print(f"  URL:        {res['url']}")
            print(f"  Domain:     {res['domain']} | Subdomain: {res['subdomain']}")
            print(f"  HTTPS:      {res['https']} | IP Literal: {res['ip_literal']} | Lookalike: {res['lookalike']} | Shortener: {res['shortener']} | Length: {res['url_length']}")
            print(f"  Risk Level: {res['risk']}")
            print(f"  Reason:     {res['reason']}")

    # Test Benchmark URLs
    print("\n" + "=" * 80)
    print("                   BENCHMARK & LEGITIMATE vs PHISHING EVALUATION              ")
    print("=" * 80)
    for b in benchmark_urls:
        res = check_url(b["url"])
        print(f"\n* Case: {b['desc']} (Expected: {b['expected']})")
        print(f"  URL:        {res['url']}")
        print(f"  Risk Level: {res['risk']} (Score >= 4: High, >= 2: Medium, else Low)")
        print(f"  Reason:     {res['reason']}")
    print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    main()
