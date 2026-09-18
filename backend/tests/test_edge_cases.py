"""
Comprehensive Edge-Case Test Suite for Security Pipeline Components:
- preprocess()
- check_url()
- check_email()
- extract_urls_from_text()
- extract_emails_from_text()
- run_security_checks orchestration

Covers all 7 required scenarios:
1. Message with zero URLs
2. Message with multiple URLs (highest risk arbitration)
3. Malformed email (missing @, weird format, trailing punctuation)
4. Non-English text in real dataset (French, Hindi, currencies, emojis)
5. Very long conversation threads (large text blocks, performance)
6. Empty or None text fields across every component
7. Real dataset field weirdness (missing IDs, skipped empty rows, multi-turn grouping, timestamps)
"""

import os
import sys
from pathlib import Path
import pytest

# Ensure sybr root and backend/ are in sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
for p in (str(ROOT_DIR), str(BACKEND_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

from security.preprocess import preprocess
from security.url_check import check_url, extract_urls_from_text
from security.email_check import check_email, extract_emails_from_text
from run_security_checks import process_conversation, pick_highest_risk


# ===========================================================================
# 1. Message with Zero URLs
# ===========================================================================
def test_zero_urls_handling():
    """Confirm zero URLs in message does not crash and returns empty/False result."""
    text_no_url = "Hello support, I am inquiring about my package delivery status."
    urls = extract_urls_from_text(text_no_url)
    assert urls == []

    # Pipeline conversation check with zero URLs
    conv = {
        "conversation_id": "TEST-ZERO-URL-01",
        "messages": [{"sender": "customer", "text": text_no_url}],
    }
    rec = process_conversation(conv)
    assert rec["suspicious_url"] is False
    assert rec["url_risk"] == "Low"
    assert rec["url_reason"] is None


# ===========================================================================
# 2. Message with Multiple URLs (Highest Risk Selection)
# ===========================================================================
def test_multiple_urls_highest_risk_selected():
    """Confirm that when multiple URLs are present, the highest risk is correctly selected."""
    text = (
        "Check our official site https://docs.sybr-support.com/faq for details, "
        "or visit the temporary short link http://tinyurl.com/account-bypass-verify, "
        "or access the raw admin host at http://192.168.1.100/root-login immediately."
    )
    urls = extract_urls_from_text(text)
    assert len(urls) == 3

    # Individual evaluations:
    # 1. https://docs.sybr-support.com/faq -> Low
    # 2. http://tinyurl.com/account-bypass-verify -> Medium (shortener + HTTP)
    # 3. http://192.168.1.100/root-login -> High (IP literal + HTTP)
    evals = [check_url(u) for u in urls]
    top_result = pick_highest_risk(evals)
    assert top_result["risk"] == "High"
    assert "192.168.1.100" in top_result["url"]

    # End-to-end conversation processing
    conv = {
        "conversation_id": "TEST-MULTI-URL-01",
        "messages": [{"sender": "attacker", "text": text}],
    }
    rec = process_conversation(conv)
    assert rec["suspicious_url"] is True
    assert rec["url_risk"] == "High"
    assert "raw IP address host" in rec["url_reason"]

    # Test Medium beats Low
    med_and_low_text = "See https://google.com/search and http://tinyurl.com/safe-test"
    conv_med = {
        "conversation_id": "TEST-MULTI-URL-02",
        "messages": [{"sender": "customer", "text": med_and_low_text}],
    }
    rec_med = process_conversation(conv_med)
    assert rec_med["suspicious_url"] is True
    assert rec_med["url_risk"] == "Medium"


# ===========================================================================
# 3. Malformed Email Handling
# ===========================================================================
def test_malformed_email_extraction_and_check():
    """Confirm regex doesn't crash on malformed emails and handles trailing punctuation gracefully."""
    sample_text = (
        "Contact me at support@store.com. or support@store.com, or <billing@store.com> "
        "Avoid invalid strings like notanemail, user@@doubleat.com, @nodomain.com, user@.com, "
        "or user@domain..com in body text."
    )
    extracted = extract_emails_from_text(sample_text)
    # Extracted list must strip trailing punctuation and skip malformed strings
    assert "support@store.com" in extracted
    assert "billing@store.com" in extracted
    assert "notanemail" not in extracted
    assert "user@@doubleat.com" not in extracted

    # check_email directly with malformed inputs
    res_no_at = check_email("notanemail")
    assert res_no_at["risk"] in ("Medium", "Low")
    assert "malformed" in res_no_at["reason"].lower() or not res_no_at["domain"]

    res_double_at = check_email("user@@domain.com")
    assert "malformed" in res_double_at["reason"].lower()

    # check_email with trailing punctuation strips punctuation cleanly
    res_trailing_dot = check_email("user@store.com.")
    assert res_trailing_dot["domain"] == "store.com"
    assert res_trailing_dot["risk"] == "Low"

    res_trailing_comma = check_email("user@store.com,")
    assert res_trailing_comma["domain"] == "store.com"
    assert res_trailing_comma["risk"] == "Low"

    # check_email with header format "<user@store.com>"
    res_bracketed = check_email("<support@store.com>", display_name="Store Support")
    assert res_bracketed["domain"] == "store.com"


# ===========================================================================
# 4. Non-English Text in Real Dataset
# ===========================================================================
def test_non_english_and_unicode_handling():
    """Confirm preprocess() handles French accents, Devanagari Hindi, currencies, and emojis safely."""
    # French from TICK-1007
    french_text = "Bonjour, mon colis n'est pas encore arrivé. Le numéro de suivi indique qu'il est bloqué au centre de tri. Merci de vérifier."
    cleaned_fr = preprocess(french_text)
    assert "arrivé" in cleaned_fr
    assert "numéro" in cleaned_fr
    assert "bloqué" in cleaned_fr

    # Hindi from CS-00017
    hindi_text = "नमस्ते, मुझे अपना ऑर्डर कैंसिल करना है और रिफंड चाहिए। कृपया सहायता करें।"
    cleaned_hi = preprocess(hindi_text)
    assert "नमस्ते" in cleaned_hi
    assert "ऑर्डर" in cleaned_hi
    assert "रिफंड" in cleaned_hi

    # Unicode currencies and emojis from TICK-1001, TICK-1004, TICK-1012
    mixed_unicode = "I was charged ₹1,499 twice 😡 on September 15th! Also refund €820.00 and $5,000 🙏 📦"
    cleaned_mixed = preprocess(mixed_unicode)
    assert "₹" in cleaned_mixed
    assert "€" in cleaned_mixed
    assert "$" in cleaned_mixed
    assert "😡" in cleaned_mixed
    assert "🙏" in cleaned_mixed
    assert "📦" in cleaned_mixed


# ===========================================================================
# 5. Very Long Conversation Thread (Large Text Blocks)
# ===========================================================================
def test_very_long_conversation_thread():
    """Confirm preprocessing handles large text blocks without timing out or truncating."""
    # Generate multi-turn dialogue of 300 messages (~25,000 characters)
    turns = []
    for i in range(150):
        turns.append(f"<p>Customer turn {i}: I cannot access dashboard order #{i}. Please help!</p><div>Sent from my iPhone</div>")
        turns.append(f"Agent turn {i}: Dear customer, we have refreshed ticket #{i} and cleared cache.\nBest regards,\nSupport")
    large_text = "\n".join(turns)

    assert len(large_text) > 20000
    cleaned = preprocess(large_text)

    # Must process without error and strip repetitive artifacts
    assert len(cleaned) > 8000
    assert "Sent from my iPhone" not in cleaned
    assert "Best regards" not in cleaned
    assert "<p>" not in cleaned
    assert "Customer turn 0" in cleaned
    assert "Agent turn 149" in cleaned


# ===========================================================================
# 6. Empty or None Text Field Guards
# ===========================================================================
@pytest.mark.parametrize("bad_input", [None, "", "   ", "\t\r\n", 12345, [], {}])
def test_empty_or_none_guards_all_components(bad_input):
    """Confirm every function guards against None, empty, whitespace, and non-string inputs."""
    # 1. preprocess
    res_prep = preprocess(bad_input)
    assert res_prep == ""

    # 2. check_url
    res_url = check_url(bad_input)
    assert isinstance(res_url, dict)
    assert res_url["risk"] == "Low"
    assert res_url["suspicious_url"] is False
    assert "empty or invalid" in res_url["reason"].lower()

    # 3. check_email
    res_email = check_email(bad_input)
    assert isinstance(res_email, dict)
    assert res_email["risk"] == "Low"
    assert res_email["suspicious_email"] is False
    assert "empty or invalid" in res_email["reason"].lower()

    # 4. extract_urls_from_text
    res_ext_urls = extract_urls_from_text(bad_input)
    assert res_ext_urls == []

    # 5. extract_emails_from_text
    res_ext_emails = extract_emails_from_text(bad_input)
    assert res_ext_emails == []

    # 6. process_conversation with empty message text
    conv_bad = {
        "conversation_id": "TEST-EMPTY-01",
        "messages": [{"sender": "customer", "text": bad_input}],
    }
    rec = process_conversation(conv_bad)
    assert rec["suspicious_url"] is False
    assert rec["url_risk"] == "Low"
    assert rec["url_reason"] is None
    assert rec["suspicious_email"] is False
    assert rec["email_risk"] == "Low"
    assert rec["email_reason"] is None


# ===========================================================================
# 7. Real Dataset Weirdness Specific Tests
# ===========================================================================
def test_real_data_missing_conversation_id_generation():
    """Specific Test 7a: Missing ticket_id in CSV auto-generates deterministic unique ID."""
    from load_dataset import load_real_dataset
    import tempfile

    csv_content = (
        "ticket_id,speaker_role,message_body,timestamp_utc\n"
        ",customer,\"Order tracking question.\",2026-09-15T10:00:00Z\n"
        ",agent,\"Your order has shipped.\",2026-09-15T10:05:00Z\n"
    )
    with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, encoding="utf-8") as tmp:
        tmp.write(csv_content)
        tmp_path = Path(tmp.name)

    try:
        convs, skipped = load_real_dataset(tmp_path)
        assert len(convs) == 2
        assert convs[0]["conversation_id"] == "CS-00001"
        assert convs[1]["conversation_id"] == "CS-00002"
        assert skipped == 0
    finally:
        if tmp_path.exists():
            os.unlink(tmp_path)


def test_real_data_skips_empty_or_whitespace_messages():
    """Specific Test 7b: Empty and whitespace-only message rows are skipped."""
    from load_dataset import load_real_dataset
    import tempfile

    csv_content = (
        "ticket_id,speaker_role,message_body,timestamp_utc\n"
        "TICK-1003,customer,\"\",2026-09-15T09:30:00Z\n"
        "TICK-1006,customer,\"   \",2026-09-15T11:00:00Z\n"
        "TICK-1010,customer,,2026-09-15T13:25:00Z\n"
        "TICK-1011,customer,\"Valid message content.\",2026-09-15T13:30:00Z\n"
    )
    with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, encoding="utf-8") as tmp:
        tmp.write(csv_content)
        tmp_path = Path(tmp.name)

    try:
        convs, skipped = load_real_dataset(tmp_path)
        assert skipped == 3
        assert len(convs) == 1
        assert convs[0]["conversation_id"] == "TICK-1011"
        assert len(convs[0]["messages"]) == 1
    finally:
        if tmp_path.exists():
            os.unlink(tmp_path)


def test_real_data_multi_turn_conversation_grouping():
    """Specific Test 7c: Multiple rows with duplicate conversation_id are grouped in order."""
    from load_dataset import load_real_dataset
    import tempfile

    csv_content = (
        "ticket_id,speaker_role,message_body,timestamp_utc\n"
        "TICK-1001,customer,\"First message from customer.\",2026-09-15T08:12:00Z\n"
        "TICK-1001,agent,\"Agent reply to ticket.\",2026-09-15T08:30:00Z\n"
        "TICK-1001,customer,\"Customer thank you note.\",2026-09-15T08:45:00Z\n"
    )
    with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, encoding="utf-8") as tmp:
        tmp.write(csv_content)
        tmp_path = Path(tmp.name)

    try:
        convs, skipped = load_real_dataset(tmp_path)
        assert len(convs) == 1
        assert convs[0]["conversation_id"] == "TICK-1001"
        assert len(convs[0]["messages"]) == 3
        senders = [m["sender"] for m in convs[0]["messages"]]
        assert senders == ["customer", "agent", "customer"]
    finally:
        if tmp_path.exists():
            os.unlink(tmp_path)


def test_real_data_email_artifacts_and_quotes_stripping():
    """Specific Test 7d: Embedded forwarded headers, quotes, and smart quotes are stripped cleanly."""
    raw_text = (
        "---------- Forwarded message ---------\n"
        "From: billing-alerts@store.com\n"
        "Date: Mon, Sep 14, 2026 at 10:00 AM\n"
        "Subject: Invoice #44812\n\n"
        "<div>I need a revised invoice. “Total amount approved”.</div>\n"
        "> Previous ticket #8941 closed without fix.\n"
        "Sent from my Samsung Galaxy device"
    )
    cleaned = preprocess(raw_text)
    assert "Forwarded message" not in cleaned
    assert "Sent from my Samsung Galaxy device" not in cleaned
    assert "Previous ticket #8941 closed" not in cleaned
    # Smart quotes converted to standard ASCII quotes
    assert '"' in cleaned
    assert "“" not in cleaned and "”" not in cleaned
    assert "Total" in cleaned and "approved" in cleaned
    assert "revised invoice" in cleaned
