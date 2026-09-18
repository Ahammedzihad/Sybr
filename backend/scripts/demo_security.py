"""
CLI Demo: Test Deterministic Cybersecurity Threat Rules on Live Inputs.
Run: python backend/scripts/demo_security.py
"""
import sys
import os
import json

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.security.scoring import evaluate_security_rules


SAMPLE_MESSAGES = [
    {
        "title": "Scenario 1: Legitimate Customer Support Query",
        "text": "Hello, my payment of $45 was deducted from my account but my order #10245 is not showing as confirmed. Can you please check?",
        "attachments": [],
    },
    {
        "title": "Scenario 2: Classic Banking Phishing (OTP + Lookalike URL)",
        "text": "DEAR CUSTOMER, YOUR HDFC ACCOUNT IS SUSPENDED! Visit http://hdfc-security-update.top/login immediately and enter your netbanking password and OTP to restore access.",
        "attachments": [],
    },
    {
        "title": "Scenario 3: Social Engineering & Remote Access Scam",
        "text": "This is IT Support. We detected a virus on your workstation. Please install AnyDesk immediately and provide the remote access code. Do not disclose this to anyone.",
        "attachments": [],
    },
    {
        "title": "Scenario 4: Dangerous Double Extension Attachment",
        "text": "Please find attached the invoice for your pending order. Kindly review and confirm payment.",
        "attachments": ["Invoice_March2026.pdf.exe"],
    },
]


def run_demo():
    print("=" * 70)
    print("  CYBERSECURITY THREAT INTELLIGENCE ENGINE — RULE DEMO")
    print("=" * 70)

    for idx, item in enumerate(SAMPLE_MESSAGES, start=1):
        print(f"\n--- [{idx}] {item['title']} ---")
        print(f"Message Text: \"{item['text']}\"")
        if item["attachments"]:
            print(f"Attachments: {item['attachments']}")

        result = evaluate_security_rules(
            item["text"],
            explicit_attachments=item["attachments"],
        )

        print(f"\n  Threat Detected:    {result.threat_detected}")
        print(f"  Threat Type:        {result.threat_type}")
        print(f"  Risk Level:         {result.risk_level} (Score: {result.rule_score}/100)")
        print(f"  Social Engineering: {result.social_engineering}")
        print(f"  Techniques Found:   {result.techniques}")
        print(f"  OTP Request:        {result.otp_request} | Credential Request: {result.credential_request}")
        print(f"  Action:             {result.recommended_action}")
        print("  Explainable Reasons:")
        for r in result.risk_reasons:
            print(f"    - {r}")
        print("-" * 70)


if __name__ == "__main__":
    run_demo()
