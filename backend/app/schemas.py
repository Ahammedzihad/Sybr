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
    processing_ms: int = 0

    # Optional metadata for persistence/display
    source: Optional[str] = "real"
    raw_text_masked: Optional[str] = None
    messages: Optional[List[Message]] = None


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
