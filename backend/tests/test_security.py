"""
Unit tests for Phase 1 Security Rule Engine (F7, F8, F9-rules, E1).
"""
import pytest
from app.security.url_check import extract_urls, analyze_url, check_lookalike
from app.security.email_check import extract_emails_from_text, analyze_email
from app.security.attachment_check import analyze_attachment
from app.security.text_cues import analyze_text_cues
from app.security.scoring import evaluate_security_rules, apply_merge_and_overrides


def test_url_extraction():
    text = "Visit http://paypa1-security.example/login or https://bit.ly/3xY for details."
    urls = extract_urls(text)
    assert len(urls) == 2
    assert "http://paypa1-security.example/login" in urls
    assert "https://bit.ly/3xY" in urls


def test_url_lookalike_and_ip_literal():
    # Lookalike of paypal
    finding = analyze_url("http://paypa1-security.example/login")
    assert finding.lookalike_of == "paypal"
    assert finding.risk == "High"
    assert any("Lookalike" in r for r in finding.reasons)

    # IP literal
    ip_finding = analyze_url("http://192.168.1.100/verify")
    assert ip_finding.ip_literal is True
    assert ip_finding.risk in ("Medium", "High")

    # Shortener
    short_finding = analyze_url("https://bit.ly/reward-claim")
    assert short_finding.shortener is True


def test_email_spoofing_and_freemail():
    # Display name claims PayPal but domain is attacker
    finding = analyze_email("security@attacker-domain.com", display_name="PayPal Support")
    assert finding.domain_mismatch is True
    assert finding.risk in ("Medium", "High")

    # Free-mail pretending to be internal IT support
    free_finding = analyze_email("it.helpdesk@gmail.com", display_name="Company IT Support")
    assert free_finding.free_mail is True
    assert any("free webmail" in r for r in free_finding.reasons)


def test_attachment_danger():
    # Double extension
    res1 = analyze_attachment("Invoice_March2026.pdf.exe")
    assert res1.risk == "High"
    assert any("double extension" in r for r in res1.reasons)

    # Macro document
    res2 = analyze_attachment("salary_slip.xlsm")
    assert res2.risk in ("Medium", "High")
    assert res2.extension == "xlsm"

    # Benign file
    res3 = analyze_attachment("screenshot.png")
    assert res3.risk == "Low"


def test_text_cues_social_engineering():
    sample = "URGENT: Please install AnyDesk immediately and share the 6-digit OTP code to prevent account suspension."
    results = analyze_text_cues(sample)
    assert "Urgency" in results["techniques"]
    assert "Remote Access" in results["techniques"]
    assert "OTP Request" in results["techniques"]
    assert results["otp_request"] is True
    assert results["score"] >= 60


def test_override_rule_credential_and_url():
    """Rule 8.6: OTP or credential request AND suspicious URL -> minimum Critical."""
    threat_text = (
        "URGENT! Your account has been compromised. "
        "Click http://paypa1-security.example/login immediately and enter your password and OTP."
    )
    detail = evaluate_security_rules(threat_text)
    assert detail.risk_level == "Critical"
    assert detail.threat_detected is True
    assert detail.threat_type == "Phishing"
    assert detail.otp_request is True
    assert detail.credential_request is True
    assert any("Critical Override" in r for r in detail.risk_reasons)


def test_golden_demo_cases():
    # Golden Demo Case 3: Phishing alert
    text3 = "URGENT! Your account has been compromised. Click this link immediately and enter your username, password and OTP: http://secure-update-verify.com/login"
    sec3 = evaluate_security_rules(text3)
    assert sec3.risk_level == "Critical"
    assert sec3.threat_type == "Phishing"

    # Golden Demo Case 4: Lookalike URL
    text4 = "Please verify at http://paypa1-security.example/login"
    sec4 = evaluate_security_rules(text4)
    assert sec4.suspicious_url is True
    assert any(u.lookalike_of == "paypal" for u in sec4.urls)
    assert sec4.risk_level in ("High", "Critical")

    # Golden Demo Case 5: Email spoofing
    sec5 = evaluate_security_rules("Please confirm", explicit_emails=[("PayPal Service", "support@paypa1-security.example")])
    assert sec5.suspicious_email is True
    assert sec5.emails[0].lookalike_of == "paypal"
