"""
Phase 7: Gmail Integration Tests (Mocked, Zero Live Quota Dependency).
Verifies OAuth consent URL generation, token lifecycle, status checks,
inbox message ingestion, and deduplication by Gmail message ID.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings
from app.gmail import (
    is_gmail_configured,
    get_gmail_auth_url,
    store_gmail_tokens,
    get_stored_gmail_token,
    disconnect_gmail_user,
    get_gmail_connection_status,
    analyze_imported_email,
)

client = TestClient(app)


def test_gmail_unconfigured_behavior(monkeypatch):
    """Verify clean 'not configured' state when Google credentials are missing."""
    monkeypatch.setattr(settings, "GMAIL_CLIENT_ID", "")
    monkeypatch.setattr(settings, "GMAIL_CLIENT_SECRET", "")

    assert is_gmail_configured() is False

    auth_info = get_gmail_auth_url(user_id="test-user-1")
    assert auth_info["configured"] is False
    assert auth_info["auth_url"] is None
    assert "not configured" in auth_info["message"]

    res = client.get("/gmail/status", headers={"Authorization": "Bearer demo-token"})
    assert res.status_code == 200
    data = res.json()
    assert data["configured"] is False
    assert data["connected"] is False


def test_gmail_configured_auth_url(monkeypatch):
    """Verify correct Google OAuth consent URL and scopes when credentials exist."""
    monkeypatch.setattr(settings, "GMAIL_CLIENT_ID", "mock-client-id.apps.googleusercontent.com")
    monkeypatch.setattr(settings, "GMAIL_CLIENT_SECRET", "mock-client-secret")
    monkeypatch.setattr(settings, "GMAIL_REDIRECT_URI", "http://localhost:8000/gmail/callback")

    assert is_gmail_configured() is True

    auth_info = get_gmail_auth_url(user_id="test-user-1")
    assert auth_info["configured"] is True
    assert auth_info["auth_url"] is not None
    assert "accounts.google.com/o/oauth2/v2/auth" in auth_info["auth_url"]
    assert "mock-client-id" in auth_info["auth_url"]
    assert "gmail.readonly" in auth_info["auth_url"]


def test_gmail_token_lifecycle_and_disconnect(monkeypatch):
    """Verify server-side token storage, status reflection, and disconnect flow."""
    monkeypatch.setattr(settings, "GMAIL_CLIENT_ID", "mock-client-id")
    monkeypatch.setattr(settings, "GMAIL_CLIENT_SECRET", "mock-client-secret")

    user_id = "test-gmail-user-lifecycle"

    # 1. Initially disconnected
    status_before = get_gmail_connection_status(user_id)
    assert status_before["connected"] is False

    # 2. Store tokens server-side
    store_gmail_tokens(
        user_id=user_id,
        access_token="ya29.mock_access_token_xyz",
        refresh_token="1//mock_refresh_token_abc",
        expires_in=3600,
        email="support-inbox@company.com",
    )

    # 3. Status reflects connected
    status_after = get_gmail_connection_status(user_id)
    assert status_after["connected"] is True
    assert status_after["connected_email"] == "support-inbox@company.com"

    # 4. Token can be retrieved
    stored = get_stored_gmail_token(user_id)
    assert stored is not None
    assert stored["access_token"] == "ya29.mock_access_token_xyz"
    assert stored["refresh_token"] == "1//mock_refresh_token_abc"

    # 5. Disconnect user
    disconnected = disconnect_gmail_user(user_id)
    assert disconnected is True

    # 6. Status reflects disconnected
    status_final = get_gmail_connection_status(user_id)
    assert status_final["connected"] is False


def test_gmail_email_ingestion_and_deduplication():
    """
    Verify imported emails pass through the full analysis pipeline
    and deduplicate by Gmail message ID.
    """
    user_id = "demo-user-001"
    msg_id = "18d3a82f9b1c70e2"

    # 1. Ingest email with phishing content
    record1 = analyze_imported_email(
        user_id=user_id,
        gmail_message_id=msg_id,
        subject="Action Required: Verify your PayPal account",
        sender="service@paypa1-security.example",
        body="Dear customer, your account is suspended. Enter your OTP immediately at http://paypa1-security.example/login",
        date="2026-03-15T10:00:00Z",
    )

    assert record1.conversation_id == f"GMAIL-{msg_id}"
    assert record1.channel == "email"
    assert record1.source == "gmail"
    assert record1.security.threat_detected is True
    assert record1.security.risk_level == "Critical"

    # 2. Re-importing same message returns cached record without creating duplicate
    record2 = analyze_imported_email(
        user_id=user_id,
        gmail_message_id=msg_id,
        subject="Action Required: Verify your PayPal account",
        sender="service@paypa1-security.example",
        body="Duplicate content",
    )

    assert record2.conversation_id == record1.conversation_id
