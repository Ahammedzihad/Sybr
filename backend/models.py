"""
Pydantic schemas for AI Customer Support Intelligence & Threat Detection.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class ConversationRecord(BaseModel):
    """
    Schema representing a customer conversation record across ingestion,
    enrichment, and security analysis pipeline stages.
    
    All fields except conversation_id and raw_text are optional with sensible
    defaults to prevent validation failures on missing/partial data.
    """
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    # Required identifiers / primary raw input
    conversation_id: str
    raw_text: str

    # Text processing fields
    clean_text: Optional[str] = ""
    masked_text: Optional[str] = ""

    # Gemini & classification attributes
    category: Optional[str] = "Unknown"
    sentiment: Optional[str] = "Unknown"
    emotion: Optional[str] = "Unknown"
    urgency: Optional[str] = "Unknown"
    priority: Optional[str] = "Unknown"
    keywords: Optional[List[str]] = Field(default_factory=list)
    customer_request: Optional[str] = ""

    # Lifecycle / Resolution
    resolution_status: Optional[str] = "Unknown"
    summary: Optional[Dict[str, Any]] = None

    # Security Analysis - URL heuristics
    suspicious_url: Optional[bool] = False
    url_risk: Optional[str] = "Unknown"
    url_reason: Optional[str] = None

    # Security Analysis - Email heuristics
    suspicious_email: Optional[bool] = False
    email_risk: Optional[str] = "Unknown"
    email_reason: Optional[str] = None

    # Security Analysis - Threat intelligence
    threat_type: Optional[str] = "Unknown"
    social_engineering: Optional[bool] = False
    technique: Optional[List[str]] = Field(default_factory=list)
    risk_level: Optional[str] = "Unknown"
    recommended_action: Optional[str] = ""
    error: Optional[str] = None

    @field_validator("keywords", "technique", mode="before")
    @classmethod
    def default_none_list_to_empty(cls, value: Any) -> List[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return [str(v) for v in value]
        return [str(value)]
