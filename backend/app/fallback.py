"""
Local Heuristic and Rule-Based Fallback Engine.
Generates complete ConversationRecords adhering strictly to the Section 5 contract
when Gemini is offline, rate-limited, or unconfigured.
"""
import re
import time
from typing import List, Dict, Any, Optional
from app.config import CATEGORIES, ISSUE_LABELS
from app.schemas import (
    ConversationRecord,
    SummaryDetail,
    SecurityDetail,
    Message,
)
from app.security.scoring import apply_merge_and_overrides


# Category keyword heuristics
CATEGORY_KEYWORDS = {
    "Billing/Payment": [
        "payment", "charged", "deducted", "billing", "bill", "invoice",
        "upi", "card", "bank", "debited", "overcharge", "double charge", "gateway"
    ],
    "Refund Request": [
        "refund", "money back", "return money", "reimbursement", "refunded", "reversal"
    ],
    "Account/Login": [
        "login", "sign in", "password", "account", "otp", "2fa", "blocked",
        "locked", "compromise", "hacked", "access", "reset password", "credentials"
    ],
    "Delivery/Shipping": [
        "delivery", "shipping", "courier", "package", "parcel", "dispatched",
        "delivered", "delayed delivery", "tracking", "order status"
    ],
    "Product Issue": [
        "damaged", "broken", "faulty", "wrong item", "defect", "defective",
        "quality", "missing item", "fake", "hardware"
    ],
    "Subscription Issue": [
        "subscription", "membership", "renew", "renewal", "cancel plan",
        "downgrade", "auto-renew", "recurring"
    ],
    "Technical Problem": [
        "crash", "bug", "error", "glitch", "screen", "loading", "server",
        "app not working", "not opening", "freeze", "blank", "exception"
    ],
    "Service Quality": [
        "agent", "representative", "rude", "poor service", "worst service",
        "no response", "ignored", "complaint", "behavior"
    ],
    "Security Concern": [
        "phishing", "scam", "fraud", "unauthorized", "suspicious", "stolen",
        "compromised", "virus", "malware", "fake email", "fake website"
    ],
}

# Controlled issue label heuristics
ISSUE_LABEL_KEYWORDS = {
    "Payment Failure": ["payment failed", "transaction failed", "payment error", "deducted", "debited"],
    "Duplicate Charge": ["charged twice", "double charged", "duplicate charge", "charged again"],
    "Refund Delay": ["refund delay", "refund not received", "where is my refund", "waiting for refund", "refund pending", "refund not credited", "refund"],
    "Password Reset": ["reset password", "forgot password", "change password", "password link"],
    "Login Failure": ["cannot login", "unable to sign in", "login failed", "account locked", "invalid credentials"],
    "Delivery Delay": ["delivery delay", "late delivery", "not delivered", "where is my order", "shipment delayed"],
    "Wrong/Damaged Item": ["wrong item", "damaged item", "broken item", "defective", "missing item"],
    "Order Not Confirmed": ["order not confirmed", "no confirmation", "order not placed", "order status"],
    "Subscription Cancellation": ["cancel subscription", "cancel membership", "stop renewal"],
    "App Crash/Bug": ["app crash", "app crashing", "bug", "error code", "app stops"],
    "Service Outage": ["service outage", "server down", "outage", "maintenance", "system down"],
    "Account Compromise": ["account hacked", "unauthorized access", "someone logged in"],
    "Unauthorized Transaction": [
        "unauthorized transaction", "did not make this payment", "money stolen",
        "without permission", "transferred without", "without my permission",
        "without authorization", "unauthorized transfer"
    ],
    "Phishing Attempt": ["phishing", "suspicious email", "fake link", "lottery scam"],
    "Poor Support Experience": ["worst support", "rude agent", "no one responded", "poor support"],
}

# Sentiment Lexicons
POSITIVE_WORDS = {
    "thank", "thanks", "great", "excellent", "awesome", "helpful", "good",
    "satisfied", "resolved", "appreciate", "quick", "best", "perfect", "happy"
}

NEGATIVE_WORDS = {
    "bad", "terrible", "worst", "fail", "failed", "error", "horrible", "useless",
    "scam", "cheat", "fraud", "disappointed", "angry", "annoyed", "frustrated",
    "poor", "waste", "stolen", "deducted", "delay", "delayed", "unacceptable",
    "loss", "sucks", "disaster", "broken", "pathetic", "sue", "legal action"
}

EMOTION_PATTERNS = {
    "Anger": ["worst", "furious", "unacceptable", "sue you", "legal action", "cheat", "thief", "scoundrel", "scam"],
    "Frustration": ["still waiting", "again", "third time", "ignored", "no response", "fed up", "tired of", "delay"],
    "Confusion": ["confused", "don't understand", "why did this happen", "how to", "what does this mean"],
    "Urgency": ["urgent", "immediately", "emergency", "asap", "right now", "within 24 hours", "critical"],
    "Disappointment": ["disappointed", "let down", "expected better", "not happy", "poor experience"],
    "Fear": ["compromised", "hacked", "unauthorized", "stolen", "safety", "threat"],
    "Satisfaction": ["thank you", "thanks a lot", "great help", "resolved", "works now", "appreciate"],
}


def analyze_sentiment(text: str) -> str:
    """Classifies sentiment into Positive, Neutral, or Negative."""
    words = re.findall(r'\b[a-z]+\b', text.lower())
    pos_count = sum(1 for w in words if w in POSITIVE_WORDS)
    neg_count = sum(1 for w in words if w in NEGATIVE_WORDS)

    if pos_count > neg_count and pos_count >= 1:
        return "Positive"
    elif neg_count > pos_count:
        return "Negative"
    else:
        return "Neutral"


def analyze_emotion(text: str, is_angry: bool, sentiment: str) -> tuple[str, int]:
    """Determines predominant emotion and intensity (1-5)."""
    text_lower = text.lower()
    
    if is_angry:
        return "Anger", 5

    # Check specific emotion triggers
    for emotion, cues in EMOTION_PATTERNS.items():
        if any(c in text_lower for c in cues):
            intensity = 4 if emotion in ("Anger", "Urgency", "Fear") else 3
            return emotion, intensity

    if sentiment == "Positive":
        return "Satisfaction", 3
    elif sentiment == "Negative":
        return "Frustration", 3
    else:
        return "Neutral", 1


def detect_anger_cues(text: str) -> bool:
    """
    Flags true anger: ALL CAPS shouting, exclamation marks >= 2,
    insults, legal threats, or 'worst service'.
    """
    if not text:
        return False

    # Check for repeated exclamation
    if "!!" in text:
        return True

    # Check for heavy uppercase shouting (e.g. > 40% uppercase in longer message)
    letters = [c for c in text if c.isalpha()]
    if len(letters) > 15:
        upper_ratio = sum(1 for c in letters if c.isupper()) / len(letters)
        if upper_ratio > 0.45:
            return True

    text_lower = text.lower()
    anger_phrases = [
        "worst service", "worst app", "worst company", "legal action", "lawyer",
        "consumer court", "police complaint", "cheating", "fraudsters", "loot"
    ]
    return any(p in text_lower for p in anger_phrases)


def classify_category_and_issue(text: str) -> tuple[str, str, str]:
    """
    Matches text to one of the 10 fixed categories and 16 canonical issue labels.
    """
    text_lower = text.lower()

    # Match Issue Label
    matched_issue = "Other"
    for issue, phrases in ISSUE_LABEL_KEYWORDS.items():
        if any(p in text_lower for p in phrases):
            matched_issue = issue
            break

    # Match Category
    matched_category = "Other"
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(k in text_lower for k in keywords):
            matched_category = category
            break

    # Reconcile issue label and category if mismatched
    if matched_issue in ("Payment Failure", "Duplicate Charge") and matched_category == "Other":
        matched_category = "Billing/Payment"
    elif matched_issue == "Refund Delay" and matched_category == "Other":
        matched_category = "Refund Request"
    elif matched_issue in ("Password Reset", "Login Failure") and matched_category == "Other":
        matched_category = "Account/Login"
    elif matched_issue == "Delivery Delay" and matched_category == "Other":
        matched_category = "Delivery/Shipping"
    elif matched_issue == "Wrong/Damaged Item" and matched_category == "Other":
        matched_category = "Product Issue"
    elif matched_issue in ("Account Compromise", "Unauthorized Transaction", "Phishing Attempt"):
        matched_category = "Security Concern"

    customer_issue = matched_issue if matched_issue != "Other" else (text[:80].strip() or "General inquiry")

    return matched_category, matched_issue, customer_issue


def determine_urgency_and_priority(
    text: str,
    category: str,
    issue_label: str,
    is_angry: bool,
    sentiment: str,
) -> tuple[str, str, str]:
    """Computes urgency (Low/Medium/High) and priority with explainable reason."""
    text_lower = text.lower()
    urgent_words = ["urgent", "immediately", "emergency", "asap", "within 24 hours", "threat", "stolen"]
    is_urgent = any(w in text_lower for w in urgent_words)

    # Urgency
    if is_urgent or is_angry:
        urgency = "High"
    elif sentiment == "Negative" or category in ("Billing/Payment", "Refund Request"):
        urgency = "Medium"
    else:
        urgency = "Low"

    # Priority Rules from Section 7:
    # Critical = account compromise, unauthorized transaction, fraud, active outage
    # High = money deducted/not received, repeated unresolved complaint, angry + high urgency
    # Medium = delays/refunds with normal tone
    # Low = questions, feedback, positive messages
    if issue_label in ("Account Compromise", "Unauthorized Transaction", "Service Outage"):
        priority = "Critical"
        reason = "Critical account compromise, unauthorized transaction, or service outage detected."
    elif is_angry and urgency == "High":
        priority = "High"
        reason = "Customer expressing high anger and urgent grievance requiring immediate escalation."
    elif issue_label in ("Payment Failure", "Duplicate Charge", "Refund Delay"):
        priority = "High"
        reason = "Direct financial impact reported with pending resolution."
    elif urgency == "High":
        priority = "High"
        reason = "High urgency cues flagged in customer message."
    elif sentiment == "Negative" or category in ("Billing/Payment", "Refund Request"):
        priority = "Medium"
        reason = "Customer reported an issue with billing or refund request."
    else:
        priority = "Low"
        reason = "Routine customer interaction without severe escalation factors."

    return urgency, priority, reason


def determine_resolution_status(
    messages: List[Message],
    text: str,
) -> tuple[str, str]:
    """
    Section 6 E2: Across the thread, look for repeated complaint mentions without confirmation.
    Output Resolved / Unresolved / Pending + reason.
    """
    text_lower = text.lower()
    resolved_indicators = [
        "resolved", "refund processed", "issue is fixed", "ticket closed",
        "thank you it works", "working fine now", "problem solved"
    ]
    unresolved_indicators = [
        "still not", "again", "third time", "second time", "no update",
        "no response", "haven't heard", "still waiting", "why no reply"
    ]

    has_resolution = any(r in text_lower for r in resolved_indicators)
    has_repeated_complaint = any(u in text_lower for u in unresolved_indicators) or len(messages) >= 3

    if has_resolution:
        return "Resolved", "Confirmation message or fix acknowledgement present in thread."
    elif has_repeated_complaint:
        return "Unresolved", "Repeated follow-ups or ongoing issue detected without confirmed resolution."
    else:
        return "Pending", "Customer request received; awaiting resolution from support agent."


def build_structured_summary(
    text: str,
    customer_issue: str,
    priority: str,
    resolution_status: str,
    messages: List[Message],
) -> SummaryDetail:
    """Constructs the Section 5 summary object."""
    first_customer_msg = next((m.text for m in messages if m.sender == "customer"), text)
    actions = "Support ticket created and categorized"
    if any(m.sender != "customer" for m in messages):
        actions = "Agent reviewed issue and initiated troubleshooting"

    return SummaryDetail(
        issue=customer_issue[:180],
        customer_request=(first_customer_msg[:180] or "Request assistance with account or service"),
        actions_taken=actions,
        current_status=f"Status: {resolution_status}",
        priority=f"Priority level: {priority}",
    )


def fallback_analyze(
    conversation_id: str,
    channel: str,
    created_at: str,
    raw_text_masked: str,
    messages: List[Message],
    keywords: List[str],
    security: SecurityDetail,
    source: str = "real",
) -> ConversationRecord:
    """
    Main fallback analyzer. Emits the full Section 5 JSON shape using deterministic heuristics.
    """
    start_time = time.time()

    # 1. Classification & NLP heuristics
    category, issue_label, customer_issue = classify_category_and_issue(raw_text_masked)
    sentiment = analyze_sentiment(raw_text_masked)
    is_angry = detect_anger_cues(raw_text_masked)
    emotion, intensity = analyze_emotion(raw_text_masked, is_angry, sentiment)
    urgency, priority, priority_reason = determine_urgency_and_priority(
        raw_text_masked, category, issue_label, is_angry, sentiment
    )
    res_status, res_reason = determine_resolution_status(messages, raw_text_masked)

    # 2. Section 8.6 Override rules
    updated_security, final_priority, final_priority_reason, final_category = apply_merge_and_overrides(
        security_detail=security,
        gemini_risk=None,
        sentiment=sentiment,
        is_angry=is_angry,
        urgency=urgency,
        priority=priority,
        priority_reason=priority_reason,
        resolution_status=res_status,
        category=category,
    )

    # 3. Structured summary
    summary = build_structured_summary(
        text=raw_text_masked,
        customer_issue=customer_issue,
        priority=final_priority,
        resolution_status=res_status,
        messages=messages,
    )

    elapsed_ms = int((time.time() - start_time) * 1000)

    return ConversationRecord(
        conversation_id=conversation_id,
        channel=channel,
        created_at=created_at,
        customer_issue=customer_issue,
        category=final_category,
        issue_label=issue_label,
        keywords=keywords,
        sentiment=sentiment,
        emotion=emotion,
        emotion_intensity=intensity,
        is_angry=is_angry,
        urgency=urgency,
        priority=final_priority,
        priority_reason=final_priority_reason,
        resolution_status=res_status,
        resolution_reason=res_reason,
        summary=summary,
        security=updated_security,
        ai_mode="fallback",
        processing_ms=elapsed_ms,
        source=source,
        raw_text_masked=raw_text_masked,
        messages=messages,
    )
