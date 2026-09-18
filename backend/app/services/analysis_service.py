"""
Analysis Service.
Orchestrates the entire security pipeline:
Input Validation -> Security Rule Execution -> Gemini AI Analysis -> Aggregation & Reconcile -> Persistence -> Response.
"""

import re
from typing import List, Set
from app.core.logging import logger
from app.database.repository import ConversationRepository
from app.schemas.analysis import AnalysisRequest, AnalysisResult
from app.security.email_analyzer import EmailAnalyzer
from app.security.url_analyzer import URLAnalyzer
from app.services.gemini_service import GeminiService


class AnalysisService:
    """Orchestrates security rules, Gemini inference, and persistence."""

    def __init__(
        self,
        gemini_service: GeminiService,
        repository: ConversationRepository,
        url_analyzer: URLAnalyzer = None,
        email_analyzer: EmailAnalyzer = None,
    ):
        self.gemini_service = gemini_service
        self.repository = repository
        self.url_analyzer = url_analyzer or URLAnalyzer()
        self.email_analyzer = email_analyzer or EmailAnalyzer()

    async def process_analysis(self, request: AnalysisRequest) -> AnalysisResult:
        """
        Executes the full pipeline for an incoming message.
        """
        logger.info(f"Starting security analysis for message from '{request.sender}'")

        # 1. Gather all URLs (provided + extracted from body)
        all_urls: List[str] = list(request.urls)
        extracted_urls = re.findall(
            r"(?:https?://|www\.)[^\s<>\"'\)\],;]+", request.message
        )
        for u in extracted_urls:
            if u not in all_urls:
                all_urls.append(u)

        # 2. Execute Rule-Based Security Engine
        url_security = self.url_analyzer.analyze_many(all_urls)
        email_security = self.email_analyzer.analyze(
            sender=request.sender,
            subject=request.subject,
            message_preview=request.message[:200],
        )

        combined_indicators: Set[str] = set(url_security["indicators"] + email_security["indicators"])
        is_suspicious_url_flag = url_security["suspicious_url"]
        is_suspicious_sender_flag = email_security["is_suspicious"]

        logger.info(
            f"Security rules completed. Found {len(combined_indicators)} indicators: {list(combined_indicators)}"
        )

        # 3. Execute Gemini AI Analysis
        gemini_result = await self.gemini_service.analyze_message(
            sender=request.sender,
            subject=request.subject,
            message=request.message,
            urls=all_urls,
        )

        # 4. Reconcile AI Analysis with Deterministic Security Rules
        final_category = gemini_result.category
        final_risk = gemini_result.risk_level
        final_suspicious_url = gemini_result.suspicious_url or is_suspicious_url_flag
        final_social_eng = gemini_result.social_engineering or ("freemail_brand_spoofing" in combined_indicators)
        final_threat_type = gemini_result.threat_type

        # Check for critical deterministic indicators
        has_critical_indicators = any(
            ind in combined_indicators
            for ind in [
                "ip_literal_url",
                "lookalike_domain",
                "lookalike_sender_domain",
                "freemail_brand_spoofing",
                "userinfo_obfuscation",
            ]
        )

        if has_critical_indicators:
            logger.info("Deterministic critical security indicators detected. Escalating risk rating to Critical.")
            final_risk = "Critical"
            if final_category == "Clean":
                final_category = "Phishing"
            if final_threat_type == "None":
                final_threat_type = "Credential Harvesting" if "login" in request.message.lower() or "verify" in request.message.lower() else "Social Engineering"
            final_social_eng = True

        elif is_suspicious_url_flag or is_suspicious_sender_flag:
            if final_risk in ["Safe", "Low"]:
                final_risk = "High"
            if final_category == "Clean":
                final_category = "Suspicious"

        # Build final locked AnalysisResult
        final_analysis = AnalysisResult(
            category=final_category,
            sentiment=gemini_result.sentiment,
            emotion=gemini_result.emotion,
            priority=gemini_result.priority if final_risk != "Critical" else "Critical",
            summary=gemini_result.summary,
            resolution_status=gemini_result.resolution_status if final_risk not in ["High", "Critical"] else "Flagged",
            threat_type=final_threat_type,
            social_engineering=final_social_eng,
            suspicious_url=final_suspicious_url,
            risk_level=final_risk,
            recommended_action=gemini_result.recommended_action,
        )

        # 5. Store conversation and analysis
        try:
            self.repository.save(
                sender=request.sender,
                subject=request.subject,
                message=request.message,
                urls=all_urls,
                analysis=final_analysis,
                security_indicators=list(combined_indicators),
            )
            logger.info("Analysis and conversation persisted to database successfully")
        except Exception as e:
            logger.error(f"Failed to persist analysis to database: {e}")
            # Do not crash the API request if database save encounters an issue

        return final_analysis
