"""
Unit tests for Phase 3: Gemini Client, Fallback Engine, and Sentiment/Emotion Analysis.
"""
import pytest
from unittest.mock import MagicMock, patch
from app.fallback import fallback_analyze, classify_category_and_issue, detect_anger_cues, analyze_sentiment
from app.schemas import Message, SecurityDetail, CustomerIntelligenceOutput, SecurityIntelligenceOutput, SummaryDetail
from app.gemini_client import analyze_with_gemini_or_fallback


def test_fallback_schema_compliance():
    msg = Message(sender="customer", text="I was charged twice for order #49102. Please refund the duplicate amount.")
    sec = SecurityDetail()
    record = fallback_analyze(
        conversation_id="CS-TEST-1",
        channel="chat",
        created_at="2026-03-01T12:00:00Z",
        raw_text_masked=msg.text,
        messages=[msg],
        keywords=["charged", "refund", "duplicate"],
        security=sec,
    )

    data = record.model_dump()
    assert record.ai_mode == "fallback"
    assert record.category == "Billing/Payment"
    assert record.issue_label == "Duplicate Charge"
    assert record.sentiment in ("Negative", "Neutral")
    assert record.priority in ("High", "Critical")
    assert record.summary.issue != ""
    assert record.summary.customer_request != ""
    assert record.summary.current_status != ""


def test_anger_detection():
    calm_text = "Hello, could you help me check my delivery status?"
    assert detect_anger_cues(calm_text) is False

    angry_text = "THIS IS THE WORST SERVICE EVER!! I WILL FILE A CONSUMER COURT COMPLAINT AGAINST YOU!!"
    assert detect_anger_cues(angry_text) is True


def test_unresolved_thread_detection():
    thread = [
        Message(sender="customer", text="My refund is still not credited."),
        Message(sender="customer", text="Again writing for the third time, why no response?"),
    ]
    full_text = "My refund is still not credited. Again writing for the third time, why no response?"
    sec = SecurityDetail()
    record = fallback_analyze(
        conversation_id="CS-UNRESOLVED",
        channel="ticket",
        created_at="2026-03-01T12:00:00Z",
        raw_text_masked=full_text,
        messages=thread,
        keywords=["refund", "credited"],
        security=sec,
    )

    assert record.resolution_status == "Unresolved"
    assert record.priority in ("High", "Critical")


def test_gemini_mocked_success():
    """Verify that when Gemini client returns valid output, record merges properly."""
    fake_call_a = CustomerIntelligenceOutput(
        category="Billing/Payment",
        issue_label="Payment Failure",
        customer_issue="Payment deducted without order confirmation",
        sentiment="Negative",
        emotion="Frustration",
        emotion_intensity=4,
        is_angry=False,
        urgency="High",
        priority="High",
        priority_reason="Money deducted, awaiting order creation",
        resolution_status="Pending",
        resolution_reason="Agent investigating transaction ID",
        summary=SummaryDetail(
            issue="Payment deducted, order not created",
            customer_request="Confirm order or issue refund",
            actions_taken="Ticket created",
            current_status="Pending investigation",
            priority="High",
        )
    )

    fake_call_b = SecurityIntelligenceOutput(
        threat_detected=False,
        threat_type="None",
        social_engineering="No",
        techniques=[],
        credential_request=False,
        otp_request=False,
        risk_level="Low",
        risk_reasons=["Legitimate customer billing complaint"],
        recommended_action="Normal support handling",
    )

    with patch("app.gemini_client.get_genai_client") as mock_get_client, \
         patch("app.gemini_client.run_gemini_call_a", return_value=fake_call_a), \
         patch("app.gemini_client.run_gemini_call_b", return_value=fake_call_b):
        
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        msg = Message(sender="customer", text="Payment failed")
        res = analyze_with_gemini_or_fallback(
            conversation_id="CS-GEMINI-1",
            channel="chat",
            created_at="2026-03-01T12:00:00Z",
            raw_text_masked="Payment failed",
            messages=[msg],
            keywords=["payment", "failed"],
            rule_security=SecurityDetail(),
        )

        assert res.ai_mode == "gemini"
        assert res.category == "Billing/Payment"
        assert res.issue_label == "Payment Failure"
        assert res.priority == "High"
        assert res.security.risk_level == "Low"
