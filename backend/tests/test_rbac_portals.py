"""
Unit & Integration Tests for Role-Based Access Control (RBAC),
Customer Portal, Admin Portal, Last Admin Protection, and Security Audits.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings
from app.db import upsert_profile, list_profiles

client = TestClient(app)

CUSTOMER_TOKEN = "Bearer demo-token"
ADMIN_TOKEN = "Bearer admin-demo-token"
CUSTOMER_B_TOKEN = "Bearer demo-user-999"


@pytest.fixture(autouse=True)
def setup_test_profiles():
    """Ensure baseline admin and customer profiles exist for tests."""
    upsert_profile("demo-user-001", "demo@sybr.local", "Demo Customer", role="customer")
    upsert_profile("admin-user-001", "admin@sybr.local", "System Administrator", role="admin")
    upsert_profile("demo-user-999", "user999@sybr.local", "Customer B", role="customer")


def test_customer_cannot_access_admin_dashboard():
    """Verify customer role is strictly rejected with 403 on admin dashboard."""
    res = client.get("/admin/dashboard", headers={"Authorization": CUSTOMER_TOKEN})
    assert res.status_code == 403
    assert "Administrator privileges required" in res.json()["detail"]


def test_customer_cannot_access_admin_users():
    """Verify customer cannot list all user profiles."""
    res = client.get("/admin/users", headers={"Authorization": CUSTOMER_TOKEN})
    assert res.status_code == 403


def test_customer_cannot_access_admin_audit_logs():
    """Verify customer cannot read security audit logs."""
    res = client.get("/admin/audit-logs", headers={"Authorization": CUSTOMER_TOKEN})
    assert res.status_code == 403


def test_customer_cannot_access_admin_conversations_oversight():
    """Verify customer cannot access global platform conversations."""
    res = client.get("/admin/conversations", headers={"Authorization": CUSTOMER_TOKEN})
    assert res.status_code == 403


def test_customer_cannot_modify_user_roles():
    """Verify customer cannot self-promote or modify another user's role."""
    res = client.patch(
        "/admin/users/demo-user-001/role",
        headers={"Authorization": CUSTOMER_TOKEN},
        json={"role": "admin"}
    )
    assert res.status_code == 403


def test_admin_can_access_admin_dashboard():
    """Verify administrator can retrieve platform KPIs."""
    res = client.get("/admin/dashboard", headers={"Authorization": ADMIN_TOKEN})
    assert res.status_code == 200
    data = res.json()
    assert "total_users" in data
    assert "total_customers" in data
    assert "total_admins" in data
    assert "ai_status" in data
    assert "database_status" in data
    assert data["total_admins"] >= 1


def test_admin_can_list_users():
    """Verify administrator can list system profiles."""
    res = client.get("/admin/users", headers={"Authorization": ADMIN_TOKEN})
    assert res.status_code == 200
    users = res.json()
    assert len(users) >= 2
    roles = [u["role"] for u in users]
    assert "admin" in roles
    assert "customer" in roles


def test_admin_can_view_audit_logs():
    """Verify administrator can inspect security audit logs."""
    res = client.get("/admin/audit-logs", headers={"Authorization": ADMIN_TOKEN})
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_admin_conversation_oversight():
    """Verify administrator can view conversations across the platform."""
    # Create conversation under customer B
    client.post(
        "/analyze",
        headers={"Authorization": CUSTOMER_B_TOKEN},
        json={"text": "Customer B issue: billing duplicate charge.", "channel": "chat"}
    )

    res = client.get("/admin/conversations", headers={"Authorization": ADMIN_TOKEN})
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 1
    assert "items" in data


def test_customer_dashboard_scoped_data():
    """Verify Customer Dashboard returns only current customer's metrics."""
    # Analyze conversation under customer A
    res_create = client.post(
        "/analyze",
        headers={"Authorization": CUSTOMER_TOKEN},
        json={"text": "Customer A support query about account password.", "channel": "chat"}
    )
    assert res_create.status_code == 200

    dash_res = client.get("/customer/dashboard", headers={"Authorization": CUSTOMER_TOKEN})
    assert dash_res.status_code == 200
    dash = dash_res.json()
    assert "total_my_conversations" in dash
    assert dash["total_my_conversations"] >= 1
    assert "my_threats_detected" in dash
    assert "recent_activity" in dash


def test_role_promotion_and_last_admin_protection():
    """
    Verify admin can promote a customer to admin,
    and system prevents demoting the last remaining administrator.
    """
    # 1. Promote demo-user-999 to admin
    promote_res = client.patch(
        "/admin/users/demo-user-999/role",
        headers={"Authorization": ADMIN_TOKEN},
        json={"role": "admin"}
    )
    assert promote_res.status_code == 200
    assert promote_res.json()["role"] == "admin"

    # 2. Now there are 2 admins. Demoting one should succeed.
    demote_res = client.patch(
        "/admin/users/demo-user-999/role",
        headers={"Authorization": ADMIN_TOKEN},
        json={"role": "customer"}
    )
    assert demote_res.status_code == 200
    assert demote_res.json()["role"] == "customer"

    # 3. Try to demote the sole remaining admin (admin-user-001) -> must fail!
    fail_res = client.patch(
        "/admin/users/admin-user-001/role",
        headers={"Authorization": ADMIN_TOKEN},
        json={"role": "customer"}
    )
    assert fail_res.status_code == 400
    assert "Cannot demote the last remaining administrator" in fail_res.json()["detail"]


def test_audit_log_recorded_on_role_change():
    """Verify security audit log records role changes."""
    client.patch(
        "/admin/users/demo-user-001/role",
        headers={"Authorization": ADMIN_TOKEN},
        json={"role": "admin"}
    )
    # Revert back
    client.patch(
        "/admin/users/demo-user-001/role",
        headers={"Authorization": ADMIN_TOKEN},
        json={"role": "customer"}
    )

    logs_res = client.get("/admin/audit-logs", headers={"Authorization": ADMIN_TOKEN})
    assert logs_res.status_code == 200
    actions = [l["action"] for l in logs_res.json()]
    assert "ROLE_CHANGE" in actions
