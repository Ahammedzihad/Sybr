"""
Unit tests for security preprocessing and text normalization module.
Tests HTML stripping, email artifact removal, unicode normalization,
spaCy tokenization & stopword filtering, edge cases, and batch processing.
"""

import pytest
from security.preprocess import preprocess, preprocess_batch


def test_preprocess_none_and_empty():
    assert preprocess(None) == ""
    assert preprocess("") == ""
    assert preprocess("    \n\t  ") == ""


def test_preprocess_pure_html_junk():
    assert preprocess("<div><p><br/></p></div>") == ""
    assert preprocess("   <span></span>   ") == ""


def test_preprocess_html_stripping_and_entities():
    raw = "<p>Hello <b>support</b>,</p><p>My bill is &amp; remains &pound;50.</p>"
    clean = preprocess(raw)
    assert "<" not in clean
    assert ">" not in clean
    assert "&amp;" not in clean
    assert "Hello support" in clean
    assert "£50" in clean or "50" in clean


def test_preprocess_email_artifacts():
    raw = (
        "---------- Forwarded message ---------\n"
        "From: billing@company.com\n"
        "Subject: Invoice\n\n"
        "Please fix my account.\n"
        "> On Mon, Sep 15, agent wrote:\n"
        "> We are investigating.\n\n"
        "Sent from my iPhone"
    )
    clean = preprocess(raw)
    assert "Forwarded message" not in clean
    assert "From: billing@company.com" not in clean
    assert "On Mon, Sep 15" not in clean
    assert "Sent from my iPhone" not in clean
    assert "fix" in clean
    assert "account" in clean


def test_preprocess_unicode_currencies_and_emojis():
    raw = "I was charged ₹1,499 and $20.00 twice! 😡 Urgent help needed 🙏"
    clean = preprocess(raw)
    assert "₹" in clean
    assert "$" in clean
    assert "1,499" in clean
    assert "😡" in clean
    assert "🙏" in clean
    assert "charged" in clean


def test_preprocess_smart_quotes():
    raw = "Customer said “Account locked” and ‘Access denied’."
    clean = preprocess(raw)
    assert '"' in clean
    assert "“" not in clean
    assert "”" not in clean
    assert "Account locked" in clean


def test_preprocess_preserves_crucial_semantics():
    raw = "I do not have access and cannot login without verification code now."
    clean = preprocess(raw)
    # Critical security/negation words must be retained (spaCy tokenizes 'cannot' as 'can' + 'not')
    assert "not" in clean
    assert "without" in clean
    assert "login" in clean
    assert "now" in clean


def test_preprocess_non_english():
    french = "Bonjour, mon colis n'est pas encore arrivé. Merci de vérifier."
    hindi = "नमस्ते, मुझे अपना ऑर्डर कैंसिल करना है।"
    assert len(preprocess(french)) > 0
    assert len(preprocess(hindi)) > 0


def test_preprocess_batch():
    conversations = [
        {
            "conversation_id": "TEST-01",
            "messages": [
                {
                    "sender": "customer",
                    "text": "<p>Need help with invoice ₹500.</p>Sent from my iPhone",
                    "timestamp": "2026-09-18T10:00:00Z",
                },
                {
                    "sender": "agent",
                    "text": "Sure, we sent the updated invoice.",
                    "timestamp": "2026-09-18T10:05:00Z",
                }
            ]
        }
    ]

    result = preprocess_batch(conversations)
    assert len(result) == 1
    conv = result[0]
    assert "clean_text" in conv
    assert len(conv["clean_text"]) > 0
    assert "Sent from my iPhone" not in conv["clean_text"]
    assert conv["messages"][0]["clean_text"] != ""
    assert "₹500" in conv["messages"][0]["clean_text"] or "500" in conv["messages"][0]["clean_text"]
