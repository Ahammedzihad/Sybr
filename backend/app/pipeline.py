"""
Section 4. Master Analysis Pipeline (Steps 1–9).
Orchestrates entity extraction, PII redaction, deterministic security rules,
Gemini dual-call semantic intelligence, override rules, and persistence.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from app.schemas import ConversationRecord, Message
from app.preprocess import mask_pii, extract_keywords
from app.security.url_check import extract_urls
from app.security.email_check import extract_emails_from_text
from app.security.scoring import evaluate_security_rules
from app.gemini_client import analyze_with_gemini_or_fallback
from app.db import upsert_conversation


def process_conversation(conv_dict: Dict[str, Any], persist: bool = True) -> ConversationRecord:
    """
    Executes the end-to-end 9-step analysis pipeline for a single conversation.
    """
    conv_id = conv_dict.get("conversation_id") or "CS-00001"
    channel = conv_dict.get("channel") or "chat"
    created_at = conv_dict.get("created_at") or datetime.now(timezone.utc).isoformat()
    source = conv_dict.get("source") or "real"
    raw_messages: List[Message] = conv_dict.get("messages") or []

    # 1. Normalize full conversation thread text
    if len(raw_messages) > 1:
        full_raw_text = "\n".join(f"{m.sender}: {m.text}" for m in raw_messages)
    elif raw_messages:
        full_raw_text = raw_messages[0].text
    else:
        full_raw_text = conv_dict.get("text") or ""
        raw_messages = [Message(sender="customer", text=full_raw_text, timestamp=created_at)]

    # 2. Extract Entities BEFORE PII masking so security indicators remain intact
    extracted_urls = list(conv_dict.get("urls") or [])
    extracted_urls.extend(extract_urls(full_raw_text))

    extracted_emails = list(conv_dict.get("emails") or [])
    extracted_emails.extend(extract_emails_from_text(full_raw_text))

    attachments = list(conv_dict.get("attachments") or [])

    # 3. PII Masking (phones, credit cards, Aadhaar, PAN, OTP digits)
    raw_text_masked = mask_pii(full_raw_text)
    masked_messages = [
        Message(sender=m.sender, text=mask_pii(m.text), timestamp=m.timestamp)
        for m in raw_messages
    ]

    # 4. Text Preprocessing & Salient Keyword Extraction (F5, local)
    keywords = extract_keywords(raw_text_masked, top_n=5)

    # 5. Deterministic Security Rule Engine (F7, F8, F9-rules, E1)
    rule_security = evaluate_security_rules(
        text=raw_text_masked,
        explicit_urls=extracted_urls,
        explicit_emails=extracted_emails,
        explicit_attachments=attachments,
    )

    # 6, 7, 8. Gemini Call A (Customer), Call B (Security), Merge & Overrides (or Fallback)
    record = analyze_with_gemini_or_fallback(
        conversation_id=conv_id,
        channel=channel,
        created_at=created_at,
        raw_text_masked=raw_text_masked,
        messages=masked_messages,
        keywords=keywords,
        rule_security=rule_security,
        source=source,
    )

    # 9. Store in Database
    if persist:
        upsert_conversation(record)

    return record
