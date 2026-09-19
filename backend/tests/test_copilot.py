"""
Unit and integration tests for Multimodal AI Issue Copilot.
Validates text & image diagnosis, root-cause detection, threat checks,
step-by-step checklists, and history retrieval.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# 1x1 base64 transparent PNG
TINY_PNG_B64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="


def test_copilot_diagnose_text_payment():
    """Verify diagnose endpoint processes payment complaints and returns structured checklist."""
    payload = {
        "message": "My card was charged twice for $99 on Stripe checkout and transaction failed.",
        "image_name": "charge_error.png",
        "channel": "chat"
    }
    response = client.post("/copilot/diagnose", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"].startswith("copilot-")
    assert data["category"] == "Payment & Billing"
    assert "root_cause" in data and len(data["root_cause"]) > 0
    assert isinstance(data["troubleshooting_steps"], list)
    assert len(data["troubleshooting_steps"]) >= 2
    assert "suggested_response" in data and len(data["suggested_response"]) > 0
    assert "prevention_tip" in data


def test_copilot_diagnose_with_image():
    """Verify diagnose endpoint accepts base64 image data."""
    payload = {
        "message": "Crash on dashboard when clicking export",
        "image_data": TINY_PNG_B64,
        "image_name": "export_error.png",
        "channel": "ticket"
    }
    response = client.post("/copilot/diagnose", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["image_attached"] is True
    assert data["image_name"] == "export_error.png"
    assert data["category"] == "Technical Issue"


def test_copilot_diagnose_phishing_detection():
    """Verify phishing alert triggers is_threat=True and Critical severity."""
    payload = {
        "message": "Urgent verification required: please click link and enter your master password or OTP to prevent suspension.",
        "image_name": "phishing_email.png",
        "channel": "email"
    }
    response = client.post("/copilot/diagnose", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["is_threat"] is True
    assert data["severity"] == "Critical"
    assert data["threat_details"] is not None


def test_copilot_empty_validation_error():
    """Verify endpoint rejects empty request with 400 Bad Request."""
    payload = {
        "message": "",
        "image_data": None
    }
    response = client.post("/copilot/diagnose", json=payload)
    assert response.status_code == 400
    assert "Either 'message' or 'image_data' must be provided" in response.json()["detail"]


def test_copilot_history_retrieval():
    """Verify GET /copilot/history returns array of recent diagnostic sessions."""
    response = client.get("/copilot/history?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    sample = data[0]
    assert "session_id" in sample
    assert "issue_title" in sample
    assert "troubleshooting_steps" in sample
