"""Route for retrieving aggregated dashboard telemetry."""

from fastapi import APIRouter, Depends
from app.api.dependencies import get_aggregation_service
from app.schemas.dashboard import DashboardStats
from app.services.aggregation_service import AggregationService

router = APIRouter(prefix="", tags=["Dashboard"])


@router.get(
    "/dashboard",
    response_model=DashboardStats,
    summary="Retrieve aggregated dashboard metrics",
    description="Calculates KPI totals and distribution metrics for dashboard charts.",
)
def get_dashboard_stats(
    aggregation_service: AggregationService = Depends(get_aggregation_service),
) -> DashboardStats:
    """Returns aggregated security analytics metrics."""
    return aggregation_service.get_dashboard_metrics()
