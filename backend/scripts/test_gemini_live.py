"""
Test script for live Gemini connection.
Run: python backend/scripts/test_gemini_live.py
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.config import settings
from app.gemini_client import get_genai_client, run_gemini_call_a, run_gemini_call_b
from app.schemas import SecurityDetail


def main():
    print("=" * 60)
    print("  GEMINI API LIVE TEST")
    print("=" * 60)
    print(f"Model: {settings.GEMINI_MODEL}")
    has_key = bool(settings.GEMINI_API_KEY)
    print(f"GEMINI_API_KEY configured: {has_key}")

    if not has_key:
        print("\nNotice: GEMINI_API_KEY is not set in backend/.env.")
        print("The system will seamlessly operate in deterministic fallback mode.")
        print("To enable live Gemini AI, set GEMINI_API_KEY in backend/.env.")
        return

    client = get_genai_client()
    if not client:
        print("Failed to initialize Gemini client.")
        return

    sample = "Hello, my money was deducted ($35) but order was not placed. Please refund immediately!"
    print(f"\nSending test Call A with text: \"{sample}\"")
    try:
        res_a = run_gemini_call_a(client, sample)
        print("Call A Succeeded!")
        print(f"  Category:     {res_a.category}")
        print(f"  Issue Label:  {res_a.issue_label}")
        print(f"  Sentiment:    {res_a.sentiment}")
        print(f"  Emotion:      {res_a.emotion} (Intensity: {res_a.emotion_intensity})")
        print(f"  Priority:     {res_a.priority}")
        print(f"  Summary:      {res_a.summary.issue}")
    except Exception as e:
        print(f"Call A failed: {e}")

    sample_threat = "URGENT: Your PayPal account is suspended. Verify password at http://paypa1-security.com"
    print(f"\nSending test Call B with text: \"{sample_threat}\"")
    try:
        dummy_sec = SecurityDetail(
            threat_detected=True,
            threat_type="Phishing",
            rule_score=85,
            risk_level="Critical",
            social_engineering="Yes",
            techniques=["Credential Harvesting", "Urgency"],
            suspicious_url=True,
            suspicious_domain=True,
            suspicious_email=False,
            suspicious_attachment=False,
            credential_request=True,
            otp_request=False,
            risk_reasons=["Lookalike domain detected"],
            recommended_action="Block sender and do not click link"
        )
        res_b = run_gemini_call_b(client, sample_threat, dummy_sec)
        print("Call B Succeeded!")
        print(f"  Threat Type:        {res_b.threat_type}")
        print(f"  Social Engineering: {res_b.social_engineering}")
        print(f"  Techniques:         {res_b.techniques}")
        print(f"  Recommended Action: {res_b.recommended_action}")
    except Exception as e:
        print(f"Call B failed: {e}")


if __name__ == "__main__":
    main()
