"""
Unit and integration tests for the SybrV2 Admin Intelligence Portal,
human review workflow, operational status/assignments, internal notes,
data isolation, and category/security/AI analytics.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db import upsert_profile, upsert_conversation
from app.schemas import ConversationRecord, SecurityDetail, SummaryDetail

client = TestClient(app)

CUSTOMER_TOKEN = "Bearer demo-token"
ADMIN_TOKEN = "Bearer admin-demo-token"
CUSTOMER_B_TOKEN = "Bearer demo-user-999"


@pytest.fixture(autouse=True)
def setup_test_data():
    """Ensure baseline test profiles and a test conversation exist."""
    upsert_profile("demo-user-001", "demo@sybr.local", "Demo Customer", role="customer")
    upsert_profile("admin-user-001", "admin@sybr.local", "System Administrator", role="admin")
    upsert_profile("demo-user-999", "user999@sybr.local", "Customer B", role="customer")


def create_test_conversation(conv_id: str, user_id: str = "demo-user-001") -> ConversationRecord:
    record = ConversationRecord(
        conversation_id=conv_id,
        user_id=user_id,
        channel="chat",
        customer_issue="Original issue: double billing charged",
        category="Billing/Payment",
        issue_label="Duplicate Charge",
        priority="High",
        resolution_status="Pending",
        raw_text_masked="I was charged twice for order #4001.",
        security=SecurityDetail(
            threat_detected=False,
            threat_type="None",
            risk_level="Low",
            rule_score=0,
        ),
        summary=SummaryDetail(issue="Double charge on card"),
        ai_mode="fallback",
    )
    upsert_conversation(record)
    return record


def test_admin_review_correction_workflow():
    """Verify administrator can review, correct, and audit a conversation."""
    conv_id = "REV-TEST-001"
    create_test_conversation(conv_id)

    # 1. Customer cannot call review endpoint
    cust_res = client.patch(
        f"/admin/conversations/{conv_id}/review",
        headers={"Authorization": CUSTOMER_TOKEN},
        json={"category": "Refund Request", "priority": "Medium", "reason": "Not double charge, just slow refund"}
    )
    assert cust_res.status_code == 403

    # 2. Admin submits correction
    admin_res = client.patch(
        f"/admin/conversations/{conv_id}/review",
        headers={"Authorization": ADMIN_TOKEN},
        json={
            "category": "Refund Request",
            "issue_label": "Refund Delay",
            "priority": "Medium",
            "risk_level": "Low",
            "resolution_status": "Pending",
            "reason": "Corrected by senior supervisor after inspecting bank receipt."
        }
    )
    assert admin_res.status_code == 200
    data = admin_res.json()

    assert data["category"] == "Refund Request"
    assert data["issue_label"] == "Refund Delay"
    assert data["priority"] == "Medium"
    assert data["is_human_reviewed"] is True
    assert data["reviewed_by"] == "admin-user-001"
    assert data["processing_status"] == "Human Reviewed"

    # Verify original values are preserved in human_overrides
    assert data["human_overrides"] is not None
    assert "original" in data["human_overrides"]
    assert data["human_overrides"]["original"]["category"] == "Billing/Payment"
    assert data["human_overrides"]["original"]["issue_label"] == "Duplicate Charge"
    assert data["human_overrides"]["last_correction"]["reason"] == "Corrected by senior supervisor after inspecting bank receipt."

    # 3. Verify audit log entry
    logs_res = client.get("/admin/audit-logs", headers={"Authorization": ADMIN_TOKEN})
    assert logs_res.status_code == 200
    actions = [l["action"] for l in logs_res.json()]
    assert "CONVERSATION_REVIEW_CORRECTION" in actions


def test_admin_status_and_assignment_workflow():
    """Verify administrator can update status, assign, and escalate."""
    conv_id = "STATUS-TEST-001"
    create_test_conversation(conv_id)

    # Customer forbidden
    res_cust = client.patch(
        f"/admin/conversations/{conv_id}/status",
        headers={"Authorization": CUSTOMER_TOKEN},
        json={"processing_status": "Escalated"}
    )
    assert res_cust.status_code == 403

    # Admin escalates and assigns
    res_admin = client.patch(
        f"/admin/conversations/{conv_id}/status",
        headers={"Authorization": ADMIN_TOKEN},
        json={
            "processing_status": "Escalated",
            "resolution_status": "Pending",
            "assigned_to": "admin-user-001"
        }
    )
    assert res_admin.status_code == 200
    updated = res_admin.json()
    assert updated["processing_status"] == "Escalated"
    assert updated["assigned_to"] == "admin-user-001"
    assert updated["escalated_at"] is not None
    assert updated["assigned_at"] is not None


def test_admin_internal_notes_and_privacy_isolation():
    """Verify internal notes are saved, audited, and strictly stripped from customer views."""
    conv_id = "NOTE-TEST-001"
    create_test_conversation(conv_id, user_id="demo-user-001")

    # 1. Customer cannot add an internal note
    cust_post = client.post(
        f"/admin/conversations/{conv_id}/notes",
        headers={"Authorization": CUSTOMER_TOKEN},
        json={"text": "Customer trying to add internal note"}
    )
    assert cust_post.status_code == 403

    # 2. Admin adds internal note
    admin_post = client.post(
        f"/admin/conversations/{conv_id}/notes",
        headers={"Authorization": ADMIN_TOKEN},
        json={"text": "CONFIDENTIAL: Checked payment gateway logs. Payment gateway confirms reversal in progress."}
    )
    assert admin_post.status_code == 200
    note = admin_post.json()
    assert "id" in note
    assert "CONFIDENTIAL" in note["text"]
    assert note["author_id"] == "admin-user-001"

    # 3. Customer views conversation -> internal notes must be empty!
    cust_view = client.get(f"/conversations/{conv_id}", headers={"Authorization": CUSTOMER_TOKEN})
    assert cust_view.status_code == 200
    cust_data = cust_view.json()
    assert cust_data["internal_notes"] == []  # Completely stripped!
    assert cust_data["human_overrides"] is None

    # 4. Admin views conversation -> internal notes are present
    admin_view = client.get(f"/conversations/{conv_id}", headers={"Authorization": ADMIN_TOKEN})
    assert admin_view.status_code == 200
    admin_data = admin_view.json()
    assert len(admin_data["internal_notes"]) >= 1
    assert "CONFIDENTIAL" in admin_data["internal_notes"][0]["text"]


def test_request_review_and_draft_response():
    """Verify request review queue flagging and draft response generation."""
    conv_id = "DRAFT-TEST-001"
    create_test_conversation(conv_id)

    # Flag for review
    flag_res = client.post(
        f"/admin/conversations/{conv_id}/request-review?reason=Ambiguous+complaint",
        headers={"Authorization": ADMIN_TOKEN}
    )
    assert flag_res.status_code == 200
    assert flag_res.json()["needs_human_review"] is True
    assert flag_res.json()["review_reason"] == "Ambiguous complaint"

    # Generate draft response
    draft_res = client.post(
        f"/admin/conversations/{conv_id}/draft-response",
        headers={"Authorization": ADMIN_TOKEN},
        json={"tone": "empathetic"}
    )
    assert draft_res.status_code == 200
    draft_data = draft_res.json()
    assert "draft_response" in draft_data
    assert "recommended_action" in draft_data
    assert len(draft_data["draft_response"]) > 20


def test_admin_analytics_and_customer_endpoints():
    """Verify category analytics, security analytics, AI performance, and customer history."""
    # Ensure test conversations exist
    create_test_conversation("ANALYTICS-CUST-1", user_id="demo-user-001")
    create_test_conversation("ANALYTICS-CUST-2", user_id="demo-user-999")

    # 1. Customer cannot access analytics
    for endpoint in ("/admin/analytics/categories", "/admin/analytics/security", "/admin/analytics/ai", "/admin/customers"):
        res = client.get(endpoint, headers={"Authorization": CUSTOMER_TOKEN})
        assert res.status_code == 403

    # 2. Admin access category analytics
    cat_res = client.get("/admin/analytics/categories", headers={"Authorization": ADMIN_TOKEN})
    assert cat_res.status_code == 200
    assert "categories" in cat_res.json()
    assert cat_res.json()["total_conversations"] >= 1

    # 3. Admin access security analytics
    sec_res = client.get("/admin/analytics/security", headers={"Authorization": ADMIN_TOKEN})
    assert sec_res.status_code == 200
    sec_data = sec_res.json()
    assert "total_threats" in sec_data
    assert "threat_types" in sec_data

    # 4. Admin access AI performance
    ai_res = client.get("/admin/analytics/ai", headers={"Authorization": ADMIN_TOKEN})
    assert ai_res.status_code == 200
    ai_data = ai_res.json()
    assert "total_analyzed" in ai_data
    assert "model_name" in ai_data

    # 5. Admin access customer directory
    cust_res = client.get("/admin/customers", headers={"Authorization": ADMIN_TOKEN})
    assert cust_res.status_code == 200
    customers = cust_res.json()
    assert len(customers) >= 1
    assert any(c["customer_id"] == "demo-user-001" for c in customers)

    # 6. Admin access specific customer history
    history_res = client.get("/admin/customers/demo-user-001", headers={"Authorization": ADMIN_TOKEN})
    assert history_res.status_code == 200
    history_data = history_res.json()
    assert history_data["customer_id"] == "demo-user-001"
    assert history_data["total_conversations"] >= 1
