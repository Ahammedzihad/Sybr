"""Route for querying stored conversations and analyses."""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from app.api.dependencies import get_repository
from app.database.repository import ConversationRepository
from app.schemas.conversation import ConversationListResponse

router = APIRouter(prefix="", tags=["Conversations"])


@router.get(
    "/conversations",
    response_model=ConversationListResponse,
    summary="List analyzed conversations",
    description="Retrieves paginated history of analyzed communications with optional risk level filtering.",
)
def get_conversations(
    page: int = Query(1, ge=1, description="Page number starting at 1"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    risk_level: Optional[str] = Query(None, description="Filter by risk rating (e.g. Critical, High, Medium, Low, Safe)"),
    repository: ConversationRepository = Depends(get_repository),
) -> ConversationListResponse:
    """Returns paginated conversation history."""
    items, total = repository.get_all(page=page, limit=limit, risk_level=risk_level)
    total_pages = (total + limit - 1) // limit if total > 0 else 1

    return ConversationListResponse(
        items=items,
        total=total,
        page=page,
        limit=limit,
        pages=total_pages,
    )
