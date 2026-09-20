"""
Pydantic schemas locking the Section 5 data contract and API input/output models.
NEVER rename fields in ConversationRecord, SummaryDetail, or SecurityDetail.
"""
from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone


# ---------------------------------------------------------------------------
# Message & Ingestion Input Models
# ---------------------------------------------------------------------------

class Message(BaseModel):
    sender: str = Field(default="customer", description="Role or name: customer, agent, support, etc.")
    text: str = Field(description="Message body text")
    timestamp: Optional[str] = Field(default=None, description="ISO timestamp or original string")


class AnalyzeRequest(BaseModel):
    """Input payload for POST /analyze (single text or multi-turn thread)."""
    text: Optional[str] = Field(default=None, description="Single text or complaint snippet")
    messages: Optional[List[Message]] = Field(default=None, description="Structured message thread")
    channel: Optional[str] = Field(default="chat", description="Channel: email|chat|ticket|social|form|sms|voice")
    urls: Optional[List[str]] = Field(default=None, description="Explicit URLs if available")
    emails: Optional[List[str]] = Field(default=None, description="Explicit emails if available")
    attachments: Optional[List[str]] = Field(default=None, description="Attachment filenames")
    source: Optional[str] = Field(default="real", description="Data source: real | synthetic")
    user_id: Optional[str] = Field(default=None, description="Owner user ID for multi-tenant isolation")


# ---------------------------------------------------------------------------
# Section 5: Security Nested Models
# ---------------------------------------------------------------------------

class UrlFinding(BaseModel):
    url: str = ""
    domain: str = ""
    subdomain: str = ""
    https: bool = False
    ip_literal: bool = False
    shortener: bool = False
    length: int = 0
    lookalike_of: str = ""
    risk: Literal["Low", "Medium", "High"] = "Low"
    reasons: List[str] = Field(default_factory=list)


class EmailFinding(BaseModel):
    address: str = ""
    display_name: str = ""
    domain: str = ""
    free_mail: bool = False
    lookalike_of: str = ""
    domain_mismatch: bool = False
    risk: Literal["Low", "Medium", "High"] = "Low"
    reasons: List[str] = Field(default_factory=list)


class AttachmentFinding(BaseModel):
    filename: str = ""
    extension: str = ""
    risk: Literal["Low", "Medium", "High"] = "Low"
    reasons: List[str] = Field(default_factory=list)


class SummaryDetail(BaseModel):
    issue: str = ""
    customer_request: str = ""
    actions_taken: str = ""
    current_status: str = ""
    priority: str = ""


class SecurityDetail(BaseModel):
    threat_detected: bool = False
    threat_type: Literal[
        "Phishing", "Social Engineering", "Impersonation", "Malware Attachment", "None"
    ] = "None"
    social_engineering: Literal["Yes", "Possible", "No"] = "No"
    techniques: List[str] = Field(default_factory=list)
    suspicious_url: bool = False
    suspicious_domain: bool = False
    suspicious_email: bool = False
    suspicious_attachment: bool = False
    credential_request: bool = False
    otp_request: bool = False
    urls: List[UrlFinding] = Field(default_factory=list)
    emails: List[EmailFinding] = Field(default_factory=list)
    attachments: List[AttachmentFinding] = Field(default_factory=list)
    rule_score: int = 0
    risk_level: Literal["Low", "Medium", "High", "Critical"] = "Low"
    risk_reasons: List[str] = Field(default_factory=list)
    recommended_action: str = ""


# ---------------------------------------------------------------------------
# Section 5: Locked Combined Record Contract
# ---------------------------------------------------------------------------

class ConversationRecord(BaseModel):
    """The master record for every analyzed customer support conversation."""
    conversation_id: str
    channel: str = "chat"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    customer_issue: str = ""
    category: str = "Other"
    issue_label: str = "Other"
    keywords: List[str] = Field(default_factory=list)
    sentiment: Literal["Positive", "Neutral", "Negative"] = "Neutral"
    emotion: Literal[
        "Anger", "Frustration", "Satisfaction", "Confusion", "Urgency", "Disappointment", "Fear", "Neutral"
    ] = "Neutral"
    emotion_intensity: int = Field(default=1, ge=1, le=5)
    is_angry: bool = False
    urgency: Literal["Low", "Medium", "High"] = "Low"
    priority: Literal["Low", "Medium", "High", "Critical"] = "Low"
    priority_reason: str = ""
    resolution_status: Literal["Resolved", "Unresolved", "Pending"] = "Pending"
    resolution_reason: str = ""
    summary: SummaryDetail = Field(default_factory=SummaryDetail)
    security: SecurityDetail = Field(default_factory=SecurityDetail)
    ai_mode: Literal["gemini", "fallback"] = "gemini"
    model: Optional[str] = None
    processing_ms: int = 0

    # Optional metadata for persistence/display
    source: Optional[str] = "real"
    raw_text_masked: Optional[str] = None
    original_text: Optional[str] = None
    messages: Optional[List[Message]] = None
    user_id: Optional[str] = None

    # Operational lifecycle & workflow (Admin Intelligence Portal)
    processing_status: str = "AI Analyzed"
    assigned_to: Optional[str] = None
    assigned_at: Optional[str] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[str] = None
    escalated_at: Optional[str] = None
    resolved_at: Optional[str] = None

    # AI Confidence, Explainability & Signals
    confidence: Dict[str, Any] = Field(default_factory=dict)
    ai_explanation: Dict[str, Any] = Field(default_factory=dict)
    needs_human_review: bool = False
    review_reason: Optional[str] = None

    # Human Review & Manual Correction Tracking
    is_human_reviewed: bool = False
    human_overrides: Optional[Dict[str, Any]] = None

    # Admin Internal Notes (strictly admin-only, never sent to customer)
    internal_notes: List[Dict[str, Any]] = Field(default_factory=list)

    # AI Recommended Response Draft (advisory draft for support operators)
    draft_response: Optional[str] = None



# ---------------------------------------------------------------------------
# Gemini Structured Output Schemas (Call A & Call B)
# ---------------------------------------------------------------------------

class CustomerIntelligenceOutput(BaseModel):
    """Structured output expected from Gemini Call A."""
    category: str
    issue_label: str
    customer_issue: str
    sentiment: Literal["Positive", "Neutral", "Negative"]
    emotion: Literal[
        "Anger", "Frustration", "Satisfaction", "Confusion", "Urgency", "Disappointment", "Fear", "Neutral"
    ]
    emotion_intensity: int = Field(ge=1, le=5)
    is_angry: bool
    urgency: Literal["Low", "Medium", "High"]
    priority: Literal["Low", "Medium", "High", "Critical"]
    priority_reason: str
    resolution_status: Literal["Resolved", "Unresolved", "Pending"]
    resolution_reason: str
    summary: SummaryDetail


class SecurityIntelligenceOutput(BaseModel):
    """Structured output expected from Gemini Call B."""
    threat_detected: bool
    threat_type: Literal[
        "Phishing", "Social Engineering", "Impersonation", "Malware Attachment", "None"
    ]
    social_engineering: Literal["Yes", "Possible", "No"]
    techniques: List[str]
    credential_request: bool
    otp_request: bool
    risk_level: Literal["Low", "Medium", "High", "Critical"]
    risk_reasons: List[str]
    recommended_action: str


# ---------------------------------------------------------------------------
# Dashboard, Job, and Health Response Models
# ---------------------------------------------------------------------------

class HealthResponse(BaseModel):
    status: str = "ok"
    ai_mode: str = "gemini"
    model: str
    database: str
    version: str = "1.0.0"


class JobProgressResponse(BaseModel):
    job_id: str
    status: Literal["pending", "processing", "completed", "failed"]
    total: int = 0
    processed: int = 0
    errors: int = 0
    created_at: str
    completed_at: Optional[str] = None


class RankedIssue(BaseModel):
    issue_label: str
    count: int
    percentage: float
    trend: Optional[str] = "neutral"


class IssueFrequencyResponse(BaseModel):
    total_conversations: int
    issues: List[RankedIssue]


class DashboardKPIs(BaseModel):
    total_conversations: int = 0
    total_complaints: int = 0
    positive_count: int = 0
    neutral_count: int = 0
    negative_count: int = 0
    most_common_complaint: str = "None"
    most_frequent_issue: str = "None"
    unresolved_count: int = 0
    critical_count: int = 0
    threats_detected: int = 0
    angry_customers: int = 0


class DashboardResponse(BaseModel):
    kpis: DashboardKPIs
    sentiment_distribution: Dict[str, int]
    category_distribution: Dict[str, int]
    issue_frequency: List[RankedIssue]
    risk_distribution: Dict[str, int]
    emotion_distribution: Dict[str, int]
    daily_trend: List[Dict[str, Any]]


class EvaluationMetrics(BaseModel):
    total_eval_samples: int
    recall: float
    precision: float
    f1_score: float
    false_positive_rate: float
    avg_latency_ms: float
    ai_mode: str


# ---------------------------------------------------------------------------
# Multimodal AI Copilot Schemas
# ---------------------------------------------------------------------------

class IssueDiagnosisAndHelp(BaseModel):
    session_id: str
    created_at: str
    issue_title: str
    category: str
    severity: Literal["Low", "Medium", "High", "Critical"] = "Medium"
    root_cause: str
    visual_findings: List[str] = Field(default_factory=list)
    is_threat: bool = False
    threat_details: Optional[str] = None
    troubleshooting_steps: List[str] = Field(default_factory=list)
    suggested_response: str
    prevention_tip: str
    image_attached: bool = False
    image_name: Optional[str] = None
    processing_ms: int = 0
    ai_mode: str = "fallback"
    raw_message: Optional[str] = None


class CopilotDiagnoseRequest(BaseModel):
    message: Optional[str] = None
    image_data: Optional[str] = None
    image_name: Optional[str] = None
    channel: Optional[str] = "chat"


# ---------------------------------------------------------------------------
# Section 11 & RBAC: Authentication, Roles, Profiles & Audit Schemas
# ---------------------------------------------------------------------------

class UserProfile(BaseModel):
    id: str
    email: str
    display_name: Optional[str] = ""
    role: Literal["customer", "admin"] = "customer"
    status: Literal["active", "disabled"] = "active"
    is_demo: bool = False
    created_at: Optional[str] = None


class UserRoleUpdateRequest(BaseModel):
    role: Literal["customer", "admin"]


class AuditLogEntry(BaseModel):
    id: str
    actor_user_id: str
    actor_email: str = ""
    action: str
    target_resource_id: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AuthLoginRequest(BaseModel):
    email: str
    password: str


class AuthLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserProfile
    is_demo: bool = False
    message: Optional[str] = None


class AuthSignupRequest(BaseModel):
    email: str
    password: str
    display_name: Optional[str] = ""


class AuthResetPasswordRequest(BaseModel):
    email: str


class AuthUpdatePasswordRequest(BaseModel):
    password: str


class CustomerDashboardKPIs(BaseModel):
    total_my_conversations: int = 0
    my_threats_detected: int = 0
    my_pending_reviews: int = 0
    my_resolved_tickets: int = 0
    recent_activity: List[Dict[str, Any]] = Field(default_factory=list)


class AdminDashboardKPIs(BaseModel):
    total_users: int = 0
    total_customers: int = 0
    total_admins: int = 0
    total_platform_conversations: int = 0
    total_platform_threats: int = 0
    high_risk_threats: int = 0
    needs_review_count: int = 0
    unresolved_count: int = 0
    ai_status: Dict[str, Any] = Field(default_factory=dict)
    database_status: Dict[str, Any] = Field(default_factory=dict)
    recent_audit_logs: List[AuditLogEntry] = Field(default_factory=list)
    needs_attention: List[Dict[str, Any]] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Admin Intelligence Portal: Workflow, Review, Analytics & Observability
# ---------------------------------------------------------------------------

class AdminReviewCorrectionRequest(BaseModel):
    category: Optional[str] = None
    issue_label: Optional[str] = None
    priority: Optional[str] = None
    risk_level: Optional[str] = None
    resolution_status: Optional[str] = None
    reason: Optional[str] = "Manual administrative review & calibration"


class AdminStatusUpdateRequest(BaseModel):
    processing_status: Optional[str] = None
    resolution_status: Optional[str] = None
    assigned_to: Optional[str] = None


class AdminInternalNoteRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2000, description="Internal note text")


class AdminDraftResponseRequest(BaseModel):
    tone: Optional[str] = "professional"
    instructions: Optional[str] = None


class AdminDraftResponseResponse(BaseModel):
    draft_response: str
    recommended_action: str
    rationale: str


class AdminCategoryMetric(BaseModel):
    category: str
    count: int
    percentage: float
    unresolved_count: int = 0
    critical_count: int = 0
    threat_count: int = 0


class AdminCategoryAnalyticsResponse(BaseModel):
    total_conversations: int
    categories: List[AdminCategoryMetric]


class AdminSecurityAnalyticsResponse(BaseModel):
    total_threats: int
    critical_count: int
    high_count: int
    threat_types: Dict[str, int]
    techniques: Dict[str, int]
    top_domains: List[Dict[str, Any]]
    top_senders: List[Dict[str, Any]]
    top_attachments: List[Dict[str, Any]]


class AdminAIPerformanceResponse(BaseModel):
    total_analyzed: int
    gemini_count: int
    fallback_count: int
    fallback_rate: float
    avg_processing_ms: int
    human_corrections_count: int
    human_correction_rate: float
    review_queue_count: int
    model_name: str = "gemini-3.6-flash"
    prompt_injection_signals_caught: int = 0


class CustomerOverviewItem(BaseModel):
    customer_id: str
    email: str
    display_name: str
    conversation_count: int
    unresolved_count: int
    critical_count: int
    last_activity: str


class CustomerHistoryResponse(BaseModel):
    customer_id: str
    email: str
    display_name: str
    total_conversations: int
    conversations: List[ConversationRecord]


class AdminInboxResponse(BaseModel):
    items: List[ConversationRecord]
    total: int
    page: int
    limit: int
    total_pages: int
    facets: Dict[str, Any] = Field(default_factory=dict)


