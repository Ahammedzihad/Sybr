"""
FastAPI app entrypoint for Conversation Intelligence & Security Analysis.
Provides endpoints for conversation analysis, listing, inspection, and dashboard metrics.
"""

import logging
import os
import sys
import uuid
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List
from fastapi import Body, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

# Ensure backend directory is in sys.path
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

try:
    import storage
    from pipeline import run_pipeline
    from aggregation import frequently_reported_issues
except ImportError:
    from backend import storage
    from backend.pipeline import run_pipeline
    from backend.aggregation import frequently_reported_issues

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Customer Support & Security Intelligence API",
    description="API for conversation intelligence, classification, and phishing threat detection.",
    version="1.0.0",
    docs_url="/docs",
    openapi_url="/openapi.json",
)

# CORS middleware allowing all origins, methods, and headers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Ensure database schema is initialized on application start."""
    storage.init_db()


@app.get(
    "/health",
    summary="Service health check",
    tags=["System"],
)
async def health_check() -> Dict[str, str]:
    """Returns application status and database connectivity for frontend Navbar."""
    return {
        "status": "ok",
        "version": "1.0.0",
        "mock_mode": "mock",
        "database": "connected",
    }


@app.post(
    "/analyze",
    summary="Analyze conversation",
    tags=["Analysis"],
    status_code=status.HTTP_200_OK,
)
async def analyze(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    """
    Analyzes conversation messages through the security and AI pipeline,
    persists the resulting record in SQLite, and returns the ConversationRecord.
    """
    if not isinstance(payload, dict):
        payload = {}

    conversation_id = payload.get("conversation_id")
    if not conversation_id:
        conversation_id = f"CS-{uuid.uuid4().hex[:6].upper()}"

    messages = payload.get("messages")
    if messages is None:
        if "raw_text" in payload:
            messages = [{"text": payload["raw_text"]}]
        elif "message" in payload:
            sender = payload.get("sender", "")
            subject = payload.get("subject", "")
            urls = payload.get("urls", [])
            body_parts = []
            if sender:
                body_parts.append(f"From: {sender}")
            if subject:
                body_parts.append(f"Subject: {subject}")
            body_parts.append(str(payload["message"]))
            if urls and isinstance(urls, list):
                body_parts.append("URLs:\n" + "\n".join(str(u) for u in urls if u))
            messages = [{"sender": sender or "customer", "text": "\n".join(body_parts)}]
        else:
            messages = []
    elif not isinstance(messages, list):
        messages = [messages]

    override_fields = {
        k: v for k, v in payload.items()
        if k in [
            "category",
            "sentiment",
            "priority",
            "risk_level",
            "keywords",
            "emotion",
            "resolution_status",
            "customer_request",
            "summary",
        ]
    }

    record = run_pipeline(conversation_id, messages, **override_fields)
    storage.save(record)
    return record


@app.get(
    "/conversations",
    summary="List conversations",
    tags=["Conversations"],
    response_model=List[Dict[str, Any]],
)
async def get_conversations(
    risk_level: Optional[str] = None,
    category: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Returns stored conversation records with optional risk_level and category filtering."""
    records = storage.get_all()
    if risk_level and risk_level.upper() != "ALL":
        records = [r for r in records if str(r.get("risk_level", "")).lower() == risk_level.lower()]
    if category and category.upper() != "ALL":
        records = [r for r in records if str(r.get("category", "")).lower() == category.lower()]
    return records


@app.get(
    "/conversations/{conversation_id}",
    summary="Get conversation by ID",
    tags=["Conversations"],
)
async def get_conversation(conversation_id: str) -> Dict[str, Any]:
    """Fetches a single conversation record by conversation_id or raises 404."""
    record = storage.get_by_id(conversation_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{conversation_id}' not found",
        )
    return record


@app.get(
    "/dashboard",
    summary="Get dashboard telemetry",
    tags=["Dashboard"],
)
async def get_dashboard() -> Dict[str, Any]:
    """
    Returns aggregated dashboard metrics across all stored conversation records.
    Catches record-level exceptions to ensure resilience against malformed storage entries.
    """
    try:
        records = storage.get_all()
        total_conversations = len(records)

        sentiment_counter: Counter = Counter()
        category_counter: Counter = Counter()
        risk_level_counter: Counter = Counter()
        emotion_counter: Counter = Counter()
        threat_type_counter: Counter = Counter()
        unresolved_count = 0
        resolved_count = 0
        pending_count = 0
        critical_count = 0
        high_risk_count = 0

        for r in records:
            try:
                if not isinstance(r, dict):
                    continue

                # 1. sentiment_split: skip missing values
                sentiment = r.get("sentiment")
                if sentiment is not None and isinstance(sentiment, str) and sentiment.strip():
                    sentiment_counter[sentiment.strip()] += 1

                # 2. category_distribution: skip missing values
                category = r.get("category")
                if category is not None and isinstance(category, str) and category.strip():
                    category_counter[category.strip()] += 1

                # 3. risk_level_distribution: skip missing values
                risk_level = r.get("risk_level")
                if risk_level is not None and isinstance(risk_level, str) and risk_level.strip():
                    risk_level_counter[risk_level.strip()] += 1

                # 4. emotion and threat_type counters
                emotion = r.get("emotion")
                if emotion and isinstance(emotion, str) and emotion.strip():
                    emotion_counter[emotion.strip()] += 1

                threat_type = r.get("threat_type")
                if threat_type and isinstance(threat_type, str) and threat_type.strip():
                    threat_type_counter[threat_type.strip()] += 1

                # 5. resolution status counts
                res_status = str(r.get("resolution_status", "")).strip().lower()
                if res_status == "unresolved":
                    unresolved_count += 1
                elif res_status == "resolved":
                    resolved_count += 1
                elif res_status in ["pending", "flagged", "under review"]:
                    pending_count += 1

                # 6. critical and high risk counts
                priority = str(r.get("priority", "")).strip().lower()
                risk_val = str(risk_level or "").strip().lower()
                if priority == "critical" or risk_val == "critical":
                    critical_count += 1
                if risk_val in ["critical", "high"]:
                    high_risk_count += 1

            except Exception as rec_err:
                logger.warning(f"Error parsing conversation record in dashboard: {rec_err}")
                continue

        # 7. most_common_complaint: top category from category_distribution, or "N/A" if empty
        if category_counter:
            valid_cats = [cat for cat, _ in category_counter.most_common() if cat.lower() != "unknown"]
            most_common_complaint = valid_cats[0] if valid_cats else category_counter.most_common(1)[0][0]
        else:
            most_common_complaint = "N/A"

        # 8. frequently_reported_issues & most_frequent_issue
        freq_issues = frequently_reported_issues()
        top_keywords = freq_issues.get("by_keyword", [])
        most_frequent_issue = top_keywords[0][0] if top_keywords else "N/A"

        # 9. total_complaints: sum of complaint categories (excluding unknown if other categories exist)
        complaints_sum = sum(cnt for cat, cnt in category_counter.items() if cat.lower() != "unknown")
        total_complaints = complaints_sum if complaints_sum > 0 else sum(category_counter.values())

        return {
            "total_conversations": total_conversations,
            "total_complaints": total_complaints,
            "sentiment_split": dict(sentiment_counter),
            "category_distribution": dict(category_counter),
            "risk_level_distribution": dict(risk_level_counter),
            "unresolved_count": unresolved_count,
            "critical_count": critical_count,
            "most_common_complaint": most_common_complaint,
            "most_frequent_issue": most_frequent_issue,
            "frequently_reported_issues": freq_issues,
            # Frontend UI alignment fields
            "high_risk_count": high_risk_count,
            "resolved_count": resolved_count,
            "pending_count": pending_count,
            "categories": dict(category_counter),
            "sentiments": dict(sentiment_counter),
            "emotions": dict(emotion_counter),
            "risk_levels": dict(risk_level_counter),
            "threat_types": dict(threat_type_counter),
        }

    except Exception as err:
        logger.error(f"Error processing dashboard telemetry: {err}", exc_info=True)
        return {
            "total_conversations": 0,
            "total_complaints": 0,
            "sentiment_split": {},
            "category_distribution": {},
            "risk_level_distribution": {},
            "unresolved_count": 0,
            "critical_count": 0,
            "most_common_complaint": "N/A",
            "most_frequent_issue": "N/A",
            "frequently_reported_issues": {"by_category": [], "by_keyword": []},
            "error": str(err),
        }


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
