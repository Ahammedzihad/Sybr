"""FastAPI dependencies for services and repositories."""

from functools import lru_cache
from fastapi import Depends
from app.database.repository import ConversationRepository
from app.security.email_analyzer import EmailAnalyzer
from app.security.url_analyzer import URLAnalyzer
from app.services.aggregation_service import AggregationService
from app.services.analysis_service import AnalysisService
from app.services.gemini_service import GeminiService


@lru_cache()
def get_repository() -> ConversationRepository:
    """Provides a singleton repository instance."""
    return ConversationRepository()


@lru_cache()
def get_gemini_service() -> GeminiService:
    """Provides a singleton Gemini AI service instance."""
    return GeminiService()


@lru_cache()
def get_url_analyzer() -> URLAnalyzer:
    """Provides a URL analyzer instance."""
    return URLAnalyzer()


@lru_cache()
def get_email_analyzer() -> EmailAnalyzer:
    """Provides an Email analyzer instance."""
    return EmailAnalyzer()


def get_analysis_service(
    gemini_service: GeminiService = Depends(get_gemini_service),
    repository: ConversationRepository = Depends(get_repository),
    url_analyzer: URLAnalyzer = Depends(get_url_analyzer),
    email_analyzer: EmailAnalyzer = Depends(get_email_analyzer),
) -> AnalysisService:
    """Provides an AnalysisService instance with injected components."""
    return AnalysisService(
        gemini_service=gemini_service,
        repository=repository,
        url_analyzer=url_analyzer,
        email_analyzer=email_analyzer,
    )


def get_aggregation_service(
    repository: ConversationRepository = Depends(get_repository),
) -> AggregationService:
    """Provides an AggregationService instance."""
    return AggregationService(repository=repository)
