"""Analysis schemas including locked analysis contract."""

from typing import List
from pydantic import BaseModel, Field


class AnalysisRequest(BaseModel):
    """Input payload for email/message analysis."""
    sender: str = Field(..., description="Sender email address or identifier", json_schema_extra={"example": "security-update@paypal-verify.com"})
    subject: str = Field(..., description="Subject line of the email/message", json_schema_extra={"example": "Urgent: Your account is suspended"})
    message: str = Field(..., description="Full text content of the message", json_schema_extra={"example": "Please verify your identity at http://192.168.1.1/login"})
    urls: List[str] = Field(default_factory=list, description="List of URLs found in the message", json_schema_extra={"example": ["http://192.168.1.1/login"]})


class AnalysisResult(BaseModel):
    """
    Locked analysis result schema.
    DO NOT modify field names or add extra fields to this core contract.
    """
    category: str = Field(..., description="Classification category (e.g., Phishing, Malicious, Spam, Suspicious, Clean)")
    sentiment: str = Field(..., description="Tone/sentiment (e.g., Urgent, Alarming, Negative, Neutral, Positive)")
    emotion: str = Field(..., description="Targeted psychological emotion (e.g., Fear, Urgency, Greed, Curiosity, Neutral)")
    priority: str = Field(..., description="Triage priority (e.g., Critical, High, Medium, Low)")
    summary: str = Field(..., description="Concise narrative summary of the message and threat indicators")
    resolution_status: str = Field(..., description="Current status (e.g., Flagged, Blocked, Under Review, Resolved, Dismissed)")
    threat_type: str = Field(..., description="Specific threat classification (e.g., Credential Harvesting, Financial Fraud, Malicious Link, Social Engineering, None)")
    social_engineering: bool = Field(..., description="Whether social engineering tactics are present")
    suspicious_url: bool = Field(..., description="Whether any URL in the communication is suspicious/malicious")
    risk_level: str = Field(..., description="Overall risk rating (e.g., Critical, High, Medium, Low, Safe)")
    recommended_action: str = Field(..., description="Prescribed security or remediation action")


class SecurityIndicator(BaseModel):
    """Granular security indicator identified by the rule engine."""
    indicator: str
    severity: str  # Critical, High, Medium, Low
    description: str


class RuleAnalysisResult(BaseModel):
    """Output contract from the rule-based security engine."""
    suspicious_url: bool = False
    suspicious_sender: bool = False
    indicators: List[str] = Field(default_factory=list)
    details: List[SecurityIndicator] = Field(default_factory=list)
