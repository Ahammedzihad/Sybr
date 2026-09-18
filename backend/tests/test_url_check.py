"""
Unit tests for security/url_check.py module.
Verifies check_url() output structure, protocol check, IP literal detection,
shorteners, URL length, Levenshtein lookalike detection, weighted risk scoring,
and extract_urls_from_text() parsing.
"""

import pytest
from security.url_check import check_url, extract_urls_from_text, levenshtein_distance


def test_levenshtein_distance():
    assert levenshtein_distance("paypal", "paypal") == 0
    assert levenshtein_distance("paypa1", "paypal") == 1
    assert levenshtein_distance("micros0ft", "microsoft") == 1
    assert levenshtein_distance("paypa11", "paypal") == 2
    assert levenshtein_distance("completelydifferent", "paypal") > 2


def test_check_url_schema():
    res = check_url("https://example.com/path")
    expected_keys = {
        "url", "domain", "subdomain", "https", "ip_literal",
        "shortener", "url_length", "lookalike", "risk", "reason"
    }
    assert expected_keys.issubset(set(res.keys()))
    assert isinstance(res["https"], bool)
    assert isinstance(res["ip_literal"], bool)
    assert isinstance(res["shortener"], bool)
    assert isinstance(res["url_length"], int)
    assert isinstance(res["lookalike"], bool)
    assert res["risk"] in ("Low", "Medium", "High")
    assert isinstance(res["reason"], str) and len(res["reason"]) > 0


def test_check_url_ip_literal():
    res = check_url("http://192.168.1.105/auth-renew")
    assert res["ip_literal"] is True
    assert res["https"] is False
    assert res["risk"] == "High"  # 1 (http) + 3 (ip) = 4 >= 4 -> High
    assert "raw IP address host" in res["reason"]


def test_check_url_shortener():
    res = check_url("https://bit.ly/login-redirect")
    assert res["shortener"] is True
    assert res["https"] is True


def test_check_url_lookalike():
    # paypa1 with '1' substituted for 'l'
    res = check_url("https://paypa1-security.example/disputes")
    assert res["lookalike"] is True
    assert res["risk"] in ("Medium", "High")
    assert "paypal" in res["reason"]

    # micros0ft with '0' substituted for 'o' and HTTP
    res2 = check_url("http://micros0ft-verify.example/tenant-login")
    assert res2["lookalike"] is True
    assert res2["https"] is False
    assert res2["risk"] == "High"  # 1 (http) + 3 (lookalike) = 4 -> High
    assert "microsoft" in res2["reason"]


def test_check_url_genuine_brand_is_not_lookalike():
    res = check_url("https://paypal.com/signin")
    assert res["lookalike"] is False
    assert res["risk"] == "Low"


def test_check_url_long_url():
    long_url = "https://example.com/very/long/path/with/lots/of/parameters/and/tokens/that/exceeds/seventy/five/characters/in/total/length"
    assert len(long_url) > 75
    res = check_url(long_url)
    assert res["url_length"] > 75
    assert "75" in res["reason"]


def test_extract_urls_from_text():
    # Zero URLs
    assert extract_urls_from_text("Hello, this is a plain message with no links.") == []
    assert extract_urls_from_text("") == []
    assert extract_urls_from_text(None) == []

    # Single URL with trailing punctuation
    text1 = "Please verify your account at https://paypa1-security.example/login."
    assert extract_urls_from_text(text1) == ["https://paypa1-security.example/login"]

    # Multiple URLs
    text2 = "Check out http://192.168.1.1/status and also https://backup.example.com/now!"
    urls = extract_urls_from_text(text2)
    assert len(urls) == 2
    assert "http://192.168.1.1/status" in urls
    assert "https://backup.example.com/now" in urls
