"""
Unit tests for Phase 2: Ingestion, Preprocessing, PII Masking, and TF-IDF Keywords.
"""
import pytest
from app.preprocess import (
    mask_pii,
    clean_text,
    expand_contractions,
    tokenize_and_lemmatize,
    extract_keywords,
)
from app.ingest import (
    parse_csv_content,
    parse_json_content,
    detect_column_mapping,
    normalize_analyze_request,
)
from app.schemas import AnalyzeRequest, Message


def test_pii_masking():
    raw_sample = (
        "Customer phone is 9876543210. Card used: 4111 2222 3333 4444. "
        "Aadhaar: 2345 6789 0123. PAN: ABCDE1234F. My OTP is 492019."
    )
    masked = mask_pii(raw_sample)

    assert "9876543210" not in masked
    assert "[PHONE]" in masked

    assert "4111 2222 3333 4444" not in masked
    assert "[CARD]" in masked

    assert "2345 6789 0123" not in masked
    assert "[AADHAAR]" in masked

    assert "ABCDE1234F" not in masked
    assert "[PAN]" in masked

    assert "492019" not in masked
    assert "[OTP]" in masked


def test_text_cleaning_and_contractions():
    raw_text = "<b>Hello!</b> I can't access my account and won't be able to pay."
    expanded = expand_contractions(raw_text)
    assert "cannot" in expanded
    assert "will not" in expanded

    cleaned = clean_text(raw_text)
    assert "<b>" not in cleaned
    assert "cannot" in cleaned
    assert "will not" in cleaned


def test_keyword_extraction():
    complaint = (
        "My payment failed yesterday during checkout. The amount was deducted from my bank "
        "but the order was not placed. Please issue a refund for this failed transaction."
    )
    keywords = extract_keywords(complaint, top_n=4)
    assert len(keywords) > 0
    # Common salient words should appear in top keywords
    overlap = set(keywords).intersection({"payment", "refund", "order", "failed", "deducted", "transaction"})
    assert len(overlap) >= 2


def test_csv_ingest_with_aliases_and_grouping():
    csv_data = """ticket_id,sender,timestamp,complaint
CS-101,customer,2026-03-01T10:00:00Z,Payment deducted but no confirmation received.
CS-101,support,2026-03-01T10:05:00Z,We are checking with the payment gateway.
CS-102,customer,2026-03-01T11:00:00Z,App crashes every time I open settings.
"""
    conversations = parse_csv_content(csv_data)
    assert len(conversations) == 2

    # Verify CS-101 has 2 messages grouped
    c1 = next(c for c in conversations if c["conversation_id"] == "CS-101")
    assert len(c1["messages"]) == 2
    assert c1["messages"][0].sender == "customer"
    assert c1["messages"][1].sender == "support"

    # Verify CS-102 has 1 message
    c2 = next(c for c in conversations if c["conversation_id"] == "CS-102")
    assert len(c2["messages"]) == 1


def test_json_ingest_nested():
    json_data = {
        "conversations": [
            {
                "conversation_id": "TICKET-999",
                "channel": "email",
                "messages": [
                    {"sender": "customer", "text": "Need password reset."},
                    {"sender": "agent", "text": "Reset link sent."}
                ]
            }
        ]
    }
    conversations = parse_json_content(json_data)
    assert len(conversations) == 1
    assert conversations[0]["conversation_id"] == "TICKET-999"
    assert len(conversations[0]["messages"]) == 2


def test_normalize_analyze_request():
    req = AnalyzeRequest(text="Urgent help needed with refund", channel="chat")
    res = normalize_analyze_request(req)
    assert res["conversation_id"].startswith("LIVE-")
    assert len(res["messages"]) == 1
    assert res["messages"][0].text == "Urgent help needed with refund"
