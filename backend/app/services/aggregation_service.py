"""Aggregation service for dashboard telemetry."""

from app.database.repository import ConversationRepository
from app.schemas.dashboard import DashboardStats


class AggregationService:
    """Computes and formats aggregated metrics for the dashboard."""

    def __init__(self, repository: ConversationRepository):
        self.repository = repository

    def get_dashboard_metrics(self) -> DashboardStats:
        """Retrieves and computes dashboard stats from repository."""
        return self.repository.get_dashboard_stats()
