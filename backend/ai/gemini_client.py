"""
Gemini AI client integration module.
Stub implementation returning analysis matching ConversationRecord schema.
"""

from typing import Any, Dict, List


def process_conversation(
    clean_text: str,
    messages: List[Dict[str, Any]],
    url_flag: bool,
    email_flag: bool,
) -> Dict[str, Any]:
    """Stub AI analysis returning placeholder fields compliant with the schema."""
    text_lower = (clean_text or "").lower()

    # Determine category and keywords
    if any(k in text_lower for k in ["billing", "refund", "charge", "invoice", "payment"]):
        category = "Billing"
        keywords = ["billing", "refund"]
    elif any(k in text_lower for k in ["password", "login", "account", "otp", "auth"]):
        category = "Account/Login"
        keywords = ["account", "login"]
    elif any(k in text_lower for k in ["security", "phish", "hacked", "breach", "scam"]):
        category = "Security"
        keywords = ["security", "phishing"]
    elif any(k in text_lower for k in ["delivery", "shipping", "track", "package", "order"]):
        category = "Delivery"
        keywords = ["delivery", "shipping"]
    elif clean_text or messages:
        category = "Technical Support"
        keywords = ["support", "inquiry"]
    else:
        category = "Unknown"
        keywords = []

    # Determine sentiment
    if any(k in text_lower for k in ["angry", "frustrated", "terrible", "worst", "unacceptable", "broken", "failed"]):
        sentiment = "Negative"
        emotion = "Frustration"
    elif any(k in text_lower for k in ["thank", "great", "awesome", "helpful", "fixed", "resolved", "excellent"]):
        sentiment = "Positive"
        emotion = "Satisfaction"
    elif clean_text or messages:
        sentiment = "Neutral"
        emotion = "Neutral"
    else:
        sentiment = "Unknown"
        emotion = "Unknown"

    # Determine risk & priority
    if "emergency" in text_lower or "critical" in text_lower:
        risk_level = "Critical"
        priority = "Critical"
        threat_type = "Critical Vulnerability" if (url_flag or email_flag) else "None"
    elif url_flag or email_flag:
        risk_level = "High"
        priority = "High"
        threat_type = "Phishing"
    else:
        risk_level = "Low"
        priority = "Medium" if (clean_text or messages) else "Low"
        threat_type = "None"

    urgency = "High" if priority in ["Critical", "High"] else "Low"

    return {
        "category": category,
        "sentiment": sentiment,
        "emotion": emotion,
        "urgency": urgency,
        "priority": priority,
        "keywords": keywords,
        "customer_request": clean_text[:120] if clean_text else "",
        "resolution_status": "Unresolved" if (clean_text or messages) else "Unknown",
        "summary": {
            "overview": clean_text[:160] if clean_text else "Customer conversation thread."
        },
        "threat_type": threat_type,
        "social_engineering": url_flag or email_flag,
        "technique": ["Urgency"] if (url_flag or email_flag) else [],
        "risk_level": risk_level,
        "recommended_action": "Review conversation and verify sender details.",
    }
