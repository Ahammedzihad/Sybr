# AI Security Analytics — Full-Stack Boilerplate

An extensible, modular, hackathon-ready **AI-powered email and message security analysis platform** built with **FastAPI**, **Google Gemini AI**, deterministic rule-based heuristic analyzers, **SQLite**, and a **React + TypeScript + Recharts** dashboard.

---

## 1. Project Overview

Modern cyberattacks blend technical evasion (IP-literal URLs, lookalike typosquatting domains, URL shorteners) with psychological manipulation (urgency, fear, credential harvesting).

This platform combines:
1. **Rule-Based Security Engine**: Deterministic detection of URL shorteners, IP-literal URLs, missing HTTPS, lookalike typosquatting domains, and free-mail brand spoofing.
2. **Google Gemini Threat Reasoning**: Structured AI analysis of communication tone, emotional coercion, summary generation, and actionable security recommendations.
3. **Locked 11-Field Analysis Schema**: Strict type-safe contract across AI inference, backend aggregation, persistent storage, and frontend visualization.
4. **Persistent Lightweight Storage**: Zero-dependency SQLite repository with WAL mode and indexing.
5. **SOC Analyst Dashboard**: Real-time KPI metrics, interactive charts (Recharts), 1-click test samples, and paginated conversation history.

---

## 2. Architecture

```text
                           [ React + TypeScript Frontend ]
                                  (Port 5173 / Vite)
                                          │
                            REST API (HTTP / JSON Client)
                                          ▼
                               [ FastAPI Backend ]
                                  (Port 8000)
                                          │
                 ┌────────────────────────┼────────────────────────┐
                 ▼                        ▼                        ▼
           [ API Routes ]        [ Analysis Service ]      [ Dashboard Aggregation ]
           - /health                      │                        │
           - /analyze       ┌─────────────┴─────────────┐          │
           - /conversations ▼                           ▼          │
           - /dashboard  [ Security Rules ]     [ Gemini Service ] │
                         - URL Analyzer         - Structured JSON  │
                         - Email Analyzer       - Safe Mock Mode   │
                         - Typosquatting/TLD    - Google GenAI SDK │
                                │                       │          │
                                └─────────────┬─────────┘          │
                                              ▼                    │
                                     [ Reconcile & Merge ]         │
                                              │                    │
                                              ▼                    ▼
                                      [ SQLite Repository ] ◄──────┘
                                        (WAL Mode / ACID)
```

---

## 3. Technology Stack

- **Backend**:
  - Python 3.11+
  - FastAPI & Uvicorn
  - Pydantic v2 & Pydantic-Settings
  - Google GenAI SDK (`google-genai` & `google-generativeai`)
  - `tldextract` & `re` for domain and pattern heuristics
  - SQLite3 (Standard Library)
  - Pytest & HTTPX
- **Frontend**:
  - React 18 & TypeScript
  - Vite
  - Recharts (Pie, Bar, Horizontal Bar)
  - Tailwind CSS (Dark Cybersecurity Theme)
  - Lucide React Icons
- **Documentation**:
  - OpenAPI / Swagger (`/docs`) & ReDoc (`/redoc`)
  - Team integration contract (`docs/api-contract.md`)

---

## 4. Root Project Structure

```text
ai-security-analytics/
│
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI app & lifespan initialization
│   │   ├── api/
│   │   │   ├── dependencies.py      # Dependency injection providers
│   │   │   └── routes/
│   │   │       ├── analyze.py       # POST /analyze
│   │   │       ├── conversations.py # GET /conversations
│   │   │       └── dashboard.py     # GET /dashboard
│   │   ├── core/
│   │   │   ├── config.py            # Environment configuration
│   │   │   └── logging.py           # Credential-masked structured logger
│   │   ├── database/
│   │   │   ├── database.py          # SQLite WAL connection manager
│   │   │   ├── models.py            # SQL table definitions
│   │   │   └── repository.py        # ConversationRepository data access
│   │   ├── schemas/
│   │   │   ├── analysis.py          # Locked 11-field AnalysisResult schema
│   │   │   ├── conversation.py      # Conversation and pagination schemas
│   │   │   └── dashboard.py         # Dashboard telemetry schema
│   │   ├── security/                # PERSON 1: Security Rule Engine
│   │   │   ├── email_analyzer.py    # Email spoofing & brand detection
│   │   │   ├── rules.py             # Shorteners, high-risk TLDs, lookalikes
│   │   │   └── url_analyzer.py      # IP literals, HTTP/HTTPS, punycode, TLDs
│   │   ├── services/
│   │   │   ├── aggregation_service.py # Telemetry aggregator
│   │   │   ├── analysis_service.py    # PERSON 3: Pipeline orchestrator
│   │   │   └── gemini_service.py      # PERSON 2: Gemini AI & mock fallback
│   │   └── utils/
│   │       └── json_parser.py       # Resilient JSON extractor for LLMs
│   ├── tests/
│   │   ├── test_analyze.py          # API integration tests
│   │   ├── test_email_analyzer.py   # Email heuristic unit tests
│   │   └── test_url_analyzer.py     # URL heuristic unit tests
│   ├── requirements.txt
│   ├── .env.example
│   └── README.md
│
├── frontend/
│   ├── src/
│   │   ├── api/client.ts            # Centralized API client
│   │   ├── components/              # KPICard, RiskBadge, Navbar, Charts
│   │   ├── pages/                   # Dashboard, Analyze, Conversations
│   │   ├── types/analysis.ts        # Locked TypeScript interfaces
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   ├── vite.config.ts
│   ├── .env.example
│   └── README.md
│
├── docs/
│   └── api-contract.md              # Team contracts & REST specification
├── .gitignore
└── README.md
```

---

## 5. Locked Analysis JSON Schema

All analysis outputs strictly comply with this 11-field schema:

```json
{
  "category": "Phishing",
  "sentiment": "Urgent",
  "emotion": "Fear",
  "priority": "Critical",
  "summary": "Urgent account suspension alert containing an IP-literal link and typosquatted sender domain.",
  "resolution_status": "Flagged",
  "threat_type": "Credential Harvesting",
  "social_engineering": true,
  "suspicious_url": true,
  "risk_level": "Critical",
  "recommended_action": "Block sender domain, quarantine message, and blacklist URL on network proxy."
}
```

---

## 6. Team of 4 Division of Responsibilities

The codebase features decoupled modules designed for a 4-person hackathon team to work concurrently without merge conflicts:

| Role | Responsibility Area | Key Files |
| :--- | :--- | :--- |
| **Person 1: Security Rules** | URL heuristics, typosquatting lookalikes, IP literals, email spoofing, and security tests | `backend/app/security/*`<br>`backend/tests/test_url_analyzer.py`<br>`backend/tests/test_email_analyzer.py` |
| **Person 2: Gemini AI** | Gemini SDK integration, system prompts, structured JSON enforcement, and mock responses | `backend/app/services/gemini_service.py`<br>`backend/app/utils/json_parser.py` |
| **Person 3: Backend & DB** | FastAPI routes, SQLite repository, aggregation metrics, and pipeline orchestration | `backend/app/api/*`<br>`backend/app/database/*`<br>`backend/app/services/analysis_service.py` |
| **Person 4: Frontend** | React UI, Recharts telemetry charts, analyze submission page, and conversation history | `frontend/src/*` |

---

## 7. Quickstart Setup

### Step 1: Clone Repository & Configure Environment
```bash
# Clone the repository
git clone <repo-url>
cd <repo-folder>
```

### Step 2: Backend Setup
```bash
cd backend

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env

# Run FastAPI server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
- Backend API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health Check: [http://localhost:8000/health](http://localhost:8000/health)

### Step 3: Frontend Setup
In a new terminal:
```bash
cd frontend

# Install packages
npm install

# Configure environment
cp .env.example .env

# Start development server
npm run dev
```
- Frontend Dashboard: [http://localhost:5173](http://localhost:5173)

---

## 8. Environment Variables

### Backend (`backend/.env`)
```env
# Gemini API Key (Backend only, never expose to frontend)
GEMINI_API_KEY=your_gemini_api_key_here

# When true or when key is missing, mock responses are generated without API calls
GEMINI_MOCK_MODE=true

# Database storage path
DATABASE_PATH=./data/app.db

# CORS configuration
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

# Server config
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO
```

### Frontend (`frontend/.env`)
```env
# Backend API Base URL
VITE_API_BASE_URL=http://localhost:8000
```

> **Security Guardrail**: `GEMINI_API_KEY` is strictly confined to the backend service. The frontend never receives or requires the API key.

---

## 9. Mock Mode vs. Live Gemini Mode

- **Mock Mode (`GEMINI_MOCK_MODE=true` or missing API key)**:
  - Generates realistic, context-aware analysis responses based on content heuristics.
  - Zero API quota consumption.
  - Enables frontend and security engine development completely offline.
- **Live Mode (`GEMINI_MOCK_MODE=false` and valid `GEMINI_API_KEY`)**:
  - Connects to Google Gemini (`gemini-1.5-flash`).
  - Strict system instructions enforce the 11-field schema.
  - Catches parsing or network errors gracefully with fallback to avoid crashing FastAPI.

---

## 10. Automated Testing

Run the comprehensive test suite with 100% mocked external calls:
```bash
cd backend
source .venv/bin/activate
pytest -v tests
```

Tests cover:
- **URL Security**: Valid URLs, missing HTTPS, IP-literal hosts, URL shorteners, brand lookalike domains, suspicious TLDs, userinfo obfuscation, and excessive subdomains.
- **Email Security**: Valid corporate email, malformed email addresses, lookalike sender domains, and free-mail brand spoofing.
- **API Endpoints**: `/health`, `/analyze` (locked schema validation and rule escalation), `/conversations` (pagination & storage), and `/dashboard` (telemetry aggregation).
