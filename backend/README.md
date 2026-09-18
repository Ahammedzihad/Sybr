# AI Security Analytics — Backend Service

FastAPI-powered security analysis service combining deterministic heuristic rule analyzers (URL & Email) and Google Gemini AI threat reasoning.

---

## 1. Architecture Overview

```
[ POST /analyze ] ──► [ Analysis Service ]
                              │
             ┌────────────────┴────────────────┐
             ▼                                 ▼
      [ Security Rules ]               [ Gemini Service ]
      - URLAnalyzer (IPs, lookalikes)  - Structured JSON Prompting
      - EmailAnalyzer (Spoofing)       - Resilient Mock Mode Fallback
             │                                 │
             └────────────────┬────────────────┘
                              ▼
                [ Aggregation & Reconciliation ]
                              │
                              ▼
                     [ SQLite Database ]
                     (Repository Pattern)
```

---

## 2. Directory Structure

```text
backend/
├── app/
│   ├── main.py                  # FastAPI entry point, CORS, and lifespan
│   ├── api/
│   │   ├── dependencies.py      # Dependency injection providers
│   │   └── routes/
│   │       ├── analyze.py       # POST /analyze
│   │       ├── conversations.py # GET /conversations
│   │       └── dashboard.py     # GET /dashboard
│   ├── core/
│   │   ├── config.py            # Pydantic Settings & environment variables
│   │   └── logging.py           # Safe structured logger with credential masking
│   ├── database/
│   │   ├── database.py          # SQLite connection and WAL initialization
│   │   ├── models.py            # Table definitions
│   │   └── repository.py        # ConversationRepository data access layer
│   ├── schemas/
│   │   ├── analysis.py          # Locked 11-field AnalysisResult schema
│   │   ├── conversation.py      # Paginated conversation schemas
│   │   └── dashboard.py         # Dashboard telemetry schema
│   ├── security/                # PERSON 1: Security rule engine
│   │   ├── email_analyzer.py    # Email spoofing, brand mismatch, and formatting rules
│   │   ├── rules.py             # Known shorteners, suspicious TLDs, lookalike mappings
│   │   └── url_analyzer.py      # IP literals, HTTP/HTTPS, lookalikes, punycode, shorteners
│   ├── services/
│   │   ├── aggregation_service.py # Telemetry calculations for dashboard
│   │   ├── analysis_service.py    # PERSON 3: Pipeline orchestrator
│   │   └── gemini_service.py      # PERSON 2: Google Gemini AI integration & mock mode
│   └── utils/
│       └── json_parser.py       # Resilient JSON extractor for LLM output
├── tests/
│   ├── test_analyze.py          # Endpoints integration tests
│   ├── test_email_analyzer.py   # Email rule unit tests
│   └── test_url_analyzer.py     # URL rule unit tests
├── requirements.txt
├── .env.example
└── README.md
```

---

## 3. Team Responsibilities

### Person 1: Security Rules (`backend/app/security/`)
- Add new detection rules in `rules.py`
- Enhance `URLAnalyzer` in `url_analyzer.py` (e.g., brand typosquatting, new TLDs)
- Enhance `EmailAnalyzer` in `email_analyzer.py` (e.g., SPF/DKIM heuristic flags)
- Add unit tests under `tests/test_url_analyzer.py` and `tests/test_email_analyzer.py`

### Person 2: Gemini Integration (`backend/app/services/gemini_service.py`)
- Tune `SYSTEM_INSTRUCTION` and prompt formats
- Test with real Gemini API keys
- Maintain fallback mock responses in `_generate_mock_analysis`
- Verify JSON schema compliance

### Person 3: Backend / Storage / Aggregation (`backend/app/api/`, `services/`, `database/`)
- Maintain routes in `app/api/routes/`
- SQLite schemas and indexes in `app/database/models.py`
- Repository queries in `app/database/repository.py`
- Aggregation telemetry in `app/services/aggregation_service.py`

---

## 4. Setup & Running Locally

### Prerequisites
- Python 3.11+

### Installation
```bash
# 1. Navigate to backend directory
cd backend

# 2. Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
```

### Run the Server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
- API Documentation: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health Check: [http://localhost:8000/health](http://localhost:8000/health)

---

## 5. Mock Mode vs Live Gemini Mode

### Offline / Mock Mode (Default)
In `.env`:
```env
GEMINI_MOCK_MODE=true
```
When mock mode is enabled (or if `GEMINI_API_KEY` is not provided), the backend generates realistic, context-aware analysis responses without calling the Gemini API.

### Live Gemini Mode
In `.env`:
```env
GEMINI_API_KEY=AIzaSyYourRealKeyHere
GEMINI_MOCK_MODE=false
```
When configured, the backend sends messages directly to Google Gemini and validates responses against the locked Pydantic schema.

---

## 6. Running Tests

```bash
pytest -v tests
```
