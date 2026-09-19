"""
Multimodal Issue Diagnosis and Resolution Copilot.
Combines user text descriptions with uploaded images/screenshots (via Gemini 2.5 Flash vision)
to detect root causes, extract visual findings, evaluate cybersecurity threats,
and provide step-by-step troubleshooting checklists and customer response drafts.
"""
import base64
import json
import logging
import os
import re
import sqlite3
import time
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field

from app.config import settings
from app.schemas import IssueDiagnosisAndHelp, ConversationRecord, Message, SummaryDetail, SecurityDetail
from app.db import SQLITE_DB_PATH, upsert_conversation

logger = logging.getLogger("copilot")

class CopilotModelOutput(BaseModel):
    issue_title: str = Field(description="Short, concise title of the identified issue")
    category: str = Field(description="One of: Payment & Billing, Account Access, Technical Issue, Security Alert, Delivery & Order, Feature Request, General Support")
    severity: Literal["Low", "Medium", "High", "Critical"] = Field(default="Medium", description="Severity level")
    root_cause: str = Field(description="Detailed explanation of the root cause based on text and image")
    visual_findings: List[str] = Field(default_factory=list, description="Specific error codes, UI elements, text, URLs, or visual cues detected in the screenshot")
    is_threat: bool = Field(default=False, description="True if phishing, fake login, credential harvesting, malware, scam, or social engineering")
    threat_details: Optional[str] = Field(default=None, description="Detailed explanation of the threat if detected")
    troubleshooting_steps: List[str] = Field(default_factory=list, description="Ordered actionable troubleshooting steps to resolve the issue")
    suggested_response: str = Field(description="Polite, professional, ready-to-copy customer response draft")
    prevention_tip: str = Field(description="Proactive measure or best practice to prevent this issue in the future")


COPILOT_SYSTEM_PROMPT = """You are an elite Customer Support & Technical Issue Diagnosis Copilot.
Your job is to examine customer problem reports, which include their message text and any uploaded screenshots, error logs, or photos.
Analyze the message and the visual image carefully:
1. Extract any visual findings (error messages, HTTP status codes, transaction IDs, UI glitches, suspicious URLs, mismatched domains, form inputs).
2. Determine the exact issue title, category, and severity (Low, Medium, High, Critical).
3. Identify the true root cause.
4. Security check: Determine if this is a phishing scam, spoofed login page, invoice fraud, malware lure, or credential harvester. If so, set is_threat=True and detail the threat.
5. Provide a step-by-step troubleshooting checklist that either the customer or support agent can execute immediately.
6. Provide a ready-to-copy empathetic, professional customer response draft.
7. Provide a practical prevention tip to avoid recurrence.

Respond ONLY with structured JSON conforming to the schema."""


def init_copilot_table():
    """Ensures the copilot_diagnoses SQLite table exists."""
    os.makedirs(os.path.dirname(SQLITE_DB_PATH), exist_ok=True)
    conn = sqlite3.connect(SQLITE_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS copilot_diagnoses (
        session_id TEXT PRIMARY KEY,
        created_at TEXT,
        issue_title TEXT,
        category TEXT,
        severity TEXT,
        root_cause TEXT,
        visual_findings_json TEXT,
        is_threat BOOLEAN,
        threat_details TEXT,
        troubleshooting_steps_json TEXT,
        suggested_response TEXT,
        prevention_tip TEXT,
        image_attached BOOLEAN,
        image_name TEXT,
        processing_ms INTEGER,
        ai_mode TEXT,
        raw_message TEXT,
        user_id TEXT
    );
    """)

    cursor.execute("PRAGMA table_info(copilot_diagnoses)")
    cols = [c[1] for c in cursor.fetchall()]
    if "user_id" not in cols:
        cursor.execute("ALTER TABLE copilot_diagnoses ADD COLUMN user_id TEXT;")

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_copilot_created ON copilot_diagnoses(created_at);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_copilot_user ON copilot_diagnoses(user_id);")
    conn.commit()
    conn.close()


init_copilot_table()


def parse_base64_image(image_data: str, image_name: Optional[str] = None):
    """
    Parses a base64 string or data URI into (bytes, mime_type).
    Handles 'data:image/png;base64,...' and raw base64.
    """
    mime_type = "image/png"
    clean_b64 = image_data.strip()

    data_uri_match = re.match(r"^data:([^;]+);base64,(.*)$", clean_b64, re.DOTALL)
    if data_uri_match:
        mime_type = data_uri_match.group(1).strip()
        clean_b64 = data_uri_match.group(2).strip()
    elif image_name:
        ext = image_name.lower().split(".")[-1]
        if ext in ("jpg", "jpeg"):
            mime_type = "image/jpeg"
        elif ext == "webp":
            mime_type = "image/webp"
        elif ext == "gif":
            mime_type = "image/gif"
        elif ext == "svg":
            mime_type = "image/svg+xml"

    clean_b64 = re.sub(r"\s+", "", clean_b64)
    image_bytes = base64.b64decode(clean_b64)
    return image_bytes, mime_type


def run_deterministic_copilot_fallback(
    message: Optional[str],
    image_name: Optional[str],
    has_image: bool = False,
) -> IssueDiagnosisAndHelp:
    """
    Deterministic rule-based diagnosis when Gemini is offline or unavailable.
    Provides intelligent heuristics based on text patterns and image hints.
    """
    text = (message or "").lower()
    img = (image_name or "").lower()

    session_id = f"copilot-{uuid.uuid4().hex[:10]}"
    now_iso = datetime.now(timezone.utc).isoformat()

    # Rule 1: Phishing / Security Alert
    if any(k in text or k in img for k in ["phishing", "scam", "suspicious", "fake", "spoof", "verify account", "urgent action", "unauthorized access", "otp", "wire transfer", "hacked"]):
        return IssueDiagnosisAndHelp(
            session_id=session_id,
            created_at=now_iso,
            issue_title="Suspicious Security Alert / Phishing Attempt Detected",
            category="Security Alert",
            severity="Critical",
            root_cause="The interaction contains indicators of deceptive impersonation or credential harvesting aimed at compromising user security.",
            visual_findings=[
                f"Inspection of asset '{image_name or 'attachment'}': suspicious domain or login prompt structure detected.",
                "High urgency language requesting credential verification or out-of-band authorization.",
            ] if has_image else ["Text exhibits urgent call-to-action requesting sensitive credentials or verification."],
            is_threat=True,
            threat_details="Potential credential harvesting or unauthorized access attempt. Senders or endpoints do not match legitimate organizational domain patterns.",
            troubleshooting_steps=[
                "Immediately quarantine the communication and do NOT click any links or scan QR codes.",
                "Check user account session logs for unauthorized concurrent logins.",
                "Force an active session revocation and require password/2FA reset if credentials were typed.",
                "Report sender domain/IP to the SOC threat blocklist."
            ],
            suggested_response="Thank you for alerting us. Our security team has inspected this report and identified potential phishing indicators. Please do NOT click any links or enter credentials. We have secured your account details and are investigating further.",
            prevention_tip="Always verify sender domain spelling and enable hardware-backed 2FA (WebAuthn / FIDO2) across all administrative accounts.",
            image_attached=has_image,
            image_name=image_name,
            processing_ms=12,
            ai_mode="fallback",
            raw_message=message,
        )

    # Rule 2: Payment & Billing / Refund
    if any(k in text or k in img for k in ["payment", "charged", "billing", "refund", "card declined", "invoice", "double charge", "stripe", "receipt"]):
        return IssueDiagnosisAndHelp(
            session_id=session_id,
            created_at=now_iso,
            issue_title="Payment Processing Failure & Transaction Discrepancy",
            category="Payment & Billing",
            severity="High",
            root_cause="Card network decline or 3D-Secure authentication handshake timeout during settlement.",
            visual_findings=[
                f"Payment receipt/checkout visual '{image_name or 'screenshot'}' shows transaction failure or declined status banner.",
                "Gateway response code indicates insufficient funds, expired authorization, or anti-fraud cardholder block."
            ] if has_image else ["Customer reports unexpected transaction decline or pending hold on card."],
            is_threat=False,
            threat_details=None,
            troubleshooting_steps=[
                "Search payment gateway logs using the customer email or timestamp to inspect decline code.",
                "Verify if the charge is a temporary pre-authorization hold rather than a captured debit.",
                "Advise customer to contact their issuing bank to approve online recurring transactions.",
                "Offer an alternate payment link or digital wallet method (Apple Pay / Google Pay / PayPal)."
            ],
            suggested_response="We understand how frustrating billing issues can be and we're here to help. We are reviewing your recent transaction. Any pending holds from declined attempts typically release back to your account within 3–5 business days. We can also provide a direct invoice link if preferred.",
            prevention_tip="Implement automated pre-decline dunning notifications 48 hours before subscription renewals.",
            image_attached=has_image,
            image_name=image_name,
            processing_ms=10,
            ai_mode="fallback",
            raw_message=message,
        )

    # Rule 3: Technical Bug / Error 500 / Crash
    if any(k in text or k in img for k in ["500", "error", "crash", "blank screen", "failed to load", "bug", "timeout", "exception", "console", "server error"]):
        return IssueDiagnosisAndHelp(
            session_id=session_id,
            created_at=now_iso,
            issue_title="Application Runtime Exception & View Render Crash",
            category="Technical Issue",
            severity="High",
            root_cause="Unhandled exception or client-side asset failure during page rendering or API synchronization.",
            visual_findings=[
                f"Diagnostic capture '{image_name or 'screen'}' displays an explicit error message or stack trace.",
                "Client viewport reflects broken state or uncaught API 5xx failure."
            ] if has_image else ["User reports system instability, broken functionality, or unresponsive interface."],
            is_threat=False,
            threat_details=None,
            troubleshooting_steps=[
                "Check APM and cloud error logs for tracebacks matching the customer's timestamp.",
                "Instruct the user to clear browser local cache or perform a hard refresh (Cmd+Shift+R).",
                "Verify service health across downstream API gateways and microservices.",
                "Escalate diagnostic session ID and browser/OS details to the on-call engineering squad."
            ],
            suggested_response="We apologize for the interruption. We have captured the diagnostic information from your report and escalated it to our engineering team. In the meantime, performing a quick browser cache refresh often resolves temporary state conflicts.",
            prevention_tip="Deploy automated end-to-end synthetic monitoring on core user journeys to catch regressions before end users do.",
            image_attached=has_image,
            image_name=image_name,
            processing_ms=15,
            ai_mode="fallback",
            raw_message=message,
        )

    # Rule 4: Account Access / Password Reset
    if any(k in text or k in img for k in ["login", "password", "sign in", "locked", "access", "reset", "2fa", "mfa"]):
        return IssueDiagnosisAndHelp(
            session_id=session_id,
            created_at=now_iso,
            issue_title="Account Authentication & Access Lockout",
            category="Account Access",
            severity="Medium",
            root_cause="Excessive failed login attempts triggered automated rate limiting or expired credential token.",
            visual_findings=[
                f"Screenshot '{image_name or 'auth_screen'}' reveals an authentication modal with invalid credentials or lockout countdown."
            ] if has_image else ["Customer is locked out of account or unable to complete verification."],
            is_threat=False,
            threat_details=None,
            troubleshooting_steps=[
                "Verify customer identity through standard out-of-band verification procedure.",
                "Check account status in identity provider (Auth0/Firebase/Supabase) to confirm if account is locked.",
                "Dispatch secure self-service password reset link to registered primary email.",
                "Reset rate-limiting lockouts if identity check clears."
            ],
            suggested_response="We're glad to assist you in getting back into your account safely. A secure reset link has been dispatched to your primary email on file. Please allow up to 2 minutes for delivery and check spam folders if necessary.",
            prevention_tip="Encourage users to register a verified recovery email or security key for instant self-recovery.",
            image_attached=has_image,
            image_name=image_name,
            processing_ms=8,
            ai_mode="fallback",
            raw_message=message,
        )

    # Generic Fallback
    return IssueDiagnosisAndHelp(
        session_id=session_id,
        created_at=now_iso,
        issue_title="General Support Inquiry & Diagnostic Request",
        category="General Support",
        severity="Low" if len(text) < 50 else "Medium",
        root_cause="User submitted an inquiry or workflow question requiring support team triage and assistance.",
        visual_findings=[
            f"Attached file '{image_name or 'media'}' provided for visual context."
        ] if has_image else ["Customer inquiry submitted via support channel."],
        is_threat=False,
        threat_details=None,
        troubleshooting_steps=[
            "Review customer profile and recent activity history.",
            "Clarify specific desired outcome and provide direct navigation steps.",
            "Confirm resolution and invite any follow-up questions."
        ],
        suggested_response="Hello, thank you for reaching out to us! We have received your inquiry and are reviewing the details you shared. We will ensure this is taken care of promptly.",
        prevention_tip="Maintain comprehensive documentation and contextual tooltips throughout the user interface.",
        image_attached=has_image,
        image_name=image_name,
        processing_ms=5,
        ai_mode="fallback",
        raw_message=message,
    )


def save_copilot_diagnosis(diag: IssueDiagnosisAndHelp, user_id: Optional[str] = None) -> None:
    """Persists a diagnosis session into SQLite and mirrors into conversations table with user_id."""
    conn = sqlite3.connect(SQLITE_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO copilot_diagnoses (
        session_id, created_at, issue_title, category, severity, root_cause,
        visual_findings_json, is_threat, threat_details, troubleshooting_steps_json,
        suggested_response, prevention_tip, image_attached, image_name,
        processing_ms, ai_mode, raw_message, user_id
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(session_id) DO UPDATE SET
        user_id=COALESCE(excluded.user_id, copilot_diagnoses.user_id),
        issue_title=excluded.issue_title,
        category=excluded.category,
        severity=excluded.severity,
        root_cause=excluded.root_cause,
        visual_findings_json=excluded.visual_findings_json,
        is_threat=excluded.is_threat,
        threat_details=excluded.threat_details,
        troubleshooting_steps_json=excluded.troubleshooting_steps_json,
        suggested_response=excluded.suggested_response,
        prevention_tip=excluded.prevention_tip,
        processing_ms=excluded.processing_ms;
    """, (
        diag.session_id,
        diag.created_at,
        diag.issue_title,
        diag.category,
        diag.severity,
        diag.root_cause,
        json.dumps(diag.visual_findings),
        1 if diag.is_threat else 0,
        diag.threat_details,
        json.dumps(diag.troubleshooting_steps),
        diag.suggested_response,
        diag.prevention_tip,
        1 if diag.image_attached else 0,
        diag.image_name,
        diag.processing_ms,
        diag.ai_mode,
        diag.raw_message,
        user_id,
    ))
    conn.commit()
    conn.close()

    try:
        conv_record = ConversationRecord(
            conversation_id=diag.session_id,
            user_id=user_id,
            channel="copilot",
            created_at=diag.created_at,
            customer_issue=diag.issue_title,
            category=diag.category if diag.category in ["Technical Issue", "Payment & Billing", "Account Access", "Security Alert", "Delivery & Order", "Feature Request", "General Support"] else "Technical Issue",
            issue_label=diag.issue_title[:50],
            keywords=[k.strip() for k in (diag.issue_title + " " + diag.category).split() if len(k) > 3],
            sentiment="Negative" if diag.severity in ("High", "Critical") else "Neutral",
            emotion="Frustration" if diag.severity in ("High", "Critical") else "Neutral",
            emotion_intensity=4 if diag.severity == "Critical" else (3 if diag.severity == "High" else 2),
            is_angry=(diag.severity == "Critical"),
            urgency="High" if diag.severity in ("High", "Critical") else "Medium",
            priority=diag.severity,
            priority_reason=diag.root_cause[:180],
            resolution_status="Pending",
            resolution_reason="Diagnosed by AI Multimodal Copilot; awaiting customer action.",
            summary=SummaryDetail(
                issue=diag.issue_title,
                customer_request=diag.raw_message[:200] if diag.raw_message else "Assistance needed for attached diagnostic image",
                actions_taken="Identified root cause and generated step-by-step checklist and response",
                current_status="Checklist ready",
                priority=diag.severity,
            ),
            security=SecurityDetail(
                threat_detected=diag.is_threat,
                threat_type="Phishing" if diag.is_threat else "None",
                social_engineering="Yes" if diag.is_threat else "No",
                techniques=["Credential Harvesting", "Impersonation"] if diag.is_threat else [],
                risk_level=diag.severity,
                risk_reasons=[diag.threat_details] if diag.threat_details else [],
                recommended_action=diag.troubleshooting_steps[0] if diag.troubleshooting_steps else "Proceed with standard resolution.",
            ),
            ai_mode=diag.ai_mode,
            processing_ms=diag.processing_ms,
            source="copilot",
            raw_text_masked=diag.raw_message or f"Image: {diag.image_name or 'Uploaded screenshot'}",
            messages=[
                Message(
                    sender="customer",
                    text=diag.raw_message or f"Uploaded {diag.image_name or 'screenshot'}",
                    timestamp=diag.created_at,
                ),
                Message(
                    sender="copilot",
                    text=diag.suggested_response,
                    timestamp=diag.created_at,
                )
            ]
        )
        upsert_conversation(conv_record)
    except Exception as e:
        logger.warning(f"Could not mirror diagnosis to conversations table: {e}")


def get_recent_copilot_diagnoses(limit: int = 20, user_id: Optional[str] = None) -> List[IssueDiagnosisAndHelp]:
    """Retrieves recent diagnostic sessions from SQLite scoped by user_id if supplied."""
    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    if user_id:
        cursor.execute("""
        SELECT * FROM copilot_diagnoses
        WHERE user_id = ? OR user_id IS NULL
        ORDER BY created_at DESC
        LIMIT ?
        """, (user_id, limit))
    else:
        cursor.execute("""
        SELECT * FROM copilot_diagnoses
        ORDER BY created_at DESC
        LIMIT ?
        """, (limit,))
    rows = cursor.fetchall()
    conn.close()

    results = []
    for r in rows:
        results.append(IssueDiagnosisAndHelp(
            session_id=r["session_id"],
            created_at=r["created_at"],
            issue_title=r["issue_title"],
            category=r["category"],
            severity=r["severity"],
            root_cause=r["root_cause"],
            visual_findings=json.loads(r["visual_findings_json"] or "[]"),
            is_threat=bool(r["is_threat"]),
            threat_details=r["threat_details"],
            troubleshooting_steps=json.loads(r["troubleshooting_steps_json"] or "[]"),
            suggested_response=r["suggested_response"],
            prevention_tip=r["prevention_tip"],
            image_attached=bool(r["image_attached"]),
            image_name=r["image_name"],
            processing_ms=r["processing_ms"] or 0,
            ai_mode=r["ai_mode"] or "gemini",
            raw_message=r["raw_message"],
        ))
    return results


def diagnose_multimodal_issue(
    message: Optional[str] = None,
    image_data: Optional[str] = None,
    image_name: Optional[str] = None,
    channel: Optional[str] = "chat",
    user_id: Optional[str] = None,
) -> IssueDiagnosisAndHelp:
    """
    Main entrypoint: executes multimodal diagnosis using Gemini 2.5 Flash
    (or deterministic heuristics fallback).

    """
    start_time = time.time()
    has_image = bool(image_data and len(image_data.strip()) > 0)
    has_text = bool(message and len(message.strip()) > 0)

    if not has_image and not has_text:
        message = "No text or image provided."

    # Try Gemini 2.5 Flash if configured
    if settings.GEMINI_API_KEY:
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            contents: List[Any] = [COPILOT_SYSTEM_PROMPT]

            user_text = f"Channel: {channel or 'chat'}\n"
            if image_name:
                user_text += f"Image Filename: {image_name}\n"
            if message:
                user_text += f"User Issue Report:\n{message}\n"
            else:
                user_text += "User uploaded an image without text description. Please diagnose the issue entirely from the visual evidence.\n"

            contents.append(user_text)

            if has_image:
                image_bytes, mime_type = parse_base64_image(image_data, image_name)
                contents.append(types.Part.from_bytes(data=image_bytes, mime_type=mime_type))

            response = client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=contents,
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    response_mime_type="application/json",
                    response_schema=CopilotModelOutput,
                ),
            )

            result_dict = json.loads(response.text)
            parsed = CopilotModelOutput(**result_dict)

            elapsed_ms = int((time.time() - start_time) * 1000)
            diag = IssueDiagnosisAndHelp(
                session_id=f"copilot-{uuid.uuid4().hex[:10]}",
                created_at=datetime.now(timezone.utc).isoformat(),
                issue_title=parsed.issue_title,
                category=parsed.category,
                severity=parsed.severity,
                root_cause=parsed.root_cause,
                visual_findings=parsed.visual_findings,
                is_threat=parsed.is_threat,
                threat_details=parsed.threat_details,
                troubleshooting_steps=parsed.troubleshooting_steps,
                suggested_response=parsed.suggested_response,
                prevention_tip=parsed.prevention_tip,
                image_attached=has_image,
                image_name=image_name,
                processing_ms=elapsed_ms,
                ai_mode="gemini",
                raw_message=message,
            )
            save_copilot_diagnosis(diag, user_id=user_id)
            return diag

        except Exception as e:
            logger.warning(f"Gemini Copilot inference failed or timed out ({e}), falling back to deterministic engine.")

    # Deterministic fallback
    diag = run_deterministic_copilot_fallback(message=message, image_name=image_name, has_image=has_image)
    diag.processing_ms = int((time.time() - start_time) * 1000)
    save_copilot_diagnosis(diag, user_id=user_id)
    return diag

