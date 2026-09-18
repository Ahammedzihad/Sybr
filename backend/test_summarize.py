"""
Test script to validate summarize() function on multi-turn customer support threads.
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
    from ai.gemini_client import summarize
except ImportError:
    from backend.ai.gemini_client import summarize


def run_summarize_tests():
    print("=" * 65, flush=True)
    print("TESTING summarize() FUNCTION ON MULTI-TURN CONVERSATIONS", flush=True)
    print("=" * 65, flush=True)

    # 1. Edge Case: Single message / empty list (Must return None without calling API)
    print("\n--- [Test 1] Single Message / Empty Edge Cases ---", flush=True)
    res_empty = summarize([])
    res_single = summarize(["Customer: I need help with my account."])
    print(f"Empty list result:   {res_empty} (Expected: None)")
    print(f"Single msg result:   {res_single} (Expected: None)")
    assert res_empty is None, "Error: Empty list must return None"
    assert res_single is None, "Error: Single message must return None"
    print("[PASS] Quota conservation verified for <= 1 message threads.\n", flush=True)

    # 2. Multi-turn test threads
    threads = [
        (
            "Thread 1: Resolved Billing Refund",
            [
                {"sender": "customer", "text": "I requested a refund for overcharge of $40 on invoice #INV-9281."},
                {"sender": "agent", "text": "We reviewed the transaction and refunded the $40 back to your original payment method."},
                {"sender": "customer", "text": "Thank you, confirmed received!"},
            ],
            "Resolved",
        ),
        (
            "Thread 2: Unresolved Double Billing",
            [
                {"sender": "customer", "text": "I was charged twice for my subscription this morning."},
                {"sender": "customer", "text": "Still waiting for someone to help me, my card is blocked."},
            ],
            "Unresolved",
        ),
        (
            "Thread 3: Pending Account Settings Inquiry",
            [
                {"sender": "customer", "text": "Where do I update my recovery email and security questions?"},
                {"sender": "agent", "text": "Checking settings guide and creating an internal ticket with the security team."},
            ],
            "Pending",
        ),
        (
            "Thread 4: Critical Admin Lockout",
            [
                {"sender": "customer", "text": "Emergency: locked out of admin portal and suspicious logins detected!"},
                {"sender": "customer", "text": "Still haven't received unlock instructions, please escalate!"},
                {"sender": "agent", "text": "Security incident response is actively investigating."},
            ],
            "Pending",
        ),
    ]

    for idx, (title, msgs, expected_status) in enumerate(threads, 2):
        print(f"--- [Test {idx}] {title} ---", flush=True)
        print("Messages:", flush=True)
        for m in msgs:
            print(f"  {m['sender'].capitalize()}: {m['text']}", flush=True)

        res = summarize(msgs)
        print("Summary Result:", flush=True)
        print(json.dumps(res, indent=2), flush=True)

        # Validations
        assert isinstance(res, dict), f"Error: expected dict, got {type(res)}"
        assert "issue" in res, "Missing 'issue' key"
        assert "customer_request" in res, "Missing 'customer_request' key"
        assert "actions_taken" in res, "Missing 'actions_taken' key"
        assert "current_status" in res, "Missing 'current_status' key"
        assert "priority" in res, "Missing 'priority' key"

        status = res.get("current_status")
        print(f"Current Status: '{status}' (Expected close to: '{expected_status}')", flush=True)
        print("-" * 50, flush=True)
        time.sleep(1)

    print("\n[PASS] All summarize() tests executed successfully with valid structure!", flush=True)


if __name__ == "__main__":
    run_summarize_tests()
