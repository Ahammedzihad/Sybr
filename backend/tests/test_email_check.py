"""
Unit tests for security/email_check.py module.
Tests domain extraction, free-mail customer safety (zero false positives),
brand typosquatting/lookalike detection, display name mismatch impersonation,
and regex email extraction from text.
"""

import pytest
from security.email_check import check_email, extract_emails_from_text, is_lookalike_domain


def test_check_email_schema():
    res = check_email("test@example.com")
    expected_keys = {
        "email", "domain", "free_mail", "lookalike",
        "domain_mismatch", "risk", "reason"
    }
    assert expected_keys.issubset(set(res.keys()))
    assert isinstance(res["free_mail"], bool)
    assert isinstance(res["lookalike"], bool)
    assert isinstance(res["domain_mismatch"], bool)
    assert res["risk"] in ("Low", "Medium", "High")
    assert isinstance(res["reason"], str) and len(res["reason"]) > 0


def test_check_email_customer_freemail_is_low_risk():
    """
    CRITICAL REQUIREMENT: Ordinary customer emails on Gmail, Yahoo, etc.
    must be classified as Low risk with zero false positives.
    """
    res1 = check_email("alice.johnson@gmail.com", display_name="Alice Johnson")
    assert res1["free_mail"] is True
    assert res1["lookalike"] is False
    assert res1["domain_mismatch"] is False
    assert res1["risk"] == "Low"

    res2 = check_email("robert.smith@yahoo.com")
    assert res2["free_mail"] is True
    assert res2["risk"] == "Low"

    res3 = check_email("claire@outlook.com", display_name="Claire")
    assert res3["free_mail"] is True
    assert res3["risk"] == "Low"


def test_check_email_lookalike_phishing():
    # Synthetic phish 1: paypa1 typosquat
    res1 = check_email("support@paypa1-security.example", display_name="PayPal Resolution Center")
    assert res1["lookalike"] is True
    assert res1["domain_mismatch"] is True
    assert res1["risk"] == "High"
    assert "paypal" in res1["reason"]

    # Synthetic phish 2: micros0ft typosquat
    res2 = check_email("admin-alerts@micros0ft-verify.example", display_name="Microsoft 365 Admin Center")
    assert res2["lookalike"] is True
    assert res2["domain_mismatch"] is True
    assert res2["risk"] == "High"
    assert "microsoft" in res2["reason"]


def test_check_email_impersonation_on_freemail():
    # Attempting official support impersonation from a consumer Gmail address
    res = check_email("account-security@gmail.com", display_name="Corporate Security Team")
    assert res["free_mail"] is True
    assert res["domain_mismatch"] is True
    assert res["risk"] == "High"
    assert "impersonation" in res["reason"] or "suggests official role" in res["reason"]


def test_check_email_expected_org_domain():
    # Genuine internal/corporate support
    res = check_email("helpdesk@sybr-support.com", display_name="Sybr Support Desk")
    assert res["free_mail"] is False
    assert res["lookalike"] is False
    assert res["domain_mismatch"] is False
    assert res["risk"] == "Low"


def test_check_email_edge_cases():
    assert check_email(None)["risk"] == "Low"
    assert check_email("")["risk"] == "Low"
    assert check_email("   ")["risk"] == "Low"
    # Malformed without @
    res = check_email("not-an-email-address")
    assert res["risk"] in ("Medium", "High")
    assert "malformed" in res["reason"]


def test_extract_emails_from_text():
    # Zero emails
    assert extract_emails_from_text("Plain customer message.") == []
    assert extract_emails_from_text("") == []
    assert extract_emails_from_text(None) == []

    # Single email with punctuation
    text1 = "Contact support at help@sybr-support.com."
    assert extract_emails_from_text(text1) == ["help@sybr-support.com"]

    # Multiple emails
    text2 = "Forwarded from billing@store.com to admin@sybr-support.com!"
    emails = extract_emails_from_text(text2)
    assert len(emails) == 2
    assert "billing@store.com" in emails
    assert "admin@sybr-support.com" in emails
