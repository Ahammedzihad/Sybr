"""
F7. Suspicious URL and Domain Analysis Engine.
Offline analysis using regex, urllib.parse, tldextract, and rapidfuzz.
"""
import re
import json
import os
from typing import List, Tuple
from urllib.parse import urlparse
import tldextract
from rapidfuzz.distance import Levenshtein
from app.schemas import UrlFinding

# Offline tldextract to prevent runtime HTTP calls during hackathon/demo
extractor = tldextract.TLDExtract(suffix_list_urls=None)

# URL extraction regex that captures URLs with or without scheme
URL_REGEX = re.compile(
    r'(?:https?://|www\.)[^\s<>"\'{}|\\^`\[\]]+|(?:[a-zA-Z0-9-]+\.)+(?:com|org|net|io|in|co|xyz|top|site|info|biz|zip|click|work|link|app)[^\s<>"\'{}|\\^`\[\]]*',
    re.IGNORECASE,
)

# Common URL shorteners
SHORTENERS = {
    "bit.ly", "tinyurl.com", "t.co", "goo.gl", "cutt.ly", "rb.gy",
    "is.gd", "ow.ly", "buff.ly", "bl.ink", "tiny.cc", "shorte.st"
}

# Suspicious / high-abuse TLDs
SUSPICIOUS_TLDS = {
    "zip", "top", "xyz", "click", "work", "link", "surf", "gq",
    "cf", "tk", "ml", "ga", "rest", "buzz", "cam", "loan", "stream"
}

# Security-sensitive path keywords
SENSITIVE_PATH_KEYWORDS = {
    "login", "signin", "verify", "verification", "secure", "update",
    "account", "banking", "authenticate", "confirm", "credential", "otp"
}

# Load protected brands
BRANDS_FILE = os.path.join(os.path.dirname(__file__), "brands.json")
try:
    with open(BRANDS_FILE, "r") as f:
        PROTECTED_BRANDS = json.load(f)
except Exception:
    PROTECTED_BRANDS = {}


def extract_urls(text: str) -> List[str]:
    """Extract all URLs from a block of text."""
    if not text:
        return []
    matches = URL_REGEX.findall(text)
    # Strip trailing punctuation often caught in sentences
    cleaned = []
    for match in matches:
        m = match.rstrip(".,;:!?)]}")
        if m and m not in cleaned:
            cleaned.append(m)
    return cleaned


def normalize_homoglyphs(text: str) -> str:
    """Normalize common visually deceptive homoglyphs/character swaps."""
    replacements = {
        "1": "l",
        "0": "o",
        "5": "s",
        "8": "b",
        "vv": "w",
        "rn": "m",
        "@": "a",
    }
    normalized = text.lower()
    for k, v in replacements.items():
        normalized = normalized.replace(k, v)
    return normalized


def check_lookalike(domain_label: str, full_domain: str, host: str = "") -> Tuple[str, bool]:
    """
    Check if a domain label or any host tokens mimic a known protected brand.
    Returns (brand_name, is_lookalike).
    """
    # If the domain is officially owned by the brand, it is legitimate
    for brand, info in PROTECTED_BRANDS.items():
        official_domains = info.get("official_domains", [])
        if any(
            host == off
            or host.endswith("." + off)
            or full_domain == off
            or full_domain.endswith("." + off)
            for off in official_domains
        ):
            return "", False

    # Extract all tokens to inspect (domain_label, parts of hyphenated labels, subdomains)
    labels_to_check = set()
    if domain_label:
        labels_to_check.add(domain_label)
        labels_to_check.update(domain_label.split("-"))
    if host:
        host_no_port = host.split(":")[0]
        for part in host_no_port.split("."):
            labels_to_check.add(part)
            labels_to_check.update(part.split("-"))

    for brand, info in PROTECTED_BRANDS.items():
        brand_lower = brand.lower()
        keywords = [kw.lower() for kw in info.get("keywords", [brand_lower])]

        for label in labels_to_check:
            if not label or len(label) < 3:
                continue
            normalized = normalize_homoglyphs(label)
            # Exact match to brand after homoglyph normalization (e.g. paypa1 -> paypal)
            if normalized == brand_lower:
                return brand, True
            # Levenshtein distance <= 2 (e.g. paypl, paypall, netflx)
            dist = Levenshtein.distance(normalized, brand_lower)
            if 0 < dist <= 2 and len(label) >= 4:
                return brand, True
            # Brand token combined with words (e.g. paypa1-security, login-paypal)
            for kw in keywords:
                if kw in normalized and normalized != kw:
                    return brand, True

    return "", False


def analyze_url(raw_url: str) -> UrlFinding:
    """
    F7: Analyzes a single URL against deterministic cybersecurity rules.
    Assigns rule points and outputs explainable reasons.
    """
    url_to_parse = raw_url
    if not url_to_parse.startswith(("http://", "https://")):
        url_to_parse = "http://" + url_to_parse

    parsed = urlparse(url_to_parse)
    netloc = parsed.netloc or parsed.path.split("/")[0]

    # Split domain parts using tldextract
    ext = extractor(netloc)
    subdomain = ext.subdomain
    domain_label = ext.domain
    suffix = ext.suffix

    # If tldextract couldn't identify a standard suffix (e.g. RFC .example, .local, .internal)
    if not suffix and "." in netloc:
        host_no_port = netloc.split(":")[0]
        host_parts = host_no_port.split(".")
        if len(host_parts) >= 2:
            suffix = host_parts[-1]
            domain_label = host_parts[-2]
            subdomain = ".".join(host_parts[:-2])

    full_domain = f"{domain_label}.{suffix}" if suffix else domain_label

    reasons: List[str] = []
    score = 0
    lookalike_brand = ""

    # 1. IP literal check (+30)
    is_ip = bool(re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(?::\d+)?$", netloc))
    if is_ip:
        score += 30
        reasons.append("URL uses an IP literal address instead of a domain name (+30)")

    # 2. Lookalike / typosquatting check (+35)
    brand, is_lookalike = check_lookalike(domain_label, full_domain, host=netloc)
    if is_lookalike:
        score += 35
        lookalike_brand = brand
        reasons.append(f"Lookalike/typosquat domain mimicking protected brand '{brand}' (+35)")

    # 3. Brand name inside a different subdomain (+30)
    if subdomain and not is_lookalike:
        for brand_name, info in PROTECTED_BRANDS.items():
            if brand_name in subdomain.lower():
                official_domains = info.get("official_domains", [])
                if not any(full_domain == off or full_domain.endswith("." + off) for off in official_domains):
                    score += 30
                    reasons.append(f"Brand name '{brand_name}' embedded inside untrusted subdomain '{subdomain}' (+30)")
                    lookalike_brand = brand_name
                    break

    # 4. Punycode / non-ascii check (+25)
    if "xn--" in netloc.lower() or any(ord(c) > 127 for c in netloc):
        score += 25
        reasons.append("Punycode / non-ASCII homoglyph characters detected in host (+25)")

    # 5. @ character in URL (+20)
    if "@" in raw_url:
        score += 20
        reasons.append("Deceptive '@' character found in URL (+20)")

    # 6. URL shortener (+15)
    is_shortener = netloc.lower() in SHORTENERS or full_domain.lower() in SHORTENERS
    if is_shortener:
        score += 15
        reasons.append(f"URL shortener '{netloc}' hides true destination (+15)")

    # 7. Suspicious TLD (+15)
    if suffix.lower() in SUSPICIOUS_TLDS:
        score += 15
        reasons.append(f"Suspicious high-risk top-level domain '.{suffix}' (+15)")

    # 8. Missing HTTPS (+10)
    is_https = raw_url.lower().startswith("https://")
    if not is_https and not is_ip:
        score += 10
        reasons.append("Unencrypted connection (HTTP instead of HTTPS) (+10)")

    # 9. Excessive length > 75 (+10)
    if len(raw_url) > 75:
        score += 10
        reasons.append(f"Excessive URL length ({len(raw_url)} characters) (+10)")

    # 10. Deep subdomains (>= 4 levels) (+10)
    if subdomain:
        subdomain_levels = len(subdomain.split("."))
        if subdomain_levels >= 4:
            score += 10
            reasons.append(f"Excessive subdomain depth ({subdomain_levels} levels) (+10)")

    # 11. Many hyphens (>=2) or digits in domain (+10)
    hyphen_count = domain_label.count("-")
    digit_count = sum(c.isdigit() for c in domain_label)
    if hyphen_count >= 2 or digit_count >= 3:
        score += 10
        reasons.append("Multiple hyphens or excessive digits in domain name (+10)")

    # 12. Sensitive keywords in path on untrusted domain (+10)
    path_lower = parsed.path.lower()
    for kw in SENSITIVE_PATH_KEYWORDS:
        if kw in path_lower:
            # check if official brand
            is_official = False
            for info in PROTECTED_BRANDS.values():
                if any(full_domain == off or full_domain.endswith("." + off) for off in info.get("official_domains", [])):
                    is_official = True
                    break
            if not is_official:
                score += 10
                reasons.append(f"Sensitive keyword '{kw}' in URL path on non-brand domain (+10)")
                break

    # Determine risk band
    if score >= 50:
        risk = "High"
    elif score >= 25:
        risk = "Medium"
    else:
        risk = "Low"

    return UrlFinding(
        url=raw_url,
        domain=full_domain,
        subdomain=subdomain,
        https=is_https,
        ip_literal=is_ip,
        shortener=is_shortener,
        length=len(raw_url),
        lookalike_of=lookalike_brand,
        risk=risk,
        reasons=reasons,
    )
