"""Route for analyzing emails and messages."""

from fastapi import APIRouter, Depends, HTTPException, status
from app.core.logging import logger
from app.schemas.analysis import AnalysisRequest, AnalysisResult
from app.services.analysis_service import AnalysisService
from app.api.dependencies import get_analysis_service

router = APIRouter(prefix="", tags=["Analysis"])


@router.post(
    "/analyze",
    response_model=AnalysisResult,
    summary="Analyze incoming email/message",
    description="Processes message through rule-based security analyzers and Gemini AI to produce structured threat intelligence.",
)
async def analyze_message(
    payload: AnalysisRequest,
    analysis_service: AnalysisService = Depends(get_analysis_service),
) -> AnalysisResult:
    """
    Submits a message and associated URLs for security and threat evaluation.
    """
    try:
        result = await analysis_service.process_analysis(payload)
        return result
    except Exception as exc:
        logger.error(f"Analysis processing error: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to analyze message. Please verify input and retry.",
        )
