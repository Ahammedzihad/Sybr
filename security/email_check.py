"""
Email Security Check & Analysis Module.
Provides deterministic heuristic risk assessment for email addresses:
- Domain extraction
- Free-mail provider detection (gmail.com, yahoo.com, outlook.com, hotmail.com)
- Brand typosquatting / lookalike detection via Levenshtein edit distance and homoglyphs
- Domain mismatch detection (display name claiming official roles vs. actual sender domain)
- Weighted risk score calculation (Low, Medium, High) with false-positive protection for customers
- Regex email extraction from raw conversation text
"""

import json
import logging
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Expected organization domain for this support platform
EXPECTED_ORG_DOMAIN = "sybr-support.com"

# Known consumer free-mail providers (weak risk signal on their own)
FREE_MAIL_DOMAINS = {
    "gmail.com",
    "yahoo.com",
    "outlook.com",
    "hotmail.com",
    "aol.com",
    "icloud.com",
    "protonmail.com",
}

# Common enterprise & payment brands frequently targeted by spoofing
KNOWN_BRANDS = [
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
    "sybr",
]

# Keywords in display name indicating an official authority/internal role
OFFICIAL_ROLE_KEYWORDS = {
    "support",
    "security",
    "billing",
    "admin",
    "administrator",
    "helpdesk",
    "help desk",
    "service desk",
    "resolution center",
    "verification",
    "account team",
    "customer care",
    "it desk",
}

# Email extraction regex
EMAIL_REGEX = re.compile(r"[\w\.-]+@[\w\.-]+\.\w+", re.IGNORECASE)


def levenshtein_distance(s1: str, s2: str) -> int:
    """
    Computes Levenshtein edit distance between two strings using 2-row DP.
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
    """Replaces common typosquatting substitutions (1->l, 0->o, rn->m, vv->w)."""
    s = text.lower()
    s = s.replace("rn", "m")
    s = s.replace("vv", "w")
    s = s.replace("1", "l")
    s = s.replace("0", "o")
    return s


def is_lookalike_domain(domain: str, brands: List[str] = KNOWN_BRANDS) -> Optional[str]:
    """
    Checks if a domain (or its sub-tokens) is a lookalike/typosquat of any known brand.
    Returns the targeted brand name if detected, else None.
    """
    cleaned = domain.lower().strip()
    if not cleaned:
        return None

    # Split domain into tokens by '.' and '-'
    tokens = re.split(r"[-_.]", cleaned)
    for tok in tokens:
        if not tok or len(tok) < 3:
            continue
        # 1. Homoglyph check
        normalized = normalize_substitutions(tok)
        for brand in brands:
            if tok == brand:
                # Exact genuine match is NOT a lookalike
                continue
            if normalized == brand:
                return brand

        # 2. Levenshtein edit distance check (distance 1 to 2)
        for brand in brands:
            if tok == brand:
                continue
            dist = levenshtein_distance(tok, brand)
            if 1 <= dist <= 2:
                return brand

    return None


def parse_sender_header(sender_str: str) -> tuple[str, Optional[str]]:
    """
    Extracts email and optional display name from a formatted header string like
    'PayPal Resolution Center <support@paypa1-security.example>' or 'user@example.com'.
    """
    s = sender_str.strip()
    match = re.search(r"^(.*?)\s*<([^>]+)>", s)
    if match:
        display = match.group(1).strip()
        email_addr = match.group(2).strip()
        return email_addr, display if display else None
    return s, None


def check_email(
    email: str,
    display_name: Optional[str] = None,
    expected_org_domain: str = EXPECTED_ORG_DOMAIN
) -> Dict[str, Any]:
    """
    Evaluates risk of an email address using domain extraction, free-mail checks,
    brand lookalike detection, and display name mismatch analysis.

    Returns:
    {
      "email": str,
      "domain": str,
      "free_mail": bool,
      "lookalike": bool,
      "domain_mismatch": bool,
      "risk": "Low" | "Medium" | "High",
      "reason": str,
      # Pipeline backwards compatibility aliases:
      "suspicious_email": bool,
      "email_risk": str,
      "email_reason": str,
    }
    """
    if not email or not isinstance(email, str) or not email.strip():
        return {
            "email": "",
            "domain": "",
            "free_mail": False,
            "lookalike": False,
            "domain_mismatch": False,
            "risk": "Low",
            "reason": "Empty or invalid email provided.",
            "suspicious_email": False,
            "email_risk": "Low",
            "email_reason": "Empty or invalid email provided.",
        }

    raw_email = email.strip()

    # If the input contains a display name in angle brackets, parse it
    if "<" in raw_email and ">" in raw_email:
        parsed_email, parsed_display = parse_sender_header(raw_email)
        raw_email = parsed_email
        if display_name is None:
            display_name = parsed_display

    # Strip surrounding and trailing punctuation marks
    raw_email = raw_email.strip(".,;:!?'\")>]}(<{\r\n ")

    # Extract user and domain components
    user_part = ""
    domain = ""
    is_malformed_syntax = False

    if "@" in raw_email:
        parts = raw_email.split("@")
        if len(parts) == 2:
            user_part = parts[0].strip()
            domain = parts[1].strip(".,;:!?'\")>]}(<{\r\n ").lower()
        else:
            # Multiple @ characters (e.g. user@@domain.com) -> malformed
            user_part = parts[0].strip()
            domain = parts[-1].strip(".,;:!?'\")>]}(<{\r\n ").lower()
            is_malformed_syntax = True
    else:
        user_part = raw_email
        domain = ""
        is_malformed_syntax = True

    if not user_part:
        is_malformed_syntax = True

    # 1. Free-mail check
    is_free_mail = bool(domain) and (domain in FREE_MAIL_DOMAINS or any(domain.endswith("." + fm) for fm in FREE_MAIL_DOMAINS))

    # 2. Lookalike check
    lookalike_target = is_lookalike_domain(domain)
    is_lookalike = bool(lookalike_target)

    # 3. Domain mismatch check
    # Flags if display name suggests an official organization or known brand,
    # but domain does not match expected org domain or brand's authentic domain.
    is_domain_mismatch = False
    mismatch_reason_detail = None

    if display_name and isinstance(display_name, str):
        disp_lower = display_name.lower()
        
        # Check if display name claims an official role or known brand
        claims_official_role = any(kw in disp_lower for kw in OFFICIAL_ROLE_KEYWORDS)
        claimed_brand = next((b for b in KNOWN_BRANDS if b in disp_lower), None)

        if claims_official_role or claimed_brand:
            # Check if domain matches authentic brand or expected org domain
            is_valid_official_domain = (
                domain == expected_org_domain.lower()
                or (claimed_brand and domain == f"{claimed_brand}.com")
            )
            if not is_valid_official_domain:
                is_domain_mismatch = True
                claimed_id = claimed_brand or "official support"
                mismatch_reason_detail = (
                    f"display name suggests official role ('{display_name}') "
                    f"but sender domain is '{domain}'"
                )

    # 4. Weighted Risk Score Calculation
    # Free-mail alone is a WEAK signal (+1), which guarantees Low risk for normal customers.
    # Lookalike is a STRONG malicious signal (+3).
    # Domain mismatch (impersonation) is a STRONG signal (+3).
    # Malformed domain without '.' (+2).
    score = 0
    reasons_list: List[str] = []

    if is_lookalike:
        score += 3
        reasons_list.append(f"lookalike typosquatting of brand '{lookalike_target}' (+3)")

    if is_domain_mismatch:
        score += 3
        reasons_list.append(f"{mismatch_reason_detail} (+3)")

    if is_free_mail:
        score += 1
        if is_domain_mismatch or is_lookalike:
            reasons_list.append("free-mail provider used for official impersonation (+1)")
        else:
            reasons_list.append("standard consumer free-mail domain (+1)")

    is_malformed_email = (
        not domain
        or "." not in domain
        or is_malformed_syntax
        or domain.startswith(".")
        or domain.endswith(".")
        or len(domain.split(".")[-1]) < 2
    )
    if is_malformed_email:
        score += 2
        reasons_list.append("malformed sender domain (+2)")

    # Assign risk category
    if score >= 4:
        risk = "High"
    elif score >= 2:
        risk = "Medium"
    else:
        risk = "Low"

    # Human-readable explanation
    if score == 0:
        reason_str = f"Low risk: Verified legitimate domain '{domain}' without suspicious indicators."
    elif score == 1 and is_free_mail and not is_lookalike and not is_domain_mismatch:
        reason_str = (
            f"Low risk: Legitimate customer contact on standard consumer free-mail domain ('{domain}'). "
            "No impersonation or typosquatting detected."
        )
    else:
        reason_str = f"{risk} risk (score {score}): " + "; ".join(reasons_list) + "."

    return {
        "email": raw_email,
        "domain": domain,
        "free_mail": is_free_mail,
        "lookalike": is_lookalike,
        "domain_mismatch": is_domain_mismatch,
        "risk": risk,
        "reason": reason_str,
        # Backward compatibility aliases for pipeline.py
        "suspicious_email": risk in ("Medium", "High"),
        "email_risk": risk,
        "email_reason": reason_str,
    }


def extract_emails_from_text(text: Optional[str]) -> List[str]:
    r"""
    Extracts all valid email addresses from raw text using regex r'[\w\.-]+@[\w\.-]+\.\w+'.
    Handles zero matches, multiple matches, and malformed strings gracefully.
    """
    if not text or not isinstance(text, str):
        return []

    raw_matches = EMAIL_REGEX.findall(text)
    clean_emails: List[str] = []

    for raw in raw_matches:
        cleaned = raw.strip().strip(".,;:!?'\")>]}(<{\r\n")
        # Basic sanity: contains '@', has text before and after, contains '.' in domain part
        if "@" in cleaned and cleaned.count("@") == 1:
            u_part, d_part = cleaned.split("@", 1)
            d_clean = d_part.strip(".,;:!?'\")>]}(<{\r\n")
            if u_part and d_clean and "." in d_clean:
                tld = d_clean.split(".")[-1]
                if len(tld) >= 2 and tld.isalpha():
                    clean_emails.append(f"{u_part}@{d_clean}")

    return clean_emails


def main():
    """
    Runs check_email() against synthetic phishing emails from Task 1,
    plus real customer emails from dataset.json, confirming no false positives
    on legitimate customer contact info.
    """
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    print("\n" + "=" * 80)
    print("                   EMAIL SECURITY ANALYSIS EVALUATION RESULTS                 ")
    print("=" * 80)

    # 1. Test against synthetic phishing emails from Task 1
    phishing_test_cases = [
        {
            "email": "support@paypa1-security.example",
            "display": "PayPal Resolution Center",
            "desc": "Synthetic Phish: Typosquatted PayPal + Display Name",
        },
        {
            "email": "admin-alerts@micros0ft-verify.example",
            "display": "Microsoft 365 Admin Center",
            "desc": "Synthetic Phish: Typosquatted Microsoft + Official Display Name",
        },
        {
            "email": "security-update@gmail.com",
            "display": "Bank Security Department",
            "desc": "Phishing Attempt: Official security role claiming via consumer Gmail",
        },
        {
            "email": "billing-support@yahoo.com",
            "display": "Billing Support Desk",
            "desc": "Phishing Attempt: Billing desk claiming via consumer Yahoo",
        },
    ]

    print("\n--- Phishing & Impersonation Senders (Expected: High/Medium) ---")
    for tc in phishing_test_cases:
        res = check_email(tc["email"], display_name=tc["display"])
        print(f"\n* Case: {tc['desc']}")
        print(f"  Sender:     {tc['display']} <{res['email']}>")
        print(f"  Domain:     {res['domain']} | Free-mail: {res['free_mail']} | Lookalike: {res['lookalike']} | Mismatch: {res['domain_mismatch']}")
        print(f"  Risk Level: {res['risk']}")
        print(f"  Reason:     {res['reason']}")

    # 2. Test against legitimate customer and organization emails (Zero False Positives)
    legitimate_test_cases = [
        {
            "email": "john.doe@gmail.com",
            "display": "John Doe",
            "desc": "Real Customer: Ordinary inquiry from Gmail (MUST BE LOW RISK)",
        },
        {
            "email": "sarah.smith@yahoo.com",
            "display": "Sarah Smith",
            "desc": "Real Customer: Ordinary support ticket from Yahoo (MUST BE LOW RISK)",
        },
        {
            "email": "billing-alerts@store.com",
            "display": "Store Invoices",
            "desc": "Real Corporate Sender: Legitimate merchant invoice",
        },
        {
            "email": "help@sybr-support.com",
            "display": "Sybr Support Desk",
            "desc": "Internal Official Support: Matches EXPECTED_ORG_DOMAIN",
        },
    ]

    print("\n" + "=" * 80)
    print("--- Legitimate Customer & Org Senders (Expected: Low - Zero False Positives) ---")
    for tc in legitimate_test_cases:
        res = check_email(tc["email"], display_name=tc["display"])
        print(f"\n* Case: {tc['desc']}")
        print(f"  Sender:     {tc['display']} <{res['email']}>")
        print(f"  Domain:     {res['domain']} | Free-mail: {res['free_mail']} | Lookalike: {res['lookalike']} | Mismatch: {res['domain_mismatch']}")
        print(f"  Risk Level: {res['risk']}")
        print(f"  Reason:     {res['reason']}")

    # 3. Test extract_emails_from_text
    print("\n" + "=" * 80)
    print("--- Email Extraction from Raw Text Evaluation ---")
    samples = [
        "Please send updates to support@sybr-support.com or backup@store.com.",
        "From: billing-alerts@store.com; contact me at user.test@gmail.com!",
        "Plain message without any email addresses inside.",
    ]
    for text in samples:
        found = extract_emails_from_text(text)
        print(f"\n  Input:  {text}")
        print(f"  Found:  {found}")
    print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    main()
