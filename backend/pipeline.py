"""
Pipeline processing module for customer conversation intelligence & security threat detection.
"""

import logging
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure backend directory is in sys.path
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

try:
    from utils import mask_pii
except ImportError:
    from backend.utils import mask_pii

try:
    from aggregation import detect_resolution
except ImportError:
    from backend.aggregation import detect_resolution

try:
    from security.preprocess import preprocess
    from security.url_check import check_url
    from security.email_check import check_email
    from ai.gemini_client import process_conversation
except ImportError:
    from backend.security.preprocess import preprocess
    from backend.security.url_check import check_url
    from backend.security.email_check import check_email
    from backend.ai.gemini_client import process_conversation

logger = logging.getLogger(__name__)


def run_pipeline(conversation_id: str, messages: List[Dict[str, Any]], **overrides) -> Dict[str, Any]:
    """
    Executes the ingestion, enrichment, and security analysis pipeline.

    1. Joins message texts into raw_text
    2. Calls mask_pii(raw_text) to produce masked_text
    3. Calls preprocess(raw_text) to produce clean_text
    4. Extracts URLs with regex r'https?://\\S+' (try/except safe)
    5. Extracts emails with regex r'[\\w\\.-]+@[\\w\\.-]+\\.\\w+' (try/except safe)
    6. Calls check_url(url) and check_email(email) if any found
    7. Calls process_conversation(clean_text, messages, url_flag, email_flag)
    8. Merges everything into one dict matching ConversationRecord schema
    """
    raw_text = ""
    try:
        # Step 1: Join message texts into raw_text
        raw_parts = []
        if isinstance(messages, list):
            for msg in messages:
                if isinstance(msg, dict):
                    text = msg.get("text") or msg.get("message") or msg.get("content") or msg.get("body") or ""
                    if text:
                        raw_parts.append(str(text))
                elif isinstance(msg, str):
                    raw_parts.append(msg)
                elif msg is not None:
                    raw_parts.append(str(msg))
        raw_text = "\n".join(raw_parts)

        # Step 2: Mask PII for display and long-term storage
        masked_text = mask_pii(raw_text)

        # Step 3: Preprocess raw text
        clean_text = preprocess(raw_text)

        # Step 4: Extract URLs safely
        urls = []
        try:
            if raw_text:
                urls = re.findall(r'https?://\S+', raw_text)
        except Exception as url_err:
            logger.warning(f"Error extracting URLs: {url_err}")
            urls = []

        # Step 5: Extract emails safely
        emails = []
        try:
            if raw_text:
                emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', raw_text)
        except Exception as email_err:
            logger.warning(f"Error extracting emails: {email_err}")
            emails = []

        # Step 6: Security checks for URLs and emails
        suspicious_url = False
        url_risk = "Low"
        url_reason = None
        if urls:
            for url in urls:
                try:
                    res = check_url(url)
                    if isinstance(res, dict):
                        if res.get("suspicious_url"):
                            suspicious_url = True
                            url_risk = res.get("url_risk", "High")
                            url_reason = res.get("url_reason")
                            break
                        elif not url_reason and res.get("url_risk"):
                            url_risk = res.get("url_risk", "Low")
                            url_reason = res.get("url_reason")
                except Exception as check_err:
                    logger.warning(f"Error checking URL '{url}': {check_err}")

        suspicious_email = False
        email_risk = "Low"
        email_reason = None
        if emails:
            for email in emails:
                try:
                    res = check_email(email)
                    if isinstance(res, dict):
                        if res.get("suspicious_email"):
                            suspicious_email = True
                            email_risk = res.get("email_risk", "High")
                            email_reason = res.get("email_reason")
                            break
                        elif not email_reason and res.get("email_risk"):
                            email_risk = res.get("email_risk", "Low")
                            email_reason = res.get("email_reason")
                except Exception as check_err:
                    logger.warning(f"Error checking email '{email}': {check_err}")

        # Step 7: Call AI processor
        url_flag = suspicious_url
        email_flag = suspicious_email
        ai_result = {}
        try:
            ai_result = process_conversation(clean_text, messages if isinstance(messages, list) else [], url_flag, email_flag)
            if not isinstance(ai_result, dict):
                ai_result = {}
        except Exception as ai_err:
            logger.warning(f"Error calling process_conversation: {ai_err}")
            ai_result = {}

        # Populate resolution_status using detect_resolution when messages has > 1 entry
        if isinstance(messages, list) and len(messages) > 1:
            resolution_status = detect_resolution(messages)
        else:
            resolution_status = ai_result.get("resolution_status", "Unknown")

        # Step 8: Merge everything into dictionary matching ConversationRecord schema
        record: Dict[str, Any] = {
            "conversation_id": str(conversation_id) if conversation_id else "UNKNOWN",
            "raw_text": raw_text,
            "clean_text": clean_text,
            "masked_text": masked_text,
            "category": overrides.get("category") or ai_result.get("category", "Unknown"),
            "sentiment": overrides.get("sentiment") or ai_result.get("sentiment", "Unknown"),
            "emotion": overrides.get("emotion") or ai_result.get("emotion", "Unknown"),
            "urgency": overrides.get("urgency") or ai_result.get("urgency", "Unknown"),
            "priority": overrides.get("priority") or ai_result.get("priority", "Unknown"),
            "keywords": overrides.get("keywords") if "keywords" in overrides else ai_result.get("keywords", []),
            "customer_request": overrides.get("customer_request") or ai_result.get("customer_request", ""),
            "resolution_status": overrides.get("resolution_status") or resolution_status,
            "summary": overrides.get("summary") or ai_result.get("summary"),
            "suspicious_url": overrides.get("suspicious_url") if "suspicious_url" in overrides else suspicious_url,
            "url_risk": overrides.get("url_risk") or url_risk,
            "url_reason": overrides.get("url_reason") or url_reason,
            "suspicious_email": overrides.get("suspicious_email") if "suspicious_email" in overrides else suspicious_email,
            "email_risk": overrides.get("email_risk") or email_risk,
            "email_reason": overrides.get("email_reason") or email_reason,
            "threat_type": overrides.get("threat_type") or ai_result.get("threat_type", "Unknown"),
            "social_engineering": overrides.get("social_engineering") if "social_engineering" in overrides else ai_result.get("social_engineering", False),
            "technique": overrides.get("technique") if "technique" in overrides else ai_result.get("technique", []),
            "risk_level": overrides.get("risk_level") or ai_result.get("risk_level", "Unknown"),
            "recommended_action": overrides.get("recommended_action") or ai_result.get("recommended_action", ""),
        }
        return record

    except Exception as err:
        logger.error(f"Critical error in run_pipeline for conversation '{conversation_id}': {err}", exc_info=True)
        return {
            "conversation_id": str(conversation_id) if conversation_id else "UNKNOWN",
            "raw_text": raw_text if 'raw_text' in locals() else "",
            "clean_text": "",
            "masked_text": "",
            "category": "Unknown",
            "sentiment": "Unknown",
            "emotion": "Unknown",
            "urgency": "Unknown",
            "priority": "Unknown",
            "keywords": [],
            "customer_request": "",
            "resolution_status": "Unknown",
            "summary": None,
            "suspicious_url": False,
            "url_risk": "Unknown",
            "url_reason": None,
            "suspicious_email": False,
            "email_risk": "Unknown",
            "email_reason": None,
            "threat_type": "Unknown",
            "social_engineering": False,
            "technique": [],
            "risk_level": "Unknown",
            "recommended_action": "",
            "error": str(err),
        }
