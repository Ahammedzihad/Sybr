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


if __name__ == "__main__":
    main()
