"""
Gemini AI Service Layer.
Encapsulates all Google Gemini SDK interactions, prompt engineering,
strict JSON schema formatting, validation, and offline mock fallback.
"""

import os
from typing import Any, Dict, List, Optional
from app.core.config import settings
from app.core.logging import logger
from app.schemas.analysis import AnalysisResult
from app.utils.json_parser import extract_and_parse_json

SYSTEM_INSTRUCTION = """You are an elite cybersecurity threat analyst specializing in email security, social engineering, phishing, and scam detection.

Your task is to analyze the provided message/email communication and output a structured JSON analysis strictly following this format:
{
  "category": "Phishing" | "Malicious" | "Spam" | "Suspicious" | "Clean",
  "sentiment": "Urgent" | "Alarming" | "Negative" | "Neutral" | "Positive",
  "emotion": "Fear" | "Urgency" | "Greed" | "Curiosity" | "Neutral",
  "priority": "Critical" | "High" | "Medium" | "Low",
  "summary": "1-2 sentence concise summary of the communication and observed threat vectors",
  "resolution_status": "Flagged" | "Blocked" | "Under Review" | "Resolved" | "Dismissed",
  "threat_type": "Credential Harvesting" | "Financial Fraud" | "Malicious Link" | "Social Engineering" | "None",
  "social_engineering": true | false,
  "suspicious_url": true | false,
  "risk_level": "Critical" | "High" | "Medium" | "Low" | "Safe",
  "recommended_action": "Clear actionable instruction for security responders or end-users"
}

CRITICAL RULES:
1. You must ONLY output a valid JSON object. Do not include introductory text, explanations, or conclusions.
2. The JSON keys MUST exactly match the 11 fields above.
3. Booleans must be JSON true or false.
"""


class GeminiService:
    """Service providing Gemini AI analysis with validation and graceful mock fallback."""

    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.mock_mode = (
            settings.GEMINI_MOCK_MODE
            or not self.api_key
            or self.api_key == "your_gemini_api_key_here"
        )
        self._client = None
        self._init_client()

    def _init_client(self):
        """Initializes Gemini client safely if API key is present."""
        if self.mock_mode:
            logger.info("GeminiService initialized in MOCK MODE (offline/fallback mode)")
            return

        try:
            # Try official google-genai client first
            from google import genai
            self._client = genai.Client(api_key=self.api_key)
            logger.info("GeminiService initialized with google-genai client")
        except Exception as e:
            logger.warning(f"Failed to initialize google-genai: {e}. Falling back to google.generativeai")
            try:
                import google.generativeai as legacy_genai
                legacy_genai.configure(api_key=self.api_key)
                self._client = legacy_genai.GenerativeModel(settings.GEMINI_MODEL)
                logger.info("GeminiService initialized with google.generativeai")
            except Exception as e2:
                logger.error(f"Failed to initialize Gemini SDK: {e2}. Forcing mock mode.")
                self.mock_mode = True

    async def analyze_message(
        self, sender: str, subject: str, message: str, urls: List[str]
    ) -> AnalysisResult:
        """
        Analyzes a message using Gemini AI or fallback mock mode.
        Guarantees returning a valid AnalysisResult without throwing exceptions.
        """
        if self.mock_mode:
            logger.info(f"Running mock Gemini analysis for sender={sender}, subject='{subject[:30]}'")
            return self._generate_mock_analysis(sender, subject, message, urls)

        prompt = f"""Analyze this incoming communication:
Sender: {sender}
Subject: {subject}
Message Body:
\"\"\"
{message}
\"\"\"
Enclosed URLs: {', '.join(urls) if urls else 'None'}

Produce the required JSON output:"""

        try:
            logger.info(f"Sending prompt to Gemini API for message subject='{subject[:30]}'")
            raw_text = await self._call_gemini_api(prompt)
            parsed_json = extract_and_parse_json(raw_text)

            if not parsed_json:
                logger.warning("Gemini returned non-JSON text. Falling back to structured default.")
                return self._generate_mock_analysis(sender, subject, message, urls)

            # Validate against locked schema
            result = AnalysisResult(**parsed_json)
            logger.info("Gemini analysis successfully validated against AnalysisResult schema")
            return result

        except Exception as err:
            logger.error(f"Gemini API request or parsing failed: {err}. Utilizing fallback analysis.")
            return self._generate_mock_analysis(sender, subject, message, urls)

    async def _call_gemini_api(self, prompt: str) -> str:
        """Calls Gemini API with proper model configuration."""
        import asyncio

        def _sync_call():
            if hasattr(self._client, "models"):
                # google-genai v1.x client
                response = self._client.models.generate_content(
                    model=settings.GEMINI_MODEL,
                    contents=f"{SYSTEM_INSTRUCTION}\n\n{prompt}",
                )
                return response.text
            else:
                # google.generativeai client
                response = self._client.generate_content(f"{SYSTEM_INSTRUCTION}\n\n{prompt}")
                return response.text

        # Run synchronous SDK call in threadpool so FastAPI remains non-blocking
        return await asyncio.to_thread(_sync_call)

    def _generate_mock_analysis(
        self, sender: str, subject: str, message: str, urls: List[str]
    ) -> AnalysisResult:
        """
        Generates an intelligent context-aware mock response matching the locked schema.
        Ensures smooth developer experience and full offline functionality.
        """
        text_corpus = f"{sender} {subject} {message}".lower()

        # Check for phishing keywords
        phish_signals = [
            "urgent", "suspended", "immediately", "verify", "password",
            "unauthorized", "compromised", "bank", "security alert",
            "action required", "wire", "invoice", "bitcoin", "wallet", "crypto"
        ]
        has_phish_signals = any(k in text_corpus for k in phish_signals)
        has_urls = len(urls) > 0

        if has_phish_signals:
            return AnalysisResult(
                category="Phishing",
                sentiment="Urgent",
                emotion="Fear",
                priority="High",
                summary=f"Detected high-urgency communication with social engineering indicators regarding '{subject}'.",
                resolution_status="Flagged",
                threat_type="Credential Harvesting" if "password" in text_corpus or "verify" in text_corpus else "Social Engineering",
                social_engineering=True,
                suspicious_url=has_urls,
                risk_level="High" if has_urls else "Medium",
                recommended_action="Do not click links or provide credentials. Quarantine message and report to security team.",
            )
        elif "invoice" in text_corpus or "payment" in text_corpus or "receipt" in text_corpus:
            return AnalysisResult(
                category="Suspicious",
                sentiment="Neutral",
                emotion="Curiosity",
                priority="Medium",
                summary=f"Unverified billing or financial inquiry concerning '{subject}'.",
                resolution_status="Under Review",
                threat_type="Financial Fraud",
                social_engineering=True,
                suspicious_url=has_urls,
                risk_level="Medium",
                recommended_action="Verify invoice legitimacy with accounts payable before authorizing transactions.",
            )
        else:
            return AnalysisResult(
                category="Clean",
                sentiment="Neutral",
                emotion="Neutral",
                priority="Low",
                summary=f"Routine business or personal correspondence: '{subject}'. No overt security anomalies detected.",
                resolution_status="Resolved",
                threat_type="None",
                social_engineering=False,
                suspicious_url=False,
                risk_level="Safe",
                recommended_action="No security remediation required. Safe to process normally.",
            )
