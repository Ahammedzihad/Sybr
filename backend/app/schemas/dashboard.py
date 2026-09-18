"""Schemas for dashboard KPI and distribution statistics."""

from typing import Dict
from pydantic import BaseModel, Field


class DashboardStats(BaseModel):
    """
    Aggregated dashboard statistics matching the locked contract.
    """
    total_conversations: int = Field(0, description="Total count of analyzed conversations")
    high_risk_count: int = Field(0, description="Count of High and Critical risk items")
    resolved_count: int = Field(0, description="Count of Resolved and Dismissed items")
    pending_count: int = Field(0, description="Count of Flagged, Blocked, or Under Review items")
    categories: Dict[str, int] = Field(default_factory=dict, description="Distribution by category")
    sentiments: Dict[str, int] = Field(default_factory=dict, description="Distribution by sentiment")
    emotions: Dict[str, int] = Field(default_factory=dict, description="Distribution by emotion")
    risk_levels: Dict[str, int] = Field(default_factory=dict, description="Distribution by risk level")
    threat_types: Dict[str, int] = Field(default_factory=dict, description="Distribution by threat type")
