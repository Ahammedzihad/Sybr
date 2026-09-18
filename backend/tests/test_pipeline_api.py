"""
Integration tests for Phase 4: Pipeline, Database, and API Endpoints.
"""
import io
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_analyze_endpoint_normal_ticket():
    """Verify POST /analyze handles routine customer complaints."""
    payload = {
        "text": "My payment of $20 failed but money was debited from my bank card 4111 2222 3333 4444. Please refund immediately.",
        "channel": "chat"
    }
    response = client.post("/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert "conversation_id" in data
    assert data["category"] in ("Billing/Payment", "Refund Request")
    assert data["security"]["threat_detected"] is False
    assert data["security"]["risk_level"] == "Low"
    # Verify PII was masked
    assert "4111 2222 3333 4444" not in data["raw_text_masked"]
    assert "[CARD]" in data["raw_text_masked"]


def test_analyze_endpoint_phishing_threat():
    """Verify POST /analyze detects phishing, OTP, and sets Critical risk."""
    payload = {
        "text": "URGENT NOTICE! Your account is compromised. Click http://paypa1-security.example/login immediately and enter your password and OTP code to verify.",
        "channel": "email"
    }
    response = client.post("/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["security"]["threat_detected"] is True
    assert data["security"]["risk_level"] == "Critical"
    assert data["security"]["threat_type"] == "Phishing"
    assert data["security"]["otp_request"] is True
    assert data["security"]["credential_request"] is True
    assert len(data["security"]["urls"]) > 0
    assert data["security"]["urls"][0]["lookalike_of"] == "paypal"


def test_csv_upload_and_job_tracking():
    """Verify POST /upload accepts CSV file and tracks background job."""
    csv_content = """ticket_id,channel,sender,message
CS-BATCH-01,chat,customer,Delivery delayed for my order #9901.
CS-BATCH-02,chat,customer,Please help me reset my account password.
"""
    file_obj = io.BytesIO(csv_content.encode("utf-8"))
    files = {"file": ("tickets.csv", file_obj, "text/csv")}

    upload_res = client.post("/upload", files=files)
    assert upload_res.status_code == 200
    upload_data = upload_res.json()
    assert "job_id" in upload_data
    job_id = upload_data["job_id"]

    # Check job status
    job_res = client.get(f"/jobs/{job_id}")
    assert job_res.status_code == 200
    job_data = job_res.json()
    assert job_data["job_id"] == job_id
    assert job_data["total"] == 2


def test_conversations_list_and_delete():
    """Verify GET /conversations, GET /conversations/{id}, and DELETE /conversations/{id}."""
    # Analyze a test ticket first
    create_res = client.post("/analyze", json={"text": "How do I update my email address?"})
    assert create_res.status_code == 200
    created_id = create_res.json()["conversation_id"]

    # List conversations
    list_res = client.get("/conversations?limit=10")
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert "items" in list_data
    assert list_data["total"] > 0
    assert any(c["conversation_id"] == created_id for c in list_data["items"])

    # Get single conversation
    detail_res = client.get(f"/conversations/{created_id}")
    assert detail_res.status_code == 200
    assert detail_res.json()["conversation_id"] == created_id

    # Delete conversation
    del_res = client.delete(f"/conversations/{created_id}")
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "deleted"

    # Verify deleted
    get_again = client.get(f"/conversations/{created_id}")
    assert get_again.status_code == 404
