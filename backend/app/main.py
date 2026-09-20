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
    AdminReviewCorrectionRequest,
    AdminStatusUpdateRequest,
    AdminInternalNoteRequest,
    AdminDraftResponseRequest,
    AdminDraftResponseResponse,
    AdminCategoryAnalyticsResponse,
    AdminSecurityAnalyticsResponse,
    AdminAIPerformanceResponse,
    CustomerOverviewItem,
    CustomerHistoryResponse,
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
    get_profile,
    update_profile_role,
    list_audit_logs,
    update_conversation_review,
    update_conversation_status,
    add_conversation_internal_note,
    set_conversation_needs_review,
    get_admin_category_analytics,
    get_admin_security_analytics,
    get_admin_ai_performance,
    list_customer_overviews,
    get_conversations_by_user,
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
            detail="Password reset is currently disabled for this prototype.",
        )
    return request_password_reset(req)


@app.get("/auth/config", tags=["Authentication"])
async def auth_config():
    """
    Returns public Supabase configuration for client-side SDK bootstrap.
    Never returns service role keys or sensitive credentials.
    """
    return {
        "supabase_url": settings.SUPABASE_URL,
        "supabase_anon_key": settings.SUPABASE_ANON_KEY,
    }


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
    Platform-level overview metrics for the Admin Dashboard (Section 9 & 21).
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
    needs_review_count = sum(1 for c in all_convs if c.needs_human_review)
    unresolved_count = sum(1 for c in all_convs if c.resolution_status in ("Unresolved", "Pending"))

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

    needs_attention = [
        {
            "id": c.conversation_id,
            "created_at": c.created_at,
            "issue": c.customer_issue or (c.raw_text_masked[:60] if c.raw_text_masked else ""),
            "category": c.category,
            "priority": c.priority,
            "risk_level": c.security.risk_level,
            "threat_detected": c.security.threat_detected,
            "needs_human_review": c.needs_human_review,
            "processing_status": c.processing_status,
            "resolution_status": c.resolution_status,
            "user_id": c.user_id,
        }
        for c in all_convs
        if c.priority == "Critical" or c.security.risk_level in ("Critical", "High") or c.needs_human_review or c.is_angry
    ][:10]

    return AdminDashboardKPIs(
        total_users=total_users,
        total_customers=total_customers,
        total_admins=total_admins,
        total_platform_conversations=total_platform_convs,
        total_platform_threats=total_platform_threats,
        high_risk_threats=high_risk_threats,
        needs_review_count=needs_review_count,
        unresolved_count=unresolved_count,
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
        needs_attention=needs_attention,
    )


# ---------------------------------------------------------------------------
# Section 13, 14, 15: Admin Operational Review & Workflow Endpoints
# ---------------------------------------------------------------------------

@app.patch("/admin/conversations/{conv_id}/review", response_model=ConversationRecord, tags=["Admin Portal"])
async def admin_review_conversation(
    conv_id: str,
    req: AdminReviewCorrectionRequest,
    current_admin: UserProfile = Depends(require_admin),
):
    """
    Submits human review corrections for category, issue label, priority, risk level, or resolution.
    Preserves original AI analysis and logs security audit trail (Section 13 & 15).
    """
    overrides = req.model_dump(exclude_unset=True)
    reason = overrides.pop("reason", "Manual administrative review & calibration")
    updated = update_conversation_review(
        conv_id=conv_id,
        reviewer_id=current_admin.id,
        reviewer_email=current_admin.email,
        overrides=overrides,
        reason=reason,
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{conv_id}' not found.",
        )
    return updated


@app.patch("/admin/conversations/{conv_id}/status", response_model=ConversationRecord, tags=["Admin Portal"])
async def admin_update_conversation_status(
    conv_id: str,
    req: AdminStatusUpdateRequest,
    current_admin: UserProfile = Depends(require_admin),
):
    """
    Updates operational workflow status, resolution status, or assignment for a conversation (Section 15).
    """
    updated = update_conversation_status(
        conv_id=conv_id,
        actor_id=current_admin.id,
        actor_email=current_admin.email,
        processing_status=req.processing_status,
        resolution_status=req.resolution_status,
        assigned_to=req.assigned_to,
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{conv_id}' not found.",
        )
    return updated


@app.post("/admin/conversations/{conv_id}/notes", tags=["Admin Portal"])
async def admin_add_internal_note(
    conv_id: str,
    req: AdminInternalNoteRequest,
    current_admin: UserProfile = Depends(require_admin),
):
    """
    Appends an internal admin note to a conversation dossier (Section 14 & 15).
    Private to administrative staff; strictly hidden from customers.
    """
    note = add_conversation_internal_note(
        conv_id=conv_id,
        author_id=current_admin.id,
        author_name=current_admin.display_name or current_admin.email.split("@")[0],
        note_text=req.text,
        author_email=current_admin.email,
    )
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{conv_id}' not found.",
        )
    return note


@app.post("/admin/conversations/{conv_id}/request-review", response_model=ConversationRecord, tags=["Admin Portal"])
async def admin_request_conversation_review(
    conv_id: str,
    reason: str = Query("Flagged for administrative review", min_length=1),
    current_admin: UserProfile = Depends(require_admin),
):
    """Flags a conversation for the human review triage queue (Section 13)."""
    updated = set_conversation_needs_review(
        conv_id=conv_id,
        actor_id=current_admin.id,
        actor_email=current_admin.email,
        reason=reason,
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{conv_id}' not found.",
        )
    return updated


@app.post("/admin/conversations/{conv_id}/draft-response", response_model=AdminDraftResponseResponse, tags=["Admin Portal"])
async def admin_generate_draft_response(
    conv_id: str,
    req: AdminDraftResponseRequest,
    current_admin: UserProfile = Depends(require_admin),
):
    """
    Synthesizes an advisory customer support response draft grounded in the conversation's
    extracted issues and security findings.
    """
    record = get_conversation(conv_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{conv_id}' not found.",
        )

    if record.security.threat_detected:
        draft = (
            f"Dear Customer,\n\n"
            f"Our security monitoring system flagged a potential security anomaly regarding: '{record.customer_issue or 'your recent communication'}'.\n"
            f"For your account protection, please DO NOT click any external links, download attachments, or share one-time passwords (OTP).\n\n"
            f"Our security engineering team is actively reviewing your case. If you have questions, please reach out through our verified in-app help desk."
        )
        rec_action = record.security.recommended_action or "Escalate immediately to SecOps; quarantine ticket."
        rationale = f"Active threat type '{record.security.threat_type}' with risk level '{record.security.risk_level}'."
    else:
        category = record.category or "Support"
        draft = (
            f"Hi there,\n\n"
            f"Thank you for contacting Sybr Support regarding {record.customer_issue or 'your inquiry'}.\n"
            f"We understand the urgency and our team is actively handling your {category} ticket.\n\n"
            f"Status: {record.resolution_status}. We will update you as soon as this is fully resolved."
        )
        rec_action = f"Standard support workflow for {category} ({record.issue_label}). Priority: {record.priority}."
        rationale = f"Routine customer service inquiry categorized under {category} with {record.urgency} urgency."

    return AdminDraftResponseResponse(
        draft_response=draft,
        recommended_action=rec_action,
        rationale=rationale,
    )


# ---------------------------------------------------------------------------
# Section 16 & 17: Admin Intelligence Analytics & Observability Endpoints
# ---------------------------------------------------------------------------

@app.get("/admin/analytics/categories", response_model=AdminCategoryAnalyticsResponse, tags=["Admin Portal"])
async def admin_category_analytics(current_admin: UserProfile = Depends(require_admin)):
    """Provides category frequency and resolution analytics across all platform conversations (Section 16)."""
    return get_admin_category_analytics()


@app.get("/admin/analytics/security", response_model=AdminSecurityAnalyticsResponse, tags=["Admin Portal"])
async def admin_security_analytics(current_admin: UserProfile = Depends(require_admin)):
    """Provides threat intelligence distribution, detected techniques, and top indicators (Section 17)."""
    return get_admin_security_analytics()


@app.get("/admin/analytics/ai", response_model=AdminAIPerformanceResponse, tags=["Admin Portal"])
async def admin_ai_performance(current_admin: UserProfile = Depends(require_admin)):
    """Provides AI observability: Gemini vs fallback rates, latency, and human correction metrics (Section 17)."""
    return get_admin_ai_performance()


@app.get("/admin/customers", response_model=List[CustomerOverviewItem], tags=["Admin Portal"])
async def admin_list_customers(current_admin: UserProfile = Depends(require_admin)):
    """Lists customer accounts with aggregate ticket and threat metrics (Section 8)."""
    return list_customer_overviews()


@app.get("/admin/customers/{customer_id}", response_model=CustomerHistoryResponse, tags=["Admin Portal"])
async def admin_get_customer_history(customer_id: str, current_admin: UserProfile = Depends(require_admin)):
    """Retrieves full conversation history and profile for a specific customer (Section 8)."""
    profile = get_profile(customer_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer '{customer_id}' not found.",
        )
    convs = get_conversations_by_user(customer_id)
    return CustomerHistoryResponse(
        customer_id=customer_id,
        email=profile.get("email", ""),
        display_name=profile.get("display_name") or profile.get("email", "").split("@")[0],
        total_conversations=len(convs),
        conversations=convs,
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
        user_id=current_user.id if current_user.role != "admin" else None,
    )
    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit,
    }


@app.get("/conversations/{conv_id}", response_model=ConversationRecord, tags=["Conversations"])
async def get_conversation_by_id(conv_id: str, current_user: UserProfile = Depends(get_current_user)):
    """Retrieves full conversation details with role-aware data isolation (Section 14 & 22)."""
    effective_uid = None if current_user.role == "admin" else current_user.id
    record = get_conversation(conv_id, user_id=effective_uid)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{conv_id}' not found.",
        )
    # Strict customer privacy isolation:
    # Internal notes, reviewer identities, and administrative deliberations are NEVER exposed to customers
    if current_user.role != "admin":
        record.internal_notes = []
        record.human_overrides = None
        record.reviewed_by = None
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


