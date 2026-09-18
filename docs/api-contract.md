# API Specification & Team Integration Contract

## 1. Overview
This document defines the strict interfaces between the four engineering roles and the REST API specification for communication between frontend and backend.

```
[ Frontend (Person 4) ]
       │  HTTP / REST
       ▼
[ FastAPI (Person 3) ]
       │
       ├──► [ Security Rules (Person 1) ]  --> Returns SecurityIndicators
       └──► [ Gemini Service (Person 2) ]  --> Returns RawAnalysis
       │
[ Aggregate & Reconcile (Person 3) ]       --> Stores & Returns Locked AnalysisResult
```

---

## 2. Locked Analysis Schema

All analysis outputs across backend, storage, and API responses strictly conform to this JSON schema:

```json
{
  "category": "Phishing | Malicious | Spam | Suspicious | Clean",
  "sentiment": "Urgent | Alarming | Negative | Neutral | Positive",
  "emotion": "Fear | Urgency | Greed | Curiosity | Neutral",
  "priority": "Critical | High | Medium | Low",
  "summary": "Concise summary of the communication and identified threat signals",
  "resolution_status": "Flagged | Blocked | Under Review | Resolved | Dismissed",
  "threat_type": "Credential Harvesting | Financial Fraud | Malicious Link | Social Engineering | None",
  "social_engineering": true,
  "suspicious_url": true,
  "risk_level": "Critical | High | Medium | Low | Safe",
  "recommended_action": "Actionable security recommendation for SOC analysts or end-users"
}
```

---

## 3. Team Division & Internal Contracts

### Role 1: Security Rules (`backend/app/security/`)
- **Input**: URLs (`List[str]`), Sender email address (`str`), Subject (`str`), Message body (`str`)
- **Output Interface**:
  ```python
  class SecurityIndicator(BaseModel):
      indicator: str
      severity: str  # Critical, High, Medium, Low
      description: str

  class RuleAnalysisResult(BaseModel):
      suspicious_url: bool
      suspicious_sender: bool
      indicators: List[str]
      details: List[SecurityIndicator]
  ```

### Role 2: Gemini Service (`backend/app/services/gemini_service.py`)
- **Input**: Email context (`sender`, `subject`, `message`, `urls`)
- **Output Interface**:
  ```python
  class GeminiService:
      async def analyze_message(
          self, sender: str, subject: str, message: str, urls: List[str]
      ) -> AnalysisResult: ...
  ```
- **Error Handling**: Catches all network/API/parsing failures and provides fallback matching the 11-field schema.

### Role 3: Backend & Aggregation (`backend/app/api/`, `services/`, `database/`)
- Orchestrates requests:
  1. Validates input with Pydantic (`AnalysisRequest`)
  2. Executes Person 1's Security Rule Engine
  3. Executes Person 2's Gemini Service
  4. Merges signals: if security rules flag `suspicious_url = True` or high-confidence phishing indicators, the final `risk_level` and `suspicious_url` are updated accordingly
  5. Persists conversation and analysis into SQLite repository
  6. Returns `AnalysisResult`
  7. Exposes `/dashboard` and `/conversations` routes with aggregations

### Role 4: Frontend (`frontend/`)
- Consumes ONLY the documented REST endpoints.
- Displays KPIs, Recharts charts, interactive submission form, and paginated conversation history.

---

## 4. REST Endpoints

### 4.1 Health Check
- **`GET /health`**
- **Response `200 OK`**:
  ```json
  {
    "status": "ok",
    "version": "1.0.0",
    "mock_mode": true,
    "database": "connected"
  }
  ```

### 4.2 Analyze Message
- **`POST /analyze`**
- **Request Body**:
  ```json
  {
    "sender": "security-alert@micros0ft-support.xyz",
    "subject": "Urgent: Your account will be locked in 24 hours",
    "message": "We detected unauthorized login attempts. Verify your identity now: http://192.168.1.10/verify",
    "urls": ["http://192.168.1.10/verify"]
  }
  ```
- **Response `200 OK`**:
  ```json
  {
    "category": "Phishing",
    "sentiment": "Urgent",
    "emotion": "Fear",
    "priority": "Critical",
    "summary": "Urgent account suspension alert with IP-literal link and typosquatted domain.",
    "resolution_status": "Flagged",
    "threat_type": "Credential Harvesting",
    "social_engineering": true,
    "suspicious_url": true,
    "risk_level": "Critical",
    "recommended_action": "Block sender domain, blacklist URL at firewall, and notify recipient."
  }
  ```

### 4.3 List Conversations
- **`GET /conversations?page=1&limit=20&risk_level=Critical`**
- **Query Parameters**:
  - `page` (int, default: 1)
  - `limit` (int, default: 20, max: 100)
  - `risk_level` (optional string)
- **Response `200 OK`**:
  ```json
  {
    "items": [
      {
        "id": "conv-3a1f9e2b",
        "sender": "security-alert@micros0ft-support.xyz",
        "subject": "Urgent: Your account will be locked in 24 hours",
        "message": "We detected unauthorized login attempts...",
        "urls": ["http://192.168.1.10/verify"],
        "created_at": "2026-09-18T10:00:00Z",
        "analysis": {
          "category": "Phishing",
          "sentiment": "Urgent",
          "emotion": "Fear",
          "priority": "Critical",
          "summary": "Urgent account suspension alert...",
          "resolution_status": "Flagged",
          "threat_type": "Credential Harvesting",
          "social_engineering": true,
          "suspicious_url": true,
          "risk_level": "Critical",
          "recommended_action": "Block sender..."
        }
      }
    ],
    "total": 1,
    "page": 1,
    "limit": 20,
    "pages": 1
  }
  ```

### 4.4 Dashboard Aggregation
- **`GET /dashboard`**
- **Response `200 OK`**:
  ```json
  {
    "total_conversations": 42,
    "high_risk_count": 18,
    "resolved_count": 12,
    "pending_count": 30,
    "categories": {
      "Phishing": 20,
      "Malicious": 8,
      "Spam": 6,
      "Suspicious": 5,
      "Clean": 3
    },
    "sentiments": {
      "Urgent": 22,
      "Negative": 10,
      "Neutral": 8,
      "Positive": 2
    },
    "emotions": {
      "Fear": 19,
      "Urgency": 14,
      "Greed": 5,
      "Neutral": 4
    },
    "risk_levels": {
      "Critical": 12,
      "High": 6,
      "Medium": 14,
      "Low": 7,
      "Safe": 3
    },
    "threat_types": {
      "Credential Harvesting": 16,
      "Financial Fraud": 9,
      "Malicious Link": 8,
      "Social Engineering": 6,
      "None": 3
    }
  }
  ```
