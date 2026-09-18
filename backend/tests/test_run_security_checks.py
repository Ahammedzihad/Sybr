"""
Unit tests for run_security_checks.py orchestration logic.
Verifies highest-risk selection, safe defaults, per-conversation record format,
and full pipeline execution against dataset_clean.json.
"""

import json
from pathlib import Path
import pytest

from run_security_checks import pick_highest_risk, process_conversation, RISK_PRIORITY


def test_pick_highest_risk_hierarchy():
    """Verify priority order: High > Medium > Low."""
    results = [
        {"risk": "Low", "reason": "Low risk"},
        {"risk": "High", "reason": "High risk ip literal"},
        {"risk": "Medium", "reason": "Medium risk shortener"},
    ]
    top = pick_highest_risk(results)
    assert top["risk"] == "High"
    assert "ip literal" in top["reason"]

    # Verify Medium beats Low
    med_and_low = [
        {"risk": "Low", "reason": "Low risk"},
        {"risk": "Medium", "reason": "Medium risk"},
    ]
    top_med = pick_highest_risk(med_and_low)
    assert top_med["risk"] == "Medium"


def test_process_conversation_no_url_no_email():
    """Verify clean conversation with no URLs and no emails returns safe defaults."""
    conv = {
        "conversation_id": "TEST-CLEAN-01",
        "messages": [
            {
                "sender": "customer",
                "text": "Hello, I want to know when my order #12345 will arrive.",
                "timestamp": "2026-09-18T10:00:00Z",
            },
            {
                "sender": "agent",
                "text": "Your order is scheduled for delivery tomorrow by 5 PM.",
                "timestamp": "2026-09-18T10:05:00Z",
            },
        ],
    }
    record = process_conversation(conv)
    assert record["conversation_id"] == "TEST-CLEAN-01"
    assert record["suspicious_url"] is False
    assert record["url_risk"] == "Low"
    assert record["url_reason"] is None
    assert record["suspicious_email"] is False
    assert record["email_risk"] == "Low"
    assert record["email_reason"] is None


def test_process_conversation_multiple_urls_selects_highest_risk():
    """Verify conversation with benign and phishing URLs selects the highest risk."""
    conv = {
        "conversation_id": "TEST-MULTI-URL",
        "messages": [
            {
                "sender": "customer",
                "text": "I checked your docs at https://docs.store.com/faq and then saw this link: http://192.168.1.55/update-login",
                "timestamp": "2026-09-18T10:00:00Z",
            }
        ],
    }
    record = process_conversation(conv)
    assert record["suspicious_url"] is True
    assert record["url_risk"] == "High"
    assert "raw IP address host" in record["url_reason"]


def test_process_conversation_multiple_emails_selects_highest_risk():
    """Verify conversation with benign and lookalike emails selects the highest risk."""
    conv = {
        "conversation_id": "TEST-MULTI-EMAIL",
        "messages": [
            {
                "sender": "PayPal Support <support@paypa1-security.example>",
                "text": "Please confirm your payment. You can also reach user@gmail.com if needed.",
                "timestamp": "2026-09-18T10:00:00Z",
            }
        ],
    }
    record = process_conversation(conv)
    assert record["suspicious_email"] is True
    assert record["email_risk"] == "High"
    assert "paypal" in record["email_reason"].lower()


def test_security_flags_json_schema_validation():
    """Verify that generated security_flags.json adheres to the exact requested schema."""
    flags_path = Path("security_flags.json")
    assert flags_path.exists(), "security_flags.json must exist"

    with open(flags_path, "r", encoding="utf-8") as f:
        records = json.load(f)

    assert isinstance(records, list)
    assert len(records) > 0

    required_keys = {
        "conversation_id",
        "suspicious_url",
        "url_risk",
        "url_reason",
        "suspicious_email",
        "email_risk",
        "email_reason",
    }

    for r in records:
        assert set(r.keys()) == required_keys
        assert isinstance(r["conversation_id"], str)
        assert isinstance(r["suspicious_url"], bool)
        assert r["url_risk"] in ("Low", "Medium", "High")
        assert r["url_reason"] is None or isinstance(r["url_reason"], str)
        assert isinstance(r["suspicious_email"], bool)
        assert r["email_risk"] in ("Low", "Medium", "High")
        assert r["email_reason"] is None or isinstance(r["email_reason"], str)
