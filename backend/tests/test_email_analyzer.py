"""Unit tests for rule-based Email sender security analyzer."""

import pytest
from app.security.email_analyzer import EmailAnalyzer


@pytest.fixture
def email_analyzer():
    return EmailAnalyzer()


def test_valid_corporate_email(email_analyzer):
    result = email_analyzer.analyze("alice@acme-corp.com", subject="Q3 Budget Review")
    assert result["is_suspicious"] is False
    assert len(result["indicators"]) == 0


def test_invalid_email_format(email_analyzer):
    result = email_analyzer.analyze("not-an-email", subject="Hello")
    assert result["is_suspicious"] is True
    assert "invalid_email_format" in result["indicators"]


def test_lookalike_sender_domain(email_analyzer):
    result = email_analyzer.analyze("security@micros0ft.com", subject="Password Expiry")
    assert result["is_suspicious"] is True
    assert "lookalike_sender_domain" in result["indicators"]


def test_freemail_brand_spoofing(email_analyzer):
    result = email_analyzer.analyze(
        "PayPal Helpdesk <helpdesk392@gmail.com>",
        subject="Urgent: PayPal Account Locked",
        message_preview="Please verify your banking details immediately.",
    )
    assert result["is_suspicious"] is True
    assert "freemail_brand_spoofing" in result["indicators"]


def test_suspicious_sender_tld(email_analyzer):
    result = email_analyzer.analyze("admin@account-recovery.xyz", subject="Action Required")
    assert result["is_suspicious"] is True
    assert "suspicious_sender_tld" in result["indicators"]
