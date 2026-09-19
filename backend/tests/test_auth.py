"""
Phase 4: Authentication, Authorization, Session Handling, and Cross-User Data Isolation Tests.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings

client = TestClient(app)


def test_auth_login_demo_mode_success():
    """Verify login in demo mode returns valid token and user profile."""
    res = client.post("/auth/login", json={"email": "operator@company.com", "password": "securepassword123"})
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "operator@company.com"
    assert data["is_demo"] is True


def test_auth_login_invalid_input():
    """Verify login with invalid email or empty password returns 400."""
    res = client.post("/auth/login", json={"email": "not-an-email", "password": "123"})
    assert res.status_code == 400

    res2 = client.post("/auth/login", json={"email": "valid@email.com", "password": "   "})
    assert res2.status_code == 400


def test_auth_me_with_demo_token():
    """Verify /auth/me returns current user profile when authenticated."""
    res = client.get("/auth/me", headers={"Authorization": "Bearer demo-token"})
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == "demo-user-001"
    assert data["is_demo"] is True


def test_auth_logout():
    """Verify logout endpoint invalidates session."""
    res = client.post("/auth/logout", headers={"Authorization": "Bearer demo-token"})
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_invalid_token_returns_401():
    """Verify any invalid token gets HTTP 401 Unauthorized."""
    res = client.get("/auth/me", headers={"Authorization": "Bearer invalid_secret_token_xyz"})
    assert res.status_code == 401
    assert "Invalid or expired" in res.json()["detail"]


def test_unauthorized_when_auth_enabled(monkeypatch):
    """Verify missing credentials return 401 when ENABLE_AUTH=True."""
    monkeypatch.setattr(settings, "ENABLE_AUTH", True)
    res = client.get("/auth/me")
    assert res.status_code == 401
    assert "Authentication credentials were not provided" in res.json()["detail"]


def test_signup_enabled_and_success():
    """Verify public signup is enabled and creates an account."""
    res = client.post("/auth/signup", json={"email": "newuser@sybr.local", "password": "password123", "display_name": "New User"})
    assert res.status_code == 200
    assert "created successfully" in res.json()["message"] or "Account" in res.json()["message"]


def test_signup_gated_by_flag(monkeypatch):
    """Verify public signup is 403 Forbidden when flag is disabled."""
    monkeypatch.setattr(settings, "ENABLE_SIGNUP", False)
    res = client.post("/auth/signup", json={"email": "disabled@user.com", "password": "password123"})
    assert res.status_code == 403


def test_password_reset_gated_by_flag(monkeypatch):
    """Verify password reset is 403 Forbidden when flag is disabled."""
    monkeypatch.setattr(settings, "ENABLE_PASSWORD_RESET", False)
    res = client.post("/auth/reset-password", json={"email": "forgot@user.com"})
    assert res.status_code == 403



def test_cross_user_data_isolation():
    """
    Verify per-user data isolation on the backend:
    User A's conversations are not visible to User B, and User B cannot delete User A's record.
    """
    token_a = "Bearer demo-user-100"
    token_b = "Bearer demo-user-200"

    # 1. User A analyzes a ticket
    create_res = client.post(
        "/analyze",
        headers={"Authorization": token_a},
        json={
            "text": "User A private billing inquiry: invoice #889900.",
            "channel": "chat"
        }
    )
    assert create_res.status_code == 200
    record_a = create_res.json()
    conv_id = record_a["conversation_id"]

    # 2. User A can retrieve it
    detail_res_a = client.get(f"/conversations/{conv_id}", headers={"Authorization": token_a})
    assert detail_res_a.status_code == 200
    assert detail_res_a.json()["conversation_id"] == conv_id

    # 3. User B cannot see it via direct detail GET (returns 404)
    detail_res_b = client.get(f"/conversations/{conv_id}", headers={"Authorization": token_b})
    assert detail_res_b.status_code == 404

    # 4. User B cannot delete User A's conversation (returns 404)
    del_res_b = client.delete(f"/conversations/{conv_id}", headers={"Authorization": token_b})
    assert del_res_b.status_code == 404

    # 5. User A deletes their own conversation (returns 200)
    del_res_a = client.delete(f"/conversations/{conv_id}", headers={"Authorization": token_a})
    assert del_res_a.status_code == 200
    assert del_res_a.json()["status"] == "deleted"

    # 6. Verify deleted for User A
    detail_res_a2 = client.get(f"/conversations/{conv_id}", headers={"Authorization": token_a})
    assert detail_res_a2.status_code == 404
