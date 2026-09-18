"""
Main FastAPI Application Entry Point.
Provides CORS, health checks, ingestion, live analyzer, and conversation APIs.
"""
import json
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, BackgroundTasks, UploadFile, File, Query, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.schemas import (
    HealthResponse,
    AnalyzeRequest,
    ConversationRecord,
    JobProgressResponse,
    DashboardResponse,
    IssueFrequencyResponse,
    EvaluationMetrics,
)
from app.aggregates import (
    compute_dashboard_data,
    compute_ranked_issues,
    compute_trends,
    run_system_evaluation,
)
from app.ingest import (
    parse_csv_content,
    parse_json_content,
    normalize_analyze_request,
)
from app.pipeline import process_conversation
from app.jobs import create_job, update_job_progress, get_job_status
from app.db import (
    upsert_conversation,
    get_conversation,
    list_conversations,
    delete_conversation,
)

app = FastAPI(
    title="Customer Support Intelligence & Phishing Detection API",
    description="Dual-layered AI & Security analysis for customer support interactions.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS for local development and deployed frontend (Vercel)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS or ["*"],
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$|https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Returns system health, active AI mode, model name, and database status."""
    ai_available = bool(settings.GEMINI_API_KEY)
    db_available = bool(settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY)

    return HealthResponse(
        status="ok",
        ai_mode="gemini" if ai_available else "fallback",
        model=settings.GEMINI_MODEL,
        database="supabase" if db_available else "local_sqlite",
        version="1.0.0",
    )


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "AI-Powered Customer Support Intelligence & Phishing Threat Detection System API is running.",
        "docs": "/docs",
        "health": "/health",
    }


# ---------------------------------------------------------------------------
# Live Analyzer Endpoint (Section 10)
# ---------------------------------------------------------------------------

@app.post("/analyze", response_model=ConversationRecord, tags=["Analysis"])
async def analyze_live(req: AnalyzeRequest):
    """
    F10 / E6: Live Analyzer endpoint.
    Accepts single text or message thread, plus optional explicit URLs, emails, attachments.
    Returns complete combined record matching Section 5 data contract.
    """
    if not req.text and not req.messages:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either 'text' or 'messages' must be provided for analysis.",
        )

    norm_conv = normalize_analyze_request(req)
    record = process_conversation(norm_conv, persist=True)
    return record


# ---------------------------------------------------------------------------
# Batch Upload & Ingestion Endpoints (F1, Section 10)
# ---------------------------------------------------------------------------

def run_batch_ingest_job(job_id: str, conversations: List[Dict[str, Any]]):
    """Background task worker processing conversations sequentially."""
    for conv in conversations:
        try:
            process_conversation(conv, persist=True)
            update_job_progress(job_id, processed_inc=1, error=False)
        except Exception:
            update_job_progress(job_id, processed_inc=1, error=True)


@app.post("/upload", tags=["Ingestion"])
async def upload_dataset(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    """
    F1: Accepts CSV or JSON file upload.
    Maps columns, groups conversations, starts background analysis job, and returns job ID.
    """
    contents = await file.read()
    filename = (file.filename or "").lower()

    try:
        if filename.endswith(".json"):
            json_data = json.loads(contents.decode("utf-8", errors="ignore"))
            conversations = parse_json_content(json_data)
        elif filename.endswith(".csv") or b"," in contents[:1000]:
            csv_str = contents.decode("utf-8", errors="ignore")
            conversations = parse_csv_content(csv_str)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported file format. Please upload a CSV or JSON file.",
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error parsing file: {str(e)}",
        )

    if not conversations:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid conversations or messages found in the uploaded file.",
        )

    job_id = create_job(total=len(conversations))
    background_tasks.add_task(run_batch_ingest_job, job_id, conversations)

    return {
        "job_id": job_id,
        "status": "processing",
        "total": len(conversations),
        "message": f"Dataset uploaded. Processing {len(conversations)} conversations in background.",
    }


@app.get("/jobs/{job_id}", response_model=JobProgressResponse, tags=["Ingestion"])
async def get_job_progress(job_id: str):
    """Returns processing status and progress for an upload job."""
    job = get_job_status(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{job_id}' not found.",
        )
    return job


# ---------------------------------------------------------------------------
# Conversations Inbox & Drill-Down (Section 10)
# ---------------------------------------------------------------------------

@app.get("/conversations", tags=["Conversations"])
async def get_conversations(
    category: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    risk: Optional[str] = Query(None),
    sentiment: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    """
    Paginated and filterable list of analyzed conversations.
    Supports searching text and filtering by category, priority, risk, sentiment, status.
    """
    items, total = list_conversations(
        category=category,
        priority=priority,
        risk=risk,
        sentiment=sentiment,
        status=status,
        q=q,
        page=page,
        limit=limit,
    )
    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit,
    }


@app.get("/conversations/{conv_id}", response_model=ConversationRecord, tags=["Conversations"])
async def get_conversation_by_id(conv_id: str):
    """Retrieves full conversation details including messages and security breakdown."""
    record = get_conversation(conv_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{conv_id}' not found.",
        )
    return record


@app.post("/conversations/{conv_id}/reanalyze", response_model=ConversationRecord, tags=["Conversations"])
async def reanalyze_conversation(conv_id: str):
    """Re-runs the analysis pipeline on an existing conversation record."""
    existing = get_conversation(conv_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{conv_id}' not found.",
        )

    conv_dict = {
        "conversation_id": existing.conversation_id,
        "channel": existing.channel,
        "created_at": existing.created_at,
        "source": existing.source,
        "messages": existing.messages or [],
        "urls": [u.url for u in existing.security.urls],
        "emails": [(e.display_name, e.address) for e in existing.security.emails],
        "attachments": [a.filename for a in existing.security.attachments],
    }
    updated = process_conversation(conv_dict, persist=True)
    return updated


@app.delete("/conversations/{conv_id}", tags=["Conversations"])
async def delete_conversation_by_id(conv_id: str):
    """Privacy endpoint (Section 13): Deletes a conversation record."""
    deleted = delete_conversation(conv_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{conv_id}' not found.",
        )
    return {"status": "deleted", "id": conv_id}


# ---------------------------------------------------------------------------
# Analytics, KPIs, Trends & Health Endpoints (F5, E2, E5, E8)
# ---------------------------------------------------------------------------

@app.get("/dashboard", response_model=DashboardResponse, tags=["Analytics"])
async def get_dashboard():
    """
    F10 / GET /dashboard: Returns global KPI counters, sentiment split,
    category distribution, risk levels, and daily trend for the UI dashboard.
    """
    return compute_dashboard_data()


@app.get("/issues", response_model=IssueFrequencyResponse, tags=["Analytics"])
async def get_ranked_issues(days: Optional[int] = Query(None, ge=1)):
    """
    F5 / GET /issues: Returns ranked table of Frequently Reported Issues.
    """
    return compute_ranked_issues(days=days)


@app.get("/trends", tags=["Analytics"])
async def get_trends(bucket: str = Query("day", pattern="^(day|week|month)$")):
    """
    E5 / GET /trends: Returns time-series complaint and threat trends.
    """
    return compute_trends(bucket=bucket)


@app.get("/eval", response_model=EvaluationMetrics, tags=["System Health"])
async def get_system_eval():
    """
    E8 / GET /eval: Evaluates system precision, recall, and false positive rate
    on the ground-truth benchmark test set (data/labeled_eval.json).
    """
    return run_system_evaluation()
