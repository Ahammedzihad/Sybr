"""Integration tests for FastAPI endpoints with mocked Gemini."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.api.dependencies import get_gemini_service, get_repository
from app.database.database import get_db_connection
from app.database.repository import ConversationRepository
from app.schemas.analysis import AnalysisResult
from app.services.gemini_service import GeminiService


class MockGeminiService(GeminiService):
    """Mock Gemini service for testing without API calls."""

    async def analyze_message(self, sender: str, subject: str, message: str, urls: list[str]) -> AnalysisResult:
        return AnalysisResult(
            category="Phishing",
            sentiment="Urgent",
            emotion="Fear",
            priority="Critical",
            summary="Mock analysis: Suspicious communication detected.",
            resolution_status="Flagged",
            threat_type="Credential Harvesting",
            social_engineering=True,
            suspicious_url=bool(urls),
            risk_level="High",
            recommended_action="Quarantine email and block sender.",
        )


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Provides a TestClient with a fresh temporary SQLite DB and Mock Gemini."""
    db_file = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_PATH", str(db_file))
    from app.core.config import settings
    settings.DATABASE_PATH = str(db_file)

    # Initialize tables
    from app.database.database import init_db
    init_db()

    app.dependency_overrides[get_gemini_service] = lambda: MockGeminiService()
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "database" in data


def test_analyze_endpoint_success(client):
    payload = {
        "sender": "security-alert@micros0ft.com",
        "subject": "Urgent: Verify Your Microsoft Account",
        "message": "Your account is temporarily suspended. Click http://192.168.1.50/verify to unlock.",
        "urls": ["http://192.168.1.50/verify"],
    }
    response = client.post("/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()

    # Verify locked schema fields
    required_fields = [
        "category", "sentiment", "emotion", "priority", "summary",
        "resolution_status", "threat_type", "social_engineering",
        "suspicious_url", "risk_level", "recommended_action"
    ]
    for field in required_fields:
        assert field in data

    # Verify rule escalation
    assert data["suspicious_url"] is True
    assert data["risk_level"] == "Critical"  # escalated by IP-literal & lookalike sender


def test_conversations_and_dashboard_flow(client):
    # Submit message
    payload = {
        "sender": "hr@legitimate-company.com",
        "subject": "Team Lunch on Friday",
        "message": "Let's all gather at noon for lunch!",
        "urls": [],
    }
    analyze_resp = client.post("/analyze", json=payload)
    assert analyze_resp.status_code == 200

    # Retrieve conversations
    conv_resp = client.get("/conversations?page=1&limit=10")
    assert conv_resp.status_code == 200
    conv_data = conv_resp.json()
    assert conv_data["total"] >= 1
    assert len(conv_data["items"]) >= 1
    first_item = conv_data["items"][0]
    assert first_item["sender"] == payload["sender"]
    assert "analysis" in first_item

    # Retrieve dashboard metrics
    dash_resp = client.get("/dashboard")
    assert dash_resp.status_code == 200
    dash_data = dash_resp.json()
    assert dash_data["total_conversations"] >= 1
    assert "categories" in dash_data
    assert "risk_levels" in dash_data
    assert "sentiments" in dash_data
