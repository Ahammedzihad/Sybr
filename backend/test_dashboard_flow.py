"""
Test script to send 10 diverse sample conversations to /analyze
and verify that /dashboard counts match manual expectations exactly.
"""

import os
import sys
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient

BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Use an isolated SQLite database to verify pure 10-record counts
test_db = tempfile.NamedTemporaryFile(suffix="_dashboard_test.db", delete=False).name
os.environ["DATABASE_PATH"] = test_db

import storage
from main import app

client = TestClient(app)

SAMPLE_RECORDS = [
    # 1. Billing - Negative, High priority, Low risk, Unresolved
    {
        "conversation_id": "REC-01",
        "category": "Billing",
        "sentiment": "Negative",
        "priority": "High",
        "risk_level": "Low",
        "messages": [
            {"sender": "customer", "text": "I was charged twice for subscription."},
            {"sender": "customer", "text": "Still waiting for someone to help me."}
        ]
    },
    # 2. Billing - Positive, Medium priority, Low risk, Resolved
    {
        "conversation_id": "REC-02",
        "category": "Billing",
        "sentiment": "Positive",
        "priority": "Medium",
        "risk_level": "Low",
        "messages": [
            {"sender": "customer", "text": "I requested a refund for overcharge."},
            {"sender": "agent", "text": "We refunded the $40."},
            {"sender": "customer", "text": "Thank you, confirmed!"}
        ]
    },
    # 3. Account/Login - Negative, Critical priority, High risk, Unresolved
    {
        "conversation_id": "REC-03",
        "category": "Account/Login",
        "sentiment": "Negative",
        "priority": "Critical",
        "risk_level": "High",
        "messages": [
            {"sender": "customer", "text": "Emergency: locked out of admin portal."},
            {"sender": "customer", "text": "Still haven't received unlock instructions."}
        ]
    },
    # 4. Account/Login - Neutral, Medium priority, Low risk, Pending
    {
        "conversation_id": "REC-04",
        "category": "Account/Login",
        "sentiment": "Neutral",
        "priority": "Medium",
        "risk_level": "Low",
        "messages": [
            {"sender": "customer", "text": "Where do I update my recovery email?"},
            {"sender": "agent", "text": "Checking settings guide."}
        ]
    },
    # 5. Delivery - Negative, High priority, Low risk, Unresolved
    {
        "conversation_id": "REC-05",
        "category": "Delivery",
        "sentiment": "Negative",
        "priority": "High",
        "risk_level": "Low",
        "messages": [
            {"sender": "customer", "text": "Package missing."},
            {"sender": "customer", "text": "Still not delivered, no response from courier."}
        ]
    },
    # 6. Delivery - Positive, Low priority, Low risk, Resolved
    {
        "conversation_id": "REC-06",
        "category": "Delivery",
        "sentiment": "Positive",
        "priority": "Low",
        "risk_level": "Low",
        "messages": [
            {"sender": "agent", "text": "Delivery completed."},
            {"sender": "customer", "text": "Confirmed, thank you!"}
        ]
    },
    # 7. Security - Negative, Critical priority, Critical risk, Unresolved
    {
        "conversation_id": "REC-07",
        "category": "Security",
        "sentiment": "Negative",
        "priority": "Critical",
        "risk_level": "Critical",
        "messages": [
            {"sender": "customer", "text": "Phishing attack detected with fake URL."},
            {"sender": "customer", "text": "Attack failed again, still waiting for incident response."}
        ]
    },
    # 8. Security - Neutral, Medium priority, High risk, Pending
    {
        "conversation_id": "REC-08",
        "category": "Security",
        "sentiment": "Neutral",
        "priority": "Medium",
        "risk_level": "High",
        "messages": [
            {"sender": "customer", "text": "Please check url https://verify-bank.com"},
            {"sender": "agent", "text": "Security team is reviewing the certificate."}
        ]
    },
    # 9. Technical - Negative, Medium priority, Low risk, Unresolved
    {
        "conversation_id": "REC-09",
        "category": "Technical",
        "sentiment": "Negative",
        "priority": "Medium",
        "risk_level": "Low",
        "messages": [
            {"sender": "customer", "text": "Mobile application crashes on iOS 18."},
            {"sender": "customer", "text": "Still broken after update."}
        ]
    },
    # 10. Billing - Negative, Medium priority, Low risk, Unresolved
    {
        "conversation_id": "REC-10",
        "category": "Billing",
        "sentiment": "Negative",
        "priority": "Medium",
        "risk_level": "Low",
        "messages": [
            {"sender": "customer", "text": "Invoice error on invoice #9001."},
            {"sender": "customer", "text": "Haven't received updated invoice."}
        ]
    }
]


def test_dashboard():
    print(f"Testing with isolated database: {test_db}")

    # 1. Post all 10 sample records through /analyze
    print(f"Ingesting {len(SAMPLE_RECORDS)} sample records via /analyze...")
    for item in SAMPLE_RECORDS:
        res = client.post("/analyze", json=item)
        assert res.status_code == 200, f"Failed on {item['conversation_id']}: {res.text}"
        data = res.json()
        assert data["conversation_id"] == item["conversation_id"]

    # 2. Fetch /dashboard metrics
    dash_res = client.get("/dashboard")
    assert dash_res.status_code == 200, dash_res.text
    dashboard = dash_res.json()

    print("\n--- Dashboard Response ---")
    import json
    print(json.dumps(dashboard, indent=2))

    # 3. Validate metrics against manual counts
    # Total
    assert dashboard["total_conversations"] == 10, f"Expected 10, got {dashboard['total_conversations']}"
    assert dashboard["total_complaints"] == 10, f"Expected 10, got {dashboard['total_complaints']}"

    # Sentiment split (Negative: 6, Positive: 2, Neutral: 2)
    assert dashboard["sentiment_split"]["Negative"] == 6
    assert dashboard["sentiment_split"]["Positive"] == 2
    assert dashboard["sentiment_split"]["Neutral"] == 2

    # Category distribution (Billing: 3, Account/Login: 2, Delivery: 2, Security: 2, Technical: 1)
    assert dashboard["category_distribution"]["Billing"] == 3
    assert dashboard["category_distribution"]["Account/Login"] == 2
    assert dashboard["category_distribution"]["Delivery"] == 2
    assert dashboard["category_distribution"]["Security"] == 2
    assert dashboard["category_distribution"]["Technical"] == 1

    # Most common complaint: Billing (3)
    assert dashboard["most_common_complaint"] == "Billing"

    # Risk level distribution (Low: 6, High: 2, Critical: 1)
    # Notice REC-07 has risk_level Critical (1), REC-03 & REC-08 have High (2), rest Low (7 or 6)
    assert dashboard["risk_level_distribution"]["Critical"] == 1
    assert dashboard["risk_level_distribution"]["High"] == 2
    assert dashboard["risk_level_distribution"]["Low"] == 7

    # Critical count (priority == Critical or risk_level == Critical)
    # REC-03 (Priority: Critical), REC-07 (Priority: Critical, Risk: Critical) -> 2
    assert dashboard["critical_count"] == 2, f"Expected 2 critical, got {dashboard['critical_count']}"

    # Unresolved count:
    # REC-01 (Unresolved), REC-03 (Unresolved), REC-05 (Unresolved), REC-07 (Unresolved), REC-09 (Unresolved), REC-10 (Unresolved)
    # -> 6
    assert dashboard["unresolved_count"] == 6, f"Expected 6 unresolved, got {dashboard['unresolved_count']}"

    # Frequently reported issues
    assert "frequently_reported_issues" in dashboard
    assert dashboard["most_frequent_issue"] != "N/A"

    print("\nALL 10 SAMPLE DASHBOARD METRICS VALIDATED AND MATCH EXACT MANUAL COUNTS!")

    # Clean up test db
    try:
        os.remove(test_db)
    except OSError:
        pass


if __name__ == "__main__":
    test_dashboard()
