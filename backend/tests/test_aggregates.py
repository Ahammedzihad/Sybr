"""
Unit and Integration tests for Phase 5: Dashboard Analytics, Ranked Issues, Trends & Evaluation.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_dashboard_kpis_and_distributions():
    """Verify GET /dashboard returns KPIs, distributions, and trend data."""
    # Ensure at least one conversation is processed
    client.post("/analyze", json={"text": "Charged twice for my ticket, please refund."})
    client.post("/analyze", json={"text": "Phishing alert: click http://paypa1-security.example/login to verify your account."})

    response = client.get("/dashboard")
    assert response.status_code == 200
    data = response.json()

    # Check KPIs
    kpis = data["kpis"]
    assert kpis["total_conversations"] >= 2
    assert "positive_count" in kpis
    assert "negative_count" in kpis
    assert "threats_detected" in kpis
    assert kpis["threats_detected"] >= 1

    # Check distributions
    assert "Positive" in data["sentiment_distribution"]
    assert "Negative" in data["sentiment_distribution"]
    assert "Low" in data["risk_distribution"]
    assert "Critical" in data["risk_distribution"]
    assert isinstance(data["issue_frequency"], list)
    assert isinstance(data["daily_trend"], list)


def test_frequently_reported_issues():
    """Verify GET /issues returns ranked list of issue labels."""
    response = client.get("/issues")
    assert response.status_code == 200
    data = response.json()

    assert "total_conversations" in data
    assert "issues" in data
    assert isinstance(data["issues"], list)
    if data["issues"]:
        first = data["issues"][0]
        assert "issue_label" in first
        assert "count" in first
        assert "percentage" in first


def test_trends_endpoint():
    """Verify GET /trends returns time-series buckets."""
    res_day = client.get("/trends?bucket=day")
    assert res_day.status_code == 200
    assert isinstance(res_day.json(), list)

    res_week = client.get("/trends?bucket=week")
    assert res_week.status_code == 200
    assert isinstance(res_week.json(), list)


def test_eval_benchmark_metrics():
    """Verify GET /eval runs on labeled_eval.json and computes recall and precision."""
    response = client.get("/eval")
    assert response.status_code == 200
    metrics = response.json()

    assert metrics["total_eval_samples"] >= 20
    # Check targets (recall >= 90%, false positive rate <= 10%)
    assert metrics["recall"] >= 90.0, f"Recall too low: {metrics['recall']}%"
    assert metrics["false_positive_rate"] <= 10.0, f"FPR too high: {metrics['false_positive_rate']}%"
    assert metrics["precision"] >= 80.0
    assert metrics["avg_latency_ms"] >= 0.0
