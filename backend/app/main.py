"""
Main FastAPI Application Entry Point.
Provides CORS, health checks, ingestion, live analyzer, and conversation APIs.
"""
import json
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, BackgroundTasks, UploadFile, File, Query, HTTPException, status, Depends
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
    IssueDiagnosisAndHelp,
    CopilotDiagnoseRequest,
    UserProfile,
    AuthLoginRequest,
    AuthLoginResponse,
    AuthSignupRequest,
    AuthResetPasswordRequest,
    UserRoleUpdateRequest,
    AuditLogEntry,
    CustomerDashboardKPIs,
    AdminDashboardKPIs,
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
from app.copilot import diagnose_multimodal_issue, get_recent_copilot_diagnoses
from app.auth import (
    get_current_user,
    authenticate_user,
    register_user,
    request_password_reset,
    require_authenticated_user,
    require_admin,
    require_customer,
)
from app.db import (
    upsert_conversation,
    get_conversation,
    list_conversations,
    delete_conversation,
    is_supabase_enabled,
    get_supabase_client,
    get_all_conversations,
    list_profiles,
    update_profile_role,
    list_audit_logs,
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
    db_available = is_supabase_enabled()

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
# Section 11 & Phase 4: Authentication Endpoints
# ---------------------------------------------------------------------------

@app.post("/auth/login", response_model=AuthLoginResponse, tags=["Authentication"])
async def login(req: AuthLoginRequest):
    """
    Authenticates via Supabase Auth or falls back to clearly-marked Demo Mode.
    """
    return authenticate_user(req)


@app.get("/auth/me", response_model=UserProfile, tags=["Authentication"])
async def get_my_profile(current_user: UserProfile = Depends(get_current_user)):
    """
    Returns the currently authenticated user's profile.
    """
    return current_user


@app.post("/auth/logout", tags=["Authentication"])
async def logout(current_user: UserProfile = Depends(get_current_user)):
    """
    Logs out the current user and invalidates session state.
    """
    return {"status": "ok", "message": "Successfully logged out."}


@app.post("/auth/signup", tags=["Authentication"])
async def signup(req: AuthSignupRequest):
    """
    Registers a new user (Gated behind ENABLE_SIGNUP flag, defaults to False in prototype).
    PUBLIC SIGNUP ALWAYS CREATES ROLE 'CUSTOMER'.
    """
    if not settings.ENABLE_SIGNUP:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Public registration is currently disabled for this prototype.",
        )
    return register_user(req)


@app.post("/auth/reset-password", tags=["Authentication"])
async def reset_password(req: AuthResetPasswordRequest):
    """
    Requests a password reset (Gated behind ENABLE_PASSWORD_RESET flag, defaults to False in prototype).
    """
    if not settings.ENABLE_PASSWORD_RESET:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Password reset is currently disabled.",
        )
    return request_password_reset(req)


# ---------------------------------------------------------------------------
# Section 15 & 16: Customer Portal Endpoints
# ---------------------------------------------------------------------------

@app.get("/customer/dashboard", response_model=CustomerDashboardKPIs, tags=["Customer Portal"])
async def customer_get_dashboard(current_user: UserProfile = Depends(require_customer)):
    """
    Customer-scoped dashboard metrics.
    Only returns metrics and recent activity for the authenticated customer.
    """
    my_convs = get_all_conversations(user_id=current_user.id)
    total_my = len(my_convs)
    my_threats = sum(1 for c in my_convs if c.security.threat_detected)
    my_pending = sum(1 for c in my_convs if c.resolution_status == "Pending")
    my_resolved = sum(1 for c in my_convs if c.resolution_status == "Resolved")

    recent_activity = [
        {
            "id": c.conversation_id,
            "created_at": c.created_at,
            "issue": c.customer_issue or c.raw_text_masked[:60],
            "category": c.category,
            "priority": c.priority,
            "risk_level": c.security.risk_level,
            "threat_detected": c.security.threat_detected,
        }
        for c in my_convs[:10]
    ]

    return CustomerDashboardKPIs(
        total_my_conversations=total_my,
        my_threats_detected=my_threats,
        my_pending_reviews=my_pending,
        my_resolved_tickets=my_resolved,
        recent_activity=recent_activity,
    )


# ---------------------------------------------------------------------------
# Section 21-27: Admin Portal Endpoints (Role Protected)
# ---------------------------------------------------------------------------

@app.get("/admin/dashboard", response_model=AdminDashboardKPIs, tags=["Admin Portal"])
async def admin_get_dashboard(current_admin: UserProfile = Depends(require_admin)):
    """
    Platform-level overview metrics for the Admin Dashboard.
    Strictly protected by require_admin.
    """
    profiles = list_profiles()
    total_users = len(profiles)
    total_customers = len([p for p in profiles if p.get("role") == "customer"])
    total_admins = len([p for p in profiles if p.get("role") == "admin"])

    all_convs = get_all_conversations(user_id=None)
    total_platform_convs = len(all_convs)
    total_platform_threats = sum(1 for c in all_convs if c.security.threat_detected)
    high_risk_threats = sum(1 for c in all_convs if c.security.risk_level in ("High", "Critical"))

    raw_logs = list_audit_logs(limit=10)
    audit_entries = [
        AuditLogEntry(
            id=l["id"],
            actor_user_id=l["actor_user_id"],
            actor_email=l.get("actor_email", ""),
            action=l["action"],
            target_resource_id=l.get("target_resource_id", ""),
            metadata=l.get("metadata", {}),
            created_at=l["created_at"],
        )
        for l in raw_logs
    ]

    return AdminDashboardKPIs(
        total_users=total_users,
        total_customers=total_customers,
        total_admins=total_admins,
        total_platform_conversations=total_platform_convs,
        total_platform_threats=total_platform_threats,
        high_risk_threats=high_risk_threats,
        ai_status={
            "provider": "Google Gemini",
            "model": settings.GEMINI_MODEL,
            "fallback": "Rule-Based Deterministic Engine",
            "status": "online" if settings.GEMINI_API_KEY else "fallback_mode",
        },
        database_status={
            "mode": "supabase_postgresql" if is_supabase_enabled() else "local_sqlite",
            "rls_enforced": True,
        },
        recent_audit_logs=audit_entries,
    )


@app.get("/admin/users", tags=["Admin Portal"])
async def admin_list_users(current_admin: UserProfile = Depends(require_admin)):
    """Lists all user profiles for administration."""
    return list_profiles()


@app.patch("/admin/users/{user_id}/role", tags=["Admin Portal"])
async def admin_change_user_role(
    user_id: str,
    req: UserRoleUpdateRequest,
    current_admin: UserProfile = Depends(require_admin),
):
    """
    Updates the role of a user profile.
    Guards against removing the final administrator (Section 24 & 77).
    """
    try:
        updated = update_profile_role(target_id=user_id, new_role=req.role, actor_id=current_admin.id)
        return updated
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@app.get("/admin/audit-logs", tags=["Admin Portal"])
async def admin_get_audit_logs(
    limit: int = Query(50, ge=1, le=200),
    current_admin: UserProfile = Depends(require_admin),
):
    """Chronological security audit trail for administration."""
    return list_audit_logs(limit=limit)


@app.get("/admin/conversations", tags=["Admin Portal"])
async def admin_get_all_conversations(
    category: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    risk: Optional[str] = Query(None),
    sentiment: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_admin: UserProfile = Depends(require_admin),
):
    """System-wide conversation oversight across all customers for administrators."""
    items, total = list_conversations(
        category=category,
        priority=priority,
        risk=risk,
        sentiment=sentiment,
        status=status,
        q=q,
        page=page,
        limit=limit,
        user_id=None,  # Global oversight across all users
    )
    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit,
    }



# ---------------------------------------------------------------------------
# Live Analyzer Endpoint (Section 10)
# ---------------------------------------------------------------------------

@app.post("/analyze", response_model=ConversationRecord, tags=["Analysis"])
async def analyze_live(req: AnalyzeRequest, current_user: UserProfile = Depends(get_current_user)):
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

    if not req.user_id:
        req.user_id = current_user.id

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
    current_user: UserProfile = Depends(get_current_user),
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

    # Associate conversations with current user
    for conv in conversations:
        conv["user_id"] = current_user.id

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
    current_user: UserProfile = Depends(get_current_user),
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
        user_id=current_user.id,
    )
    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit,
    }


@app.get("/conversations/{conv_id}", response_model=ConversationRecord, tags=["Conversations"])
async def get_conversation_by_id(conv_id: str, current_user: UserProfile = Depends(get_current_user)):
    """Retrieves full conversation details with role-aware data isolation."""
    effective_uid = None if current_user.role == "admin" else current_user.id
    record = get_conversation(conv_id, user_id=effective_uid)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{conv_id}' not found.",
        )
    return record


@app.post("/conversations/{conv_id}/reanalyze", response_model=ConversationRecord, tags=["Conversations"])
async def reanalyze_conversation(conv_id: str, current_user: UserProfile = Depends(get_current_user)):
    """Re-runs the analysis pipeline on an existing conversation record."""
    effective_uid = None if current_user.role == "admin" else current_user.id
    existing = get_conversation(conv_id, user_id=effective_uid)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{conv_id}' not found.",
        )

    conv_dict = {
        "conversation_id": existing.conversation_id,
        "user_id": current_user.id,
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
async def delete_conversation_by_id(conv_id: str, current_user: UserProfile = Depends(get_current_user)):
    """Privacy endpoint (Section 13): Deletes a conversation record."""
    effective_uid = None if current_user.role == "admin" else current_user.id
    deleted = delete_conversation(conv_id, user_id=effective_uid)
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
async def get_dashboard(current_user: UserProfile = Depends(get_current_user)):
    """
    F10 / GET /dashboard: Returns global KPI counters, sentiment split,
    category distribution, risk levels, and daily trend for the UI dashboard.
    """
    return compute_dashboard_data(user_id=current_user.id)


@app.get("/issues", response_model=IssueFrequencyResponse, tags=["Analytics"])
async def get_ranked_issues(days: Optional[int] = Query(None, ge=1), current_user: UserProfile = Depends(get_current_user)):
    """
    F5 / GET /issues: Returns ranked table of Frequently Reported Issues.
    """
    return compute_ranked_issues(days=days, user_id=current_user.id)


@app.get("/trends", tags=["Analytics"])
async def get_trends(bucket: str = Query("day", pattern="^(day|week|month)$"), current_user: UserProfile = Depends(get_current_user)):
    """
    E5 / GET /trends: Returns time-series complaint and threat trends.
    """
    return compute_trends(bucket=bucket, user_id=current_user.id)


@app.get("/eval", response_model=EvaluationMetrics, tags=["System Health"])
async def get_system_eval():
    """
    E8 / GET /eval: Evaluates system precision, recall, and false positive rate
    on the ground-truth benchmark test set (data/labeled_eval.json).
    """
    return run_system_evaluation()


# ---------------------------------------------------------------------------
# Multimodal AI Copilot Endpoints (Section 10)
# ---------------------------------------------------------------------------

@app.post("/copilot/diagnose", response_model=IssueDiagnosisAndHelp, tags=["Copilot"])
async def copilot_diagnose(req: CopilotDiagnoseRequest, current_user: UserProfile = Depends(get_current_user)):
    """
    Multimodal AI Copilot diagnosis endpoint.
    Accepts customer problem message and/or base64 screenshot.
    """
    has_msg = bool(req.message and req.message.strip())
    has_img = bool(req.image_data and req.image_data.strip())
    if not has_msg and not has_img:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either 'message' or 'image_data' must be provided",
        )
    return diagnose_multimodal_issue(
        message=req.message,
        image_data=req.image_data,
        image_name=req.image_name,
        channel=req.channel,
        user_id=current_user.id,
    )


@app.get("/copilot/history", response_model=List[IssueDiagnosisAndHelp], tags=["Copilot"])
async def copilot_history(limit: int = Query(20, ge=1, le=100), current_user: UserProfile = Depends(get_current_user)):
    """Returns recent diagnostic sessions with user scoping."""
    effective_uid = None if current_user.role == "admin" else current_user.id
    return get_recent_copilot_diagnoses(limit=limit, user_id=effective_uid)



# ---------------------------------------------------------------------------
# Section 12 & Phase 7: Gmail Integration Endpoints
# ---------------------------------------------------------------------------

from app.gmail import (
    get_gmail_connection_status,
    get_gmail_auth_url,
    disconnect_gmail_user,
    sync_gmail_inbox,
)

@app.get("/gmail/status", tags=["Gmail"])
async def gmail_status(current_user: UserProfile = Depends(get_current_user)):
    """Returns whether Gmail integration is configured and if current user is connected."""
    return get_gmail_connection_status(user_id=current_user.id)


@app.get("/gmail/auth-url", tags=["Gmail"])
async def gmail_auth_url(current_user: UserProfile = Depends(get_current_user)):
    """Generates the Google OAuth 2.0 consent URL for the user."""
    return get_gmail_auth_url(user_id=current_user.id)


@app.post("/gmail/disconnect", tags=["Gmail"])
async def gmail_disconnect(current_user: UserProfile = Depends(get_current_user)):
    """Disconnects the user's Gmail account and clears stored tokens."""
    disconnected = disconnect_gmail_user(user_id=current_user.id)
    return {"status": "ok", "disconnected": disconnected, "message": "Gmail account disconnected."}


@app.post("/gmail/sync", tags=["Gmail"])
async def gmail_sync(limit: int = Query(10, ge=1, le=50), current_user: UserProfile = Depends(get_current_user)):
    """Syncs recent messages from the connected Gmail inbox."""
    return sync_gmail_inbox(user_id=current_user.id, limit=limit)


