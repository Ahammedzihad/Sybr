"""Unit tests for rule-based URL security analyzer."""

import pytest
from app.security.url_analyzer import URLAnalyzer


@pytest.fixture
def url_analyzer():
    return URLAnalyzer()


def test_valid_https_url(url_analyzer):
    result = url_analyzer.analyze("https://www.google.com/search?q=security")
    assert result["is_suspicious"] is False
    assert "missing_https" not in result["indicators"]
    assert "ip_literal_url" not in result["indicators"]


def test_http_url_missing_https(url_analyzer):
    result = url_analyzer.analyze("http://example.com/login")
    assert "missing_https" in result["indicators"]


def test_ip_literal_url(url_analyzer):
    result = url_analyzer.analyze("http://192.168.1.100/verify")
    assert result["is_suspicious"] is True
    assert "ip_literal_url" in result["indicators"]


def test_url_shortener(url_analyzer):
    result = url_analyzer.analyze("https://bit.ly/secure-account-verify")
    assert result["is_suspicious"] is True
    assert "url_shortener" in result["indicators"]


def test_lookalike_domain(url_analyzer):
    result = url_analyzer.analyze("https://login.micros0ft.com/auth")
    assert result["is_suspicious"] is True
    assert "lookalike_domain" in result["indicators"]


def test_suspicious_tld(url_analyzer):
    result = url_analyzer.analyze("https://secure-portal.zip/download")
    assert result["is_suspicious"] is True
    assert "suspicious_tld" in result["indicators"]


def test_userinfo_obfuscation(url_analyzer):
    result = url_analyzer.analyze("https://paypal.com@evil-site.com/signin")
    assert result["is_suspicious"] is True
    assert "userinfo_obfuscation" in result["indicators"]


def test_excessive_subdomains(url_analyzer):
    result = url_analyzer.analyze("https://corp.secure.portal.vpn.internal.attacker.com/login")
    assert result["is_suspicious"] is True
    assert "excessive_subdomains" in result["indicators"]
