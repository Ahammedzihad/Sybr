"""
Test Phase 0 Scaffold: health check and schema validation.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.schemas import ConversationRecord, SecurityDetail, SummaryDetail

client = TestClient(app)


def test_health_endpoint():
    """Verify that GET /health returns 200 and conforms to HealthResponse schema."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "ai_mode" in data
    assert "model" in data
    assert "database" in data
    assert data["version"] == "1.0.0"


def test_locked_contract_defaults():
    """Verify default instantiation of ConversationRecord matches Section 5 shape."""
    record = ConversationRecord(
        conversation_id="TEST-001",
        channel="chat",
        customer_issue="Refund not received",
        category="Refund Request",
        issue_label="Refund Delay",
        keywords=["refund", "delay"],
        sentiment="Negative",
        emotion="Frustration",
        emotion_intensity=3,
        is_angry=False,
        urgency="High",
        priority="High",
        priority_reason="Refund delayed beyond SLA",
        resolution_status="Unresolved",
        resolution_reason="Waiting for payment gateway",
        summary=SummaryDetail(
            issue="Refund delayed",
            customer_request="Immediate refund",
            actions_taken="Contacted support",
            current_status="Escalated",
            priority="High",
        ),
        security=SecurityDetail(
            threat_detected=False,
            threat_type="None",
            social_engineering="No",
            techniques=[],
            suspicious_url=False,
            suspicious_domain=False,
            suspicious_email=False,
            suspicious_attachment=False,
            credential_request=False,
            otp_request=False,
            urls=[],
            emails=[],
            attachments=[],
            rule_score=0,
            risk_level="Low",
            risk_reasons=[],
            recommended_action="Normal support handling",
        ),
        ai_mode="fallback",
        processing_ms=12,
    )

    data = record.model_dump()
    # Ensure all Section 5 mandatory fields exist
    expected_fields = [
        "conversation_id",
        "channel",
        "created_at",
        "customer_issue",
        "category",
        "issue_label",
        "keywords",
        "sentiment",
        "emotion",
        "emotion_intensity",
        "is_angry",
        "urgency",
        "priority",
        "priority_reason",
        "resolution_status",
        "resolution_reason",
        "summary",
        "security",
        "ai_mode",
        "processing_ms",
    ]
    for field in expected_fields:
        assert field in data, f"Missing locked field: {field}"

    # Nested security fields
    sec_fields = [
        "threat_detected",
        "threat_type",
        "social_engineering",
        "techniques",
        "suspicious_url",
        "suspicious_domain",
        "suspicious_email",
        "suspicious_attachment",
        "credential_request",
        "otp_request",
        "urls",
        "emails",
        "attachments",
        "rule_score",
        "risk_level",
        "risk_reasons",
        "recommended_action",
    ]
    for field in sec_fields:
        assert field in data["security"], f"Missing security field: {field}"
