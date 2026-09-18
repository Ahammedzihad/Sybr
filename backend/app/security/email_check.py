"""
F8. Suspicious Email Address and Sender Analysis Engine.
Checks display names, lookalike domains, free-mail services, and domain mismatches.
"""
import re
import os
import json
from email.utils import parseaddr
from typing import List, Tuple, Optional
import tldextract
from rapidfuzz.distance import Levenshtein
from app.config import settings
from app.schemas import EmailFinding
from app.security.url_check import check_lookalike, normalize_homoglyphs

extractor = tldextract.TLDExtract(suffix_list_urls=None)

EMAIL_REGEX = re.compile(
    r'(?:[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)',
    re.IGNORECASE,
)

FREE_MAIL_DOMAINS = {
    "gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "aol.com",
    "proton.me", "protonmail.com", "zoho.com", "mail.com", "gmx.com",
    "yandex.com", "icloud.com"
}

# Load protected brands
BRANDS_FILE = os.path.join(os.path.dirname(__file__), "brands.json")
try:
    with open(BRANDS_FILE, "r") as f:
        PROTECTED_BRANDS = json.load(f)
except Exception:
    PROTECTED_BRANDS = {}


def extract_emails_from_text(text: str) -> List[Tuple[str, str]]:
    """
    Extracts email addresses and potential (display_name, email_address) pairs from text.
    """
    if not text:
        return []
    
    results: List[Tuple[str, str]] = []
    # Pattern for "Display Name <email@example.com>"
    rfc_pattern = re.findall(r'([^<\n\r]+)<([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)>', text)
    seen_addresses = set()

    for display_name, address in rfc_pattern:
        addr_clean = address.strip()
        name_clean = display_name.strip(" \"'")
        results.append((name_clean, addr_clean))
        seen_addresses.add(addr_clean.lower())

    # Raw emails not in RFC format
    raw_matches = EMAIL_REGEX.findall(text)
    for raw in raw_matches:
        raw_clean = raw.strip()
        if raw_clean.lower() not in seen_addresses:
            results.append(("", raw_clean))
            seen_addresses.add(raw_clean.lower())

    return results


def analyze_email(
    address: str,
    display_name: str = "",
    reply_to: Optional[str] = None,
) -> EmailFinding:
    """
    F8: Deterministically analyzes a sender email address and display name pair.
    """
    cleaned_display, cleaned_addr = parseaddr(address)
    if not cleaned_addr:
        cleaned_addr = address
    if not display_name and cleaned_display:
        display_name = cleaned_display

    parts = cleaned_addr.split("@")
    domain = parts[1].lower() if len(parts) > 1 else ""

    ext = extractor(domain)
    domain_label = ext.domain
    suffix = ext.suffix

    # If tldextract couldn't identify a standard suffix (e.g. .example, .local)
    if not suffix and "." in domain:
        parts_dot = domain.split(".")
        if len(parts_dot) >= 2:
            suffix = parts_dot[-1]
            domain_label = parts_dot[-2]

    full_domain = f"{domain_label}.{suffix}" if suffix else domain_label

    reasons: List[str] = []
    score = 0
    lookalike_brand = ""
    domain_mismatch = False

    # 1. Free-mail domain check
    is_freemail = domain.lower() in FREE_MAIL_DOMAINS

    # 2. Check if display name claims to be a brand/organization
    claimed_brand = ""
    display_lower = display_name.lower() if display_name else ""
    for brand, info in PROTECTED_BRANDS.items():
        if brand in display_lower or any(kw in display_lower for kw in info.get("keywords", [])):
            claimed_brand = brand
            break

    # If display name claims brand, does domain match official domains?
    if claimed_brand:
        official_domains = PROTECTED_BRANDS[claimed_brand].get("official_domains", [])
        is_official = any(full_domain == off or full_domain.endswith("." + off) for off in official_domains)
        if not is_official:
            score += 25
            domain_mismatch = True
            reasons.append(
                f"Display name claims identity of '{claimed_brand}' but sender domain '{domain}' is unauthorized (+25)"
            )

    # 3. Lookalike domain check (+35)
    brand_match, is_lookalike = check_lookalike(domain_label, full_domain, host=domain)
    if is_lookalike:
        score += 35
        lookalike_brand = brand_match
        reasons.append(f"Sender domain '{domain}' is a lookalike/typosquat of '{brand_match}' (+35)")

    # 4. Free-mail while claiming to be support or an organization (+20)
    org_words = ["support", "service", "admin", "billing", "security", "team", "desk", "official", "helpdesk"]
    claims_org = any(w in display_lower for w in org_words) or any(w in parts[0].lower() for w in org_words)
    if is_freemail and (claimed_brand or claims_org):
        score += 20
        reasons.append(f"Official organization persona sent from public free webmail '{domain}' (+20)")

    # 5. Expected organization domain check (+20)
    # If the email purports to be from our organization but isn't in ORG_DOMAINS
    if settings.ORG_DOMAINS and claims_org and not is_lookalike:
        if not any(domain == od or domain.endswith("." + od) for od in settings.ORG_DOMAINS):
            # If not an official external brand either
            if not any(any(domain == off or domain.endswith("." + off) for off in info.get("official_domains", [])) for info in PROTECTED_BRANDS.values()):
                score += 20
                domain_mismatch = True
                reasons.append(f"Domain '{domain}' does not match expected organization domain policy (+20)")

    # 6. Reply-To mismatch (+25)
    if reply_to:
        _, reply_addr = parseaddr(reply_to)
        reply_domain = reply_addr.split("@")[-1].lower() if "@" in reply_addr else ""
        if reply_domain and reply_domain != domain:
            score += 25
            reasons.append(f"Reply-To domain '{reply_domain}' does not match From domain '{domain}' (+25)")

    # 7. Homoglyphs in email domain (+20)
    if "xn--" in domain or any(ord(c) > 127 for c in domain):
        score += 20
        reasons.append("Punycode/non-ASCII characters detected in email domain (+20)")

    # Determine risk band
    if score >= 50:
        risk = "High"
    elif score >= 25:
        risk = "Medium"
    else:
        risk = "Low"

    return EmailFinding(
        address=cleaned_addr,
        display_name=display_name,
        domain=domain,
        free_mail=is_freemail,
        lookalike_of=lookalike_brand,
        domain_mismatch=domain_mismatch,
        risk=risk,
        reasons=reasons,
    )
