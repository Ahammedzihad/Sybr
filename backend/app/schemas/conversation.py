"""Schemas for conversation storage and history querying."""

from typing import List, Optional
from pydantic import BaseModel, Field
from app.schemas.analysis import AnalysisResult


class ConversationRecord(BaseModel):
    """Stored conversation with its corresponding analysis."""
    id: str = Field(..., description="Unique conversation ID")
    sender: str
    subject: str
    message: str
    urls: List[str] = Field(default_factory=list)
    created_at: str
    analysis: AnalysisResult
    security_indicators: List[str] = Field(default_factory=list)


class ConversationListResponse(BaseModel):
    """Paginated list response for conversation history."""
    items: List[ConversationRecord]
    total: int
    page: int
    limit: int
    pages: int
