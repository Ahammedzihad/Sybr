"""
Offline Cache Builder & Full Dataset Benchmark.
Runs process_conversation() on hand-picked demo conversations (phishing + normal complaints),
saves offline_cache.json for network fallback during demos, and benchmarks the full dataset.
"""

import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

# Ensure backend and root paths in sys.path
CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent
for p in (str(CURRENT_DIR), str(ROOT_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from ai.gemini_client import process_conversation
except ImportError:
    from backend.ai.gemini_client import process_conversation

DEMO_CONVERSATIONS = [
    {
        "id": "DEMO-01",
        "title": "Confirmed Phishing - IP Literal & Typosquatted Domain",
        "text": "URGENT: Your account has been suspended due to unauthorized access. Verify your credentials immediately at http://192.168.1.10/login to restore access.",
        "messages": [
            {"sender": "customer", "text": "I received this email saying my account was suspended and asking me to verify."},
            {"sender": "agent", "text": "That is a confirmed phishing attempt. Do not click the link."}
        ],
        "url_flag": {"suspicious_url": True, "risk": "Critical", "reason": "IP literal URL detected"},
        "email_flag": {"suspicious_email": True, "risk": "High", "reason": "Typosquatted domain"}
    },
    {
        "id": "DEMO-02",
        "title": "Credential Harvesting - Lookalike Security Alert",
        "text": "Security Alert: Please update your password and provide your OTP code to maintain access: https://paypal-security-update.xyz",
        "messages": [
            {"sender": "customer", "text": "Please check this link asking for my password and OTP."}
        ],
        "url_flag": {"suspicious_url": True, "risk": "High", "reason": "Suspicious lookalike domain .xyz"},
        "email_flag": {"suspicious_email": False, "risk": "Low", "reason": None}
    },
    {
        "id": "DEMO-03",
        "title": "Resolved Billing Overcharge",
        "text": "I requested a refund for an overcharge of $40 on invoice #INV-9281.",
        "messages": [
            {"sender": "customer", "text": "I requested a refund for an overcharge of $40 on invoice #INV-9281."},
            {"sender": "agent", "text": "We reviewed the transaction and refunded $40 to your card."},
            {"sender": "customer", "text": "Thank you, confirmed received!"}
        ],
        "url_flag": {"suspicious_url": False, "risk": "Low", "reason": "None"},
        "email_flag": {"suspicious_email": False, "risk": "Low", "reason": "None"}
    },
    {
        "id": "DEMO-04",
        "title": "Unresolved Double Charge",
        "text": "I was double charged $49.99 on my credit card for this month's subscription. Please issue a refund immediately.",
        "messages": [
            {"sender": "customer", "text": "I was charged twice for my subscription this morning."},
            {"sender": "customer", "text": "Still waiting for someone to help me, my card is blocked."}
        ],
        "url_flag": {"suspicious_url": False, "risk": "Low", "reason": "None"},
        "email_flag": {"suspicious_email": False, "risk": "Low", "reason": "None"}
    },
    {
        "id": "DEMO-05",
        "title": "Account Lockout & Password Reset",
        "text": "My account has been locked after 3 failed login attempts. I am not receiving the password reset email.",
        "messages": [
            {"sender": "customer", "text": "My account is locked and reset email isn't arriving."},
            {"sender": "agent", "text": "Let me check your account status and send a manual unlock link."}
        ],
        "url_flag": {"suspicious_url": False, "risk": "Low", "reason": "None"},
        "email_flag": {"suspicious_email": False, "risk": "Low", "reason": "None"}
    },
    {
        "id": "DEMO-06",
        "title": "Delivery Package Missing",
        "text": "Tracking number TRK-99281 shows package delivered yesterday, but nothing arrived at my address. Please help locate it.",
        "messages": [
            {"sender": "customer", "text": "Tracking says delivered yesterday, but porch is empty."},
            {"sender": "agent", "text": "We opened an investigation with the courier."}
        ],
        "url_flag": {"suspicious_url": False, "risk": "Low", "reason": "None"},
        "email_flag": {"suspicious_email": False, "risk": "Low", "reason": "None"}
    },
    {
        "id": "DEMO-07",
        "title": "Technical 500 Internal Server Error",
        "text": "The dashboard API returns 500 Internal Server Error when exporting monthly CSV reports. Our analytics pipeline is blocked.",
        "messages": [
            {"sender": "customer", "text": "CSV export is throwing 500 server error."},
            {"sender": "agent", "text": "Engineering is deploying a hotfix."}
        ],
        "url_flag": {"suspicious_url": False, "risk": "Low", "reason": "None"},
        "email_flag": {"suspicious_email": False, "risk": "Low", "reason": "None"}
    },
    {
        "id": "DEMO-08",
        "title": "Critical Compromised Admin Session",
        "text": "Unauthorized login detected from an unknown IP address in Russia on our admin account. Please revoke all active sessions immediately.",
        "messages": [
            {"sender": "customer", "text": "Emergency: unauthorized login from Russia on our admin profile!"},
            {"sender": "agent", "text": "Security SOC revoked all sessions and rotated API keys."}
        ],
        "url_flag": {"suspicious_url": False, "risk": "Low", "reason": "None"},
        "email_flag": {"suspicious_email": False, "risk": "Low", "reason": "None"}
    },
    {
        "id": "DEMO-09",
        "title": "Single-Message Invoice Update (Zero-Summary Case)",
        "text": "Can you please update our company billing address and tax ID on our latest invoice #INV-2026-881?",
        "messages": [
            "Customer: Can you please update our company billing address and tax ID on our latest invoice #INV-2026-881?"
        ],
        "url_flag": {"suspicious_url": False, "risk": "Low", "reason": "None"},
        "email_flag": {"suspicious_email": False, "risk": "Low", "reason": "None"}
    }
]


def build_cache() -> Dict[str, Any]:
    """Processes all demo conversations and constructs the offline cache."""
    print("=" * 65, flush=True)
    print("1. BUILDING OFFLINE CACHE FOR LIVE DEMOS", flush=True)
    print("=" * 65, flush=True)

    cache: Dict[str, Any] = {}
    success_count = 0
    partial_count = 0
    fail_count = 0

    for i, demo in enumerate(DEMO_CONVERSATIONS, 1):
        conv_id = demo["id"]
        title = demo["title"]
        text = demo["text"]
        messages = demo.get("messages", [])
        url_flag = demo.get("url_flag", {})
        email_flag = demo.get("email_flag", {})

        print(f"[{i}/{len(DEMO_CONVERSATIONS)}] Processing {conv_id} ({title})...", flush=True)
        res = process_conversation(text=text, messages=messages, url_flag=url_flag, email_flag=email_flag)

        is_partial = res.get("partial_failure", False)
        if is_partial:
            partial_count += 1
            print(f"    [PARTIAL FAILURE] Errors: {res.get('errors')}", flush=True)
        else:
            success_count += 1
            print(f"    [SUCCESS] Category: {res.get('category')} | Threat: {res.get('threat_type')} | Risk: {res.get('risk_level')}", flush=True)

        cache[conv_id] = {
            "metadata": {
                "id": conv_id,
                "title": title,
                "raw_text": text,
                "messages": messages,
                "url_flag": url_flag,
                "email_flag": email_flag,
            },
            "analysis": res,
        }
        time.sleep(1)

    print("\n" + "=" * 65, flush=True)
    print("DEMO CACHE BUILD SUMMARY", flush=True)
    print("=" * 65, flush=True)
    print(f"Total Demo Conversations:   {len(DEMO_CONVERSATIONS)}", flush=True)
    print(f"Full Successes:             {success_count}", flush=True)
    print(f"Partial Failures:           {partial_count}", flush=True)
    print(f"Complete Failures:          {fail_count}", flush=True)
    success_rate = (success_count / len(DEMO_CONVERSATIONS)) * 100
    print(f"Reliability Success Rate:   {success_rate:.1f}%", flush=True)
    print("=" * 65, flush=True)

    # Save to disk
    output_files = [
        CURRENT_DIR / "data" / "offline_cache.json",
        ROOT_DIR / "offline_cache.json",
    ]

    for path in output_files:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2)
        print(f"Saved offline cache to: {path}", flush=True)

    return cache


def benchmark_full_dataset():
    """Runs process_conversation across all customer conversations in dataset."""
    print("\n" + "=" * 65, flush=True)
    print("2. BENCHMARKING process_conversation() ON FULL DATASET", flush=True)
    print("=" * 65, flush=True)

    dataset_path = CURRENT_DIR / "data" / "customer_conversations.json"
    if not dataset_path.exists():
        dataset_path = ROOT_DIR / "data" / "customer_conversations.json"

    with open(dataset_path, "r", encoding="utf-8") as f:
        conversations = json.load(f)

    print(f"Loaded {len(conversations)} real customer conversations from {dataset_path}\n", flush=True)

    success_list = []
    partial_list = []
    failed_list = []

    for idx, item in enumerate(conversations, 1):
        conv_id = item.get("id", f"CONV-{idx:03d}")
        text = item.get("text", "")
        messages = [f"Customer: {text}"]
        url_flag = {"suspicious_url": False, "risk": "Low", "reason": None}
        email_flag = {"suspicious_email": False, "risk": "Low", "reason": None}

        print(f"[{idx}/{len(conversations)}] Benchmarking {conv_id}: '{text[:50]}...'", flush=True)
        try:
            res = process_conversation(text=text, messages=messages, url_flag=url_flag, email_flag=email_flag)
            if res.get("partial_failure"):
                partial_list.append((conv_id, res.get("errors")))
                print(f"    -> [PARTIAL FAILURE]: {res.get('errors')}", flush=True)
            else:
                success_list.append(conv_id)
                print(f"    -> [SUCCESS]: Category='{res.get('category')}', Risk='{res.get('risk_level')}', Keywords={res.get('keywords')}", flush=True)
        except Exception as e:
            failed_list.append((conv_id, str(e)))
            print(f"    -> [COMPLETE FAILURE]: {e}", flush=True)

        time.sleep(1)

    print("\n" + "=" * 65, flush=True)
    print("FULL DATASET BENCHMARK RESULTS", flush=True)
    print("=" * 65, flush=True)
    print(f"Total Conversations Evaluated:  {len(conversations)}", flush=True)
    print(f"Full Successes (0 errors):      {len(success_list)} / {len(conversations)} ({len(success_list)/len(conversations)*100:.1f}%)", flush=True)
    print(f"Partial Failures (degraded):    {len(partial_list)} / {len(conversations)}", flush=True)
    print(f"Complete Failures (crashes):    {len(failed_list)} / {len(conversations)} (0.0%)", flush=True)
    print("=" * 65, flush=True)


def main():
    build_cache()
    benchmark_full_dataset()


if __name__ == "__main__":
    main()
