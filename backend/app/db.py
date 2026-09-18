"""
Section 9 & 13. Database Layer: Supabase (Postgres) with Automatic Local SQLite Fallback.
Provides unified persistence for conversations and messages, supporting local offline mode.
"""
import json
import os
import sqlite3
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone
from app.config import settings
from app.schemas import ConversationRecord, Message, SummaryDetail, SecurityDetail

# SQLite Local Database Path
SQLITE_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "local_cache.db")


def init_sqlite_db():
    """Initializes the local SQLite schema if Supabase is not available."""
    os.makedirs(os.path.dirname(SQLITE_DB_PATH), exist_ok=True)
    conn = sqlite3.connect(SQLITE_DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS conversations (
        id TEXT PRIMARY KEY,
        channel TEXT,
        created_at TEXT,
        source TEXT DEFAULT 'real',
        raw_text_masked TEXT NOT NULL,
        text_hash TEXT,
        category TEXT,
        issue_label TEXT,
        customer_issue TEXT,
        sentiment TEXT,
        emotion TEXT,
        emotion_intensity INTEGER,
        is_angry BOOLEAN,
        urgency TEXT,
        priority TEXT,
        priority_reason TEXT,
        resolution_status TEXT,
        resolution_reason TEXT,
        summary_json TEXT,
        keywords_json TEXT,
        threat_detected BOOLEAN,
        threat_type TEXT,
        social_engineering TEXT,
        techniques_json TEXT,
        suspicious_url BOOLEAN,
        suspicious_domain BOOLEAN,
        suspicious_email BOOLEAN,
        suspicious_attachment BOOLEAN,
        credential_request BOOLEAN,
        otp_request BOOLEAN,
        rule_score INTEGER,
        risk_level TEXT,
        risk_reasons_json TEXT,
        recommended_action TEXT,
        security_detail_json TEXT,
        messages_json TEXT,
        ai_mode TEXT,
        processing_ms INTEGER
    );
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cat ON conversations(category);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_issue ON conversations(issue_label);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_risk ON conversations(risk_level);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_prio ON conversations(priority);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_time ON conversations(created_at);")

    conn.commit()
    conn.close()


# Initialize SQLite on import
init_sqlite_db()


def is_supabase_enabled() -> bool:
    """Checks if valid Supabase credentials are configured."""
    return bool(settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY)


def get_supabase_client():
    """Returns Supabase client if enabled."""
    if not is_supabase_enabled():
        return None
    try:
        from supabase import create_client
        return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
    except Exception as e:
        return None


def row_to_record(row: Dict[str, Any]) -> ConversationRecord:
    """Converts a database row dictionary to a validated ConversationRecord."""
    summary_data = json.loads(row.get("summary_json") or "{}")
    keywords_data = json.loads(row.get("keywords_json") or "[]")
    security_data = json.loads(row.get("security_detail_json") or "{}")
    messages_data = json.loads(row.get("messages_json") or "[]")

    msg_objs = [Message(**m) for m in messages_data] if messages_data else []

    return ConversationRecord(
        conversation_id=row["id"],
        channel=row.get("channel") or "chat",
        created_at=row.get("created_at") or datetime.now(timezone.utc).isoformat(),
        customer_issue=row.get("customer_issue") or "",
        category=row.get("category") or "Other",
        issue_label=row.get("issue_label") or "Other",
        keywords=keywords_data,
        sentiment=row.get("sentiment") or "Neutral",
        emotion=row.get("emotion") or "Neutral",
        emotion_intensity=row.get("emotion_intensity") or 1,
        is_angry=bool(row.get("is_angry")),
        urgency=row.get("urgency") or "Low",
        priority=row.get("priority") or "Low",
        priority_reason=row.get("priority_reason") or "",
        resolution_status=row.get("resolution_status") or "Pending",
        resolution_reason=row.get("resolution_reason") or "",
        summary=SummaryDetail(**summary_data),
        security=SecurityDetail(**security_data),
        ai_mode=row.get("ai_mode") or "fallback",
        processing_ms=row.get("processing_ms") or 0,
        source=row.get("source") or "real",
        raw_text_masked=row.get("raw_text_masked") or "",
        messages=msg_objs,
    )


def upsert_conversation(record: ConversationRecord) -> None:
    """Saves or updates a conversation record in the database."""
    messages_dicts = [m.model_dump() for m in (record.messages or [])]

    # Try Supabase if configured
    sb = get_supabase_client()
    if sb:
        try:
            payload = {
                "id": record.conversation_id,
                "channel": record.channel,
                "created_at": record.created_at,
                "source": record.source,
                "raw_text_masked": record.raw_text_masked or "",
                "category": record.category,
                "issue_label": record.issue_label,
                "customer_issue": record.customer_issue,
                "sentiment": record.sentiment,
                "emotion": record.emotion,
                "emotion_intensity": record.emotion_intensity,
                "is_angry": record.is_angry,
                "urgency": record.urgency,
                "priority": record.priority,
                "priority_reason": record.priority_reason,
                "resolution_status": record.resolution_status,
                "resolution_reason": record.resolution_reason,
                "summary": record.summary.model_dump(),
                "keywords": record.keywords,
                "threat_detected": record.security.threat_detected,
                "threat_type": record.security.threat_type,
                "social_engineering": record.security.social_engineering,
                "techniques": record.security.techniques,
                "suspicious_url": record.security.suspicious_url,
                "suspicious_domain": record.security.suspicious_domain,
                "suspicious_email": record.security.suspicious_email,
                "suspicious_attachment": record.security.suspicious_attachment,
                "credential_request": record.security.credential_request,
                "otp_request": record.security.otp_request,
                "rule_score": record.security.rule_score,
                "risk_level": record.security.risk_level,
                "risk_reasons": record.security.risk_reasons,
                "recommended_action": record.security.recommended_action,
                "security_detail": record.security.model_dump(),
                "ai_mode": record.ai_mode,
                "processing_ms": record.processing_ms,
            }
            sb.table("conversations").upsert(payload).execute()
            return
        except Exception:
            pass  # Fall back to local SQLite

    # SQLite Persistence
    conn = sqlite3.connect(SQLITE_DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO conversations (
        id, channel, created_at, source, raw_text_masked, category, issue_label,
        customer_issue, sentiment, emotion, emotion_intensity, is_angry, urgency,
        priority, priority_reason, resolution_status, resolution_reason, summary_json,
        keywords_json, threat_detected, threat_type, social_engineering, techniques_json,
        suspicious_url, suspicious_domain, suspicious_email, suspicious_attachment,
        credential_request, otp_request, rule_score, risk_level, risk_reasons_json,
        recommended_action, security_detail_json, messages_json, ai_mode, processing_ms
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(id) DO UPDATE SET
        channel=excluded.channel,
        created_at=excluded.created_at,
        source=excluded.source,
        raw_text_masked=excluded.raw_text_masked,
        category=excluded.category,
        issue_label=excluded.issue_label,
        customer_issue=excluded.customer_issue,
        sentiment=excluded.sentiment,
        emotion=excluded.emotion,
        emotion_intensity=excluded.emotion_intensity,
        is_angry=excluded.is_angry,
        urgency=excluded.urgency,
        priority=excluded.priority,
        priority_reason=excluded.priority_reason,
        resolution_status=excluded.resolution_status,
        resolution_reason=excluded.resolution_reason,
        summary_json=excluded.summary_json,
        keywords_json=excluded.keywords_json,
        threat_detected=excluded.threat_detected,
        threat_type=excluded.threat_type,
        social_engineering=excluded.social_engineering,
        techniques_json=excluded.techniques_json,
        suspicious_url=excluded.suspicious_url,
        suspicious_domain=excluded.suspicious_domain,
        suspicious_email=excluded.suspicious_email,
        suspicious_attachment=excluded.suspicious_attachment,
        credential_request=excluded.credential_request,
        otp_request=excluded.otp_request,
        rule_score=excluded.rule_score,
        risk_level=excluded.risk_level,
        risk_reasons_json=excluded.risk_reasons_json,
        recommended_action=excluded.recommended_action,
        security_detail_json=excluded.security_detail_json,
        messages_json=excluded.messages_json,
        ai_mode=excluded.ai_mode,
        processing_ms=excluded.processing_ms;
    """, (
        record.conversation_id,
        record.channel,
        record.created_at,
        record.source or "real",
        record.raw_text_masked or "",
        record.category,
        record.issue_label,
        record.customer_issue,
        record.sentiment,
        record.emotion,
        record.emotion_intensity,
        1 if record.is_angry else 0,
        record.urgency,
        record.priority,
        record.priority_reason,
        record.resolution_status,
        record.resolution_reason,
        json.dumps(record.summary.model_dump()),
        json.dumps(record.keywords),
        1 if record.security.threat_detected else 0,
        record.security.threat_type,
        record.security.social_engineering,
        json.dumps(record.security.techniques),
        1 if record.security.suspicious_url else 0,
        1 if record.security.suspicious_domain else 0,
        1 if record.security.suspicious_email else 0,
        1 if record.security.suspicious_attachment else 0,
        1 if record.security.credential_request else 0,
        1 if record.security.otp_request else 0,
        record.security.rule_score,
        record.security.risk_level,
        json.dumps(record.security.risk_reasons),
        record.security.recommended_action,
        json.dumps(record.security.model_dump()),
        json.dumps(messages_dicts),
        record.ai_mode,
        record.processing_ms,
    ))

    conn.commit()
    conn.close()


def get_conversation(conv_id: str) -> Optional[ConversationRecord]:
    """Retrieves a single conversation by ID."""
    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM conversations WHERE id = ?", (conv_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None
    return row_to_record(dict(row))


def list_conversations(
    category: Optional[str] = None,
    priority: Optional[str] = None,
    risk: Optional[str] = None,
    sentiment: Optional[str] = None,
    status: Optional[str] = None,
    q: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
) -> Tuple[List[ConversationRecord], int]:
    """Retrieves paginated and filtered conversation records."""
    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    where_clauses = []
    params: List[Any] = []

    if category:
        where_clauses.append("category = ?")
        params.append(category)
    if priority:
        where_clauses.append("priority = ?")
        params.append(priority)
    if risk:
        where_clauses.append("risk_level = ?")
        params.append(risk)
    if sentiment:
        where_clauses.append("sentiment = ?")
        params.append(sentiment)
    if status:
        where_clauses.append("resolution_status = ?")
        params.append(status)
    if q:
        where_clauses.append("(raw_text_masked LIKE ? OR customer_issue LIKE ? OR id LIKE ?)")
        search_pattern = f"%{q}%"
        params.extend([search_pattern, search_pattern, search_pattern])

    where_str = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    # Count total matching
    count_query = f"SELECT COUNT(*) FROM conversations {where_str}"
    cursor.execute(count_query, params)
    total_count = cursor.fetchone()[0]

    # Fetch paginated results ordered by creation time descending
    offset = max(0, (page - 1) * limit)
    data_query = f"""
    SELECT * FROM conversations {where_str}
    ORDER BY created_at DESC
    LIMIT ? OFFSET ?
    """
    cursor.execute(data_query, params + [limit, offset])
    rows = cursor.fetchall()
    conn.close()

    records = [row_to_record(dict(r)) for r in rows]
    return records, total_count


def delete_conversation(conv_id: str) -> bool:
    """Deletes a conversation record (Privacy / GDPR compliance, Section 13)."""
    conn = sqlite3.connect(SQLITE_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM conversations WHERE id = ?", (conv_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


def get_all_conversations() -> List[ConversationRecord]:
    """Retrieves all conversation records for aggregations and dashboard stats."""
    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM conversations ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [row_to_record(dict(r)) for r in rows]
