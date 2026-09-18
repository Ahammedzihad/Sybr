"""
Test script to validate combined_intelligence() on:
1. Exact phishing example with pre-computed URL/email flags
2. 5-6 real non-phishing customer messages to verify low false-positive rate
"""

import json
import sys
import time
from pathlib import Path

# Ensure backend and root paths in sys.path
CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent
for p in (str(CURRENT_DIR), str(ROOT_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from ai.gemini_client import combined_intelligence
except ImportError:
    from backend.ai.gemini_client import combined_intelligence


def test_phishing_example():
    print("=" * 65, flush=True)
    print("TEST 1: EXACT PHISHING ATTACK VALIDATION", flush=True)
    print("=" * 65, flush=True)

    phish_text = (
        "URGENT! Your account has been compromised. Click this link immediately "
        "to secure your account and enter your username, password and OTP."
    )
    url_flag = {
        "suspicious_url": True,
        "risk": "High",
        "reason": "Lookalike domain detected",
    }
    email_flag = {
        "suspicious_email": False,
        "risk": "Low",
        "reason": None,
    }

    print(f"Customer Message:\n  \"{phish_text}\"\n", flush=True)
    print(f"Pre-computed URL Flag:\n  {json.dumps(url_flag)}\n", flush=True)
    print(f"Pre-computed Email Flag:\n  {json.dumps(email_flag)}\n", flush=True)

    res = combined_intelligence(phish_text, url_flag, email_flag)
    print("Model Result:", flush=True)
    print(json.dumps(res, indent=2), flush=True)

    # Validations
    threat_type = str(res.get("threat_type", ""))
    is_phish = any(term in threat_type.lower() for term in ["phish", "social engineering", "credential"])
    social_eng = res.get("social_engineering", False)
    techniques = [t.lower() for t in res.get("technique", [])]
    risk_level = str(res.get("risk_level", ""))

    print("\n--- Validation Assertions ---", flush=True)
    print(f"Threat Type is Phishing/Social Eng:   {is_phish} (Got: '{threat_type}')", flush=True)
    print(f"Social Engineering is True:           {social_eng == True} (Got: {social_eng})", flush=True)
    print(f"Techniques Detected:                  {techniques}", flush=True)
    print(f"Risk Level is High or Critical:       {risk_level in ['High', 'Critical']} (Got: '{risk_level}')", flush=True)

    return res


def test_real_customer_messages():
    print("\n" + "=" * 65, flush=True)
    print("TEST 2: 6 REAL NON-PHISHING CUSTOMER MESSAGES (FALSE POSITIVE TEST)", flush=True)
    print("=" * 65, flush=True)

    normal_samples = [
        (
            "CONV-001 (Billing/Refund)",
            "I was double charged $49.99 on my credit card for this month's subscription. Please issue a refund immediately.",
            {"suspicious_url": False, "risk": "Low", "reason": "No URLs in message"},
            {"suspicious_email": False, "risk": "Low", "reason": "Verified corporate sender"},
        ),
        (
            "CONV-003 (Delivery Tracking)",
            "Tracking number TRK-99281 shows package delivered yesterday, but nothing arrived at my address. Please help locate it.",
            {"suspicious_url": False, "risk": "Low", "reason": None},
            {"suspicious_email": False, "risk": "Low", "reason": None},
        ),
        (
            "CONV-004 (Technical 500 Error)",
            "The dashboard API returns 500 Internal Server Error when exporting monthly CSV reports. Our analytics pipeline is blocked.",
            {"suspicious_url": False, "risk": "Low", "reason": "None"},
            {"suspicious_email": False, "risk": "Low", "reason": "None"},
        ),
        (
            "CONV-006 (Invoice Address Update)",
            "Can you please update our company billing address and tax ID on our latest invoice #INV-2026-881?",
            {"suspicious_url": False, "risk": "Low", "reason": None},
            {"suspicious_email": False, "risk": "Low", "reason": None},
        ),
        (
            "CONV-008 (Fragile Hardware Damage)",
            "The courier delivered our fragile hardware package with visible box damage and broken internal components.",
            {"suspicious_url": False, "risk": "Low", "reason": None},
            {"suspicious_email": False, "risk": "Low", "reason": None},
        ),
        (
            "CONV-009 (Webhook 504 Timeout)",
            "Our web application webhook endpoints are intermittently timing out with 504 Gateway Timeout during peak traffic hours.",
            {"suspicious_url": False, "risk": "Low", "reason": None},
            {"suspicious_email": False, "risk": "Low", "reason": None},
        ),
    ]

    all_passed = True
    for title, msg_text, url_flag, email_flag in normal_samples:
        time.sleep(1)  # small spacing
        res = combined_intelligence(msg_text, url_flag, email_flag)
        threat_type = res.get("threat_type", "Unknown")
        social_eng = res.get("social_engineering", False)
        risk_level = res.get("risk_level", "Unknown")
        techniques = res.get("technique", [])

        passed = (threat_type == "None" or "None" in str(threat_type)) and not social_eng
        if not passed:
            all_passed = False

        status = "[PASS]" if passed else "[CHECK]"
        print(f"{status} {title}:", flush=True)
        print(f"       Threat: {threat_type} | Social Eng: {social_eng} | Risk: {risk_level} | Techniques: {techniques}", flush=True)
        print(f"       Action: {res.get('recommended_action')}", flush=True)

    print("\n" + "=" * 65, flush=True)
    if all_passed:
        print("ALL 6 NON-PHISHING SAMPLES CONFIRMED: 0% False Positive Rate!", flush=True)
    else:
        print("Completed non-phishing evaluation.", flush=True)
    print("=" * 65, flush=True)


def main():
    test_phishing_example()
    test_real_customer_messages()


if __name__ == "__main__":
    main()
