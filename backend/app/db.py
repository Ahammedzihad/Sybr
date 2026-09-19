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
        user_id TEXT,
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

    # Dynamic SQLite migration for existing databases
    cursor.execute("PRAGMA table_info(conversations)")
    existing_cols = [col[1] for col in cursor.fetchall()]
    
    new_cols = [
        ("user_id", "TEXT"),
        ("original_text", "TEXT"),
        ("processing_status", "TEXT DEFAULT 'AI Analyzed'"),
        ("assigned_to", "TEXT"),
        ("assigned_at", "TEXT"),
        ("reviewed_by", "TEXT"),
        ("reviewed_at", "TEXT"),
        ("escalated_at", "TEXT"),
        ("resolved_at", "TEXT"),
        ("confidence_json", "TEXT DEFAULT '{}'"),
        ("ai_explanation_json", "TEXT DEFAULT '{}'"),
        ("needs_human_review", "BOOLEAN DEFAULT 0"),
        ("review_reason", "TEXT DEFAULT ''"),
        ("human_overrides_json", "TEXT"),
        ("is_human_reviewed", "BOOLEAN DEFAULT 0"),
        ("internal_notes_json", "TEXT DEFAULT '[]'"),
        ("draft_response", "TEXT"),
    ]
    for col_name, col_type in new_cols:
        if col_name not in existing_cols:
            cursor.execute(f"ALTER TABLE conversations ADD COLUMN {col_name} {col_type};")

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cat ON conversations(category);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_issue ON conversations(issue_label);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_risk ON conversations(risk_level);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_prio ON conversations(priority);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_time ON conversations(created_at);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_user ON conversations(user_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_proc_status ON conversations(processing_status);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_assigned_to ON conversations(assigned_to);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_needs_review ON conversations(needs_human_review);")


    # Section 11 & RBAC: User Profiles & Security Audit Logs
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS profiles (
        id TEXT PRIMARY KEY,
        email TEXT NOT NULL,
        display_name TEXT DEFAULT '',
        role TEXT NOT NULL DEFAULT 'customer',
        status TEXT NOT NULL DEFAULT 'active',
        created_at TEXT,
        updated_at TEXT
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        id TEXT PRIMARY KEY,
        actor_user_id TEXT NOT NULL,
        actor_email TEXT DEFAULT '',
        action TEXT NOT NULL,
        target_resource_id TEXT DEFAULT '',
        metadata_json TEXT DEFAULT '{}',
        created_at TEXT
    );
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_profiles_role ON profiles(role);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_profiles_email ON profiles(email);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_created ON audit_logs(created_at DESC);")

    now_iso = datetime.now(timezone.utc).isoformat()
    # Seed default profiles if not present for local development / testing
    cursor.execute("SELECT COUNT(*) FROM profiles WHERE id = 'demo-user-001'")
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            "INSERT INTO profiles (id, email, display_name, role, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("demo-user-001", "demo@sybr.local", "Demo Customer", "customer", "active", now_iso, now_iso)
        )
    cursor.execute("SELECT COUNT(*) FROM profiles WHERE id = 'admin-user-001'")
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            "INSERT INTO profiles (id, email, display_name, role, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("admin-user-001", "admin@sybr.local", "System Administrator", "admin", "active", now_iso, now_iso)
        )

    conn.commit()
    conn.close()


# Initialize SQLite on import
init_sqlite_db()


def is_supabase_enabled() -> bool:
    """
    Checks if valid Supabase server credentials are configured.
    Detects key types safely: if the service-role key has a publishable prefix
    (e.g., sb_publishable_...) or contains placeholder strings, server-side Supabase is treated as disabled.
    """
    key = settings.SUPABASE_SERVICE_ROLE_KEY
    if not (settings.SUPABASE_URL and key):
        return False
    if "your-project-ref" in settings.SUPABASE_URL or "your_supabase" in key or "your-anon-key" in key:
        return False
    if key.startswith("sb_publishable_") or key.startswith("pk."):
        return False
    return True


def get_supabase_client():
    """Returns Supabase client if enabled."""
    if not is_supabase_enabled():
        return None
    try:
        from supabase import create_client
        return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
    except Exception:
        return None


def _parse_json_field(val: Any, default: Any) -> Any:
    if val is None:
        return default
    if isinstance(val, (dict, list)):
        return val
    if isinstance(val, str):
        try:
            return json.loads(val)
        except Exception:
            return default
    return default


def row_to_record(row: Dict[str, Any]) -> ConversationRecord:
    """Converts a database row dictionary to a validated ConversationRecord."""
    summary_data = _parse_json_field(row.get("summary") or row.get("summary_json"), {})
    keywords_data = _parse_json_field(row.get("keywords") or row.get("keywords_json"), [])
    security_data = _parse_json_field(row.get("security_detail") or row.get("security_detail_json"), {})
    messages_data = _parse_json_field(row.get("messages") or row.get("messages_json"), [])
    confidence_data = _parse_json_field(row.get("confidence") or row.get("confidence_json"), {})
    ai_explanation_data = _parse_json_field(row.get("ai_explanation") or row.get("ai_explanation_json"), {})
    human_overrides_data = _parse_json_field(row.get("human_overrides") or row.get("human_overrides_json"), None)
    internal_notes_data = _parse_json_field(row.get("internal_notes") or row.get("internal_notes_json"), [])

    msg_objs = [Message(**m) if isinstance(m, dict) else m for m in messages_data] if messages_data else []

    return ConversationRecord(
        conversation_id=row["id"],
        user_id=row.get("user_id"),
        channel=row.get("channel") or "chat",
        created_at=str(row.get("created_at") or datetime.now(timezone.utc).isoformat()),
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
        summary=SummaryDetail(**summary_data) if isinstance(summary_data, dict) else SummaryDetail(),
        security=SecurityDetail(**security_data) if isinstance(security_data, dict) else SecurityDetail(),
        ai_mode=row.get("ai_mode") or "fallback",
        processing_ms=row.get("processing_ms") or 0,
        source=row.get("source") or "real",
        raw_text_masked=row.get("raw_text_masked") or "",
        messages=msg_objs,
        processing_status=row.get("processing_status") or "AI Analyzed",
        assigned_to=row.get("assigned_to"),
        assigned_at=row.get("assigned_at"),
        reviewed_by=row.get("reviewed_by"),
        reviewed_at=row.get("reviewed_at"),
        escalated_at=row.get("escalated_at"),
        resolved_at=row.get("resolved_at"),
        confidence=confidence_data,
        ai_explanation=ai_explanation_data,
        needs_human_review=bool(row.get("needs_human_review")),
        review_reason=row.get("review_reason"),
        is_human_reviewed=bool(row.get("is_human_reviewed")),
        human_overrides=human_overrides_data,
        internal_notes=internal_notes_data if isinstance(internal_notes_data, list) else [],
        draft_response=row.get("draft_response"),
    )



def upsert_conversation(record: ConversationRecord) -> None:
    """Saves or updates a conversation record in Supabase and local SQLite."""
    messages_dicts = [m.model_dump() for m in (record.messages or [])]

    # Try Supabase if configured
    sb = get_supabase_client()
    if sb:
        try:
            payload = {
                "id": record.conversation_id,
                "user_id": record.user_id,
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
                "messages": messages_dicts,
                "ai_mode": record.ai_mode,
                "processing_ms": record.processing_ms,
                "processing_status": record.processing_status,
                "assigned_to": record.assigned_to,
                "assigned_at": record.assigned_at,
                "reviewed_by": record.reviewed_by,
                "reviewed_at": record.reviewed_at,
                "escalated_at": record.escalated_at,
                "resolved_at": record.resolved_at,
                "confidence": record.confidence,
                "ai_explanation": record.ai_explanation,
                "needs_human_review": record.needs_human_review,
                "review_reason": record.review_reason,
                "is_human_reviewed": record.is_human_reviewed,
                "human_overrides": record.human_overrides,
                "internal_notes": record.internal_notes,
                "draft_response": record.draft_response,
            }
            sb.table("conversations").upsert(payload).execute()
        except Exception:
            pass  # Fall back to local SQLite

    # SQLite Persistence (local dual-backup)
    conn = sqlite3.connect(SQLITE_DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO conversations (
        id, user_id, channel, created_at, source, raw_text_masked, category, issue_label,
        customer_issue, sentiment, emotion, emotion_intensity, is_angry, urgency,
        priority, priority_reason, resolution_status, resolution_reason, summary_json,
        keywords_json, threat_detected, threat_type, social_engineering, techniques_json,
        suspicious_url, suspicious_domain, suspicious_email, suspicious_attachment,
        credential_request, otp_request, rule_score, risk_level, risk_reasons_json,
        recommended_action, security_detail_json, messages_json, ai_mode, processing_ms,
        processing_status, assigned_to, assigned_at, reviewed_by, reviewed_at,
        escalated_at, resolved_at, confidence_json, ai_explanation_json,
        needs_human_review, review_reason, is_human_reviewed, human_overrides_json,
        internal_notes_json, draft_response
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(id) DO UPDATE SET
        user_id=COALESCE(excluded.user_id, conversations.user_id),
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
        processing_ms=excluded.processing_ms,
        processing_status=excluded.processing_status,
        assigned_to=excluded.assigned_to,
        assigned_at=excluded.assigned_at,
        reviewed_by=excluded.reviewed_by,
        reviewed_at=excluded.reviewed_at,
        escalated_at=excluded.escalated_at,
        resolved_at=excluded.resolved_at,
        confidence_json=excluded.confidence_json,
        ai_explanation_json=excluded.ai_explanation_json,
        needs_human_review=excluded.needs_human_review,
        review_reason=excluded.review_reason,
        is_human_reviewed=excluded.is_human_reviewed,
        human_overrides_json=excluded.human_overrides_json,
        internal_notes_json=excluded.internal_notes_json,
        draft_response=excluded.draft_response;
    """, (
        record.conversation_id,
        record.user_id,
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
        record.processing_status,
        record.assigned_to,
        record.assigned_at,
        record.reviewed_by,
        record.reviewed_at,
        record.escalated_at,
        record.resolved_at,
        json.dumps(record.confidence or {}),
        json.dumps(record.ai_explanation or {}),
        1 if record.needs_human_review else 0,
        record.review_reason or "",
        1 if record.is_human_reviewed else 0,
        json.dumps(record.human_overrides) if record.human_overrides else None,
        json.dumps(record.internal_notes or []),
        record.draft_response,
    ))

    conn.commit()
    conn.close()


def get_conversation(conv_id: str, user_id: Optional[str] = None) -> Optional[ConversationRecord]:
    """Retrieves a single conversation by ID from Supabase or local SQLite, scoped by user_id if present."""
    sb = get_supabase_client()
    if sb:
        try:
            query = sb.table("conversations").select("*").eq("id", conv_id)
            if user_id:
                query = query.eq("user_id", user_id)
            res = query.execute()
            if res.data and len(res.data) > 0:
                return row_to_record(res.data[0])
        except Exception:
            pass

    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if user_id:
        cursor.execute("SELECT * FROM conversations WHERE id = ? AND (user_id = ? OR user_id IS NULL)", (conv_id, user_id))
    else:
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
    user_id: Optional[str] = None,
) -> Tuple[List[ConversationRecord], int]:
    """Retrieves paginated and filtered conversation records from Supabase or local SQLite, scoped by user_id if present."""
    sb = get_supabase_client()
    if sb:
        try:
            query = sb.table("conversations").select("*", count="exact")
            if user_id:
                query = query.eq("user_id", user_id)
            if category:
                query = query.eq("category", category)
            if priority:
                query = query.eq("priority", priority)
            if risk:
                query = query.eq("risk_level", risk)
            if sentiment:
                query = query.eq("sentiment", sentiment)
            if status:
                query = query.eq("resolution_status", status)
            if q:
                search_q = f"%{q}%"
                query = query.or_(f"raw_text_masked.ilike.{search_q},customer_issue.ilike.{search_q},id.ilike.{search_q}")

            offset = max(0, (page - 1) * limit)
            res = query.order("created_at", desc=True).range(offset, offset + limit - 1).execute()
            records = [row_to_record(r) for r in (res.data or [])]
            total_count = res.count if res.count is not None else len(records)
            if total_count > 0:
                return records, total_count
        except Exception:
            pass

    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    where_clauses = []
    params: List[Any] = []

    if user_id:
        where_clauses.append("(user_id = ? OR user_id IS NULL)")
        params.append(user_id)
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


def delete_conversation(conv_id: str, user_id: Optional[str] = None) -> bool:
    """Deletes a conversation record (Privacy / GDPR compliance, Section 13), scoped by user_id if present."""
    sb_deleted = False
    sb = get_supabase_client()
    if sb:
        try:
            query = sb.table("conversations").delete().eq("id", conv_id)
            if user_id:
                query = query.eq("user_id", user_id)
            res = query.execute()
            sb_deleted = bool(res.data)
        except Exception:
            pass

    conn = sqlite3.connect(SQLITE_DB_PATH)
    cursor = conn.cursor()
    if user_id:
        cursor.execute("DELETE FROM conversations WHERE id = ? AND (user_id = ? OR user_id IS NULL)", (conv_id, user_id))
    else:
        cursor.execute("DELETE FROM conversations WHERE id = ?", (conv_id,))
    deleted = (cursor.rowcount > 0) or sb_deleted
    conn.commit()
    conn.close()
    return deleted


def get_all_conversations(user_id: Optional[str] = None) -> List[ConversationRecord]:
    """Retrieves all conversation records for aggregations and dashboard stats from Supabase or local SQLite."""
    sb = get_supabase_client()
    if sb:
        try:
            query = sb.table("conversations").select("*").order("created_at", desc=True)
            if user_id:
                query = query.eq("user_id", user_id)
            res = query.execute()
            if res.data:
                return [row_to_record(r) for r in res.data]
        except Exception:
            pass

    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    if user_id:
        cursor.execute("SELECT * FROM conversations WHERE (user_id = ? OR user_id IS NULL) ORDER BY created_at DESC", (user_id,))
    else:
        cursor.execute("SELECT * FROM conversations ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [row_to_record(dict(r)) for r in rows]


# ---------------------------------------------------------------------------
# Section 11 & RBAC: Profiles & Audit Log Persistence
# ---------------------------------------------------------------------------

def get_profile(user_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves a user profile by ID from Supabase or local SQLite."""
    sb = get_supabase_client()
    if sb:
        try:
            res = sb.table("profiles").select("*").eq("id", user_id).execute()
            if res.data and len(res.data) > 0:
                return res.data[0]
        except Exception:
            pass

    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM profiles WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None


def upsert_profile(
    user_id: str,
    email: str,
    display_name: str = "",
    role: str = "customer",
    status: str = "active",
) -> Dict[str, Any]:
    """Saves or updates a user profile in Supabase and local SQLite."""
    now_iso = datetime.now(timezone.utc).isoformat()
    record = {
        "id": user_id,
        "email": email,
        "display_name": display_name or email.split("@")[0],
        "role": role,
        "status": status,
        "updated_at": now_iso,
    }

    sb = get_supabase_client()
    if sb:
        try:
            sb.table("profiles").upsert(record).execute()
        except Exception:
            pass

    conn = sqlite3.connect(SQLITE_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO profiles (id, email, display_name, role, status, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(id) DO UPDATE SET
        email=excluded.email,
        display_name=COALESCE(NULLIF(excluded.display_name, ''), profiles.display_name),
        role=excluded.role,
        status=excluded.status,
        updated_at=excluded.updated_at;
    """, (
        record["id"],
        record["email"],
        record["display_name"],
        record["role"],
        record["status"],
        now_iso,
        now_iso,
    ))
    conn.commit()
    conn.close()
    return record


def list_profiles() -> List[Dict[str, Any]]:
    """Retrieves all user profiles for administrative management."""
    sb = get_supabase_client()
    if sb:
        try:
            res = sb.table("profiles").select("*").order("created_at", desc=True).execute()
            if res.data:
                return res.data
        except Exception:
            pass

    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM profiles ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_profile_role(target_id: str, new_role: str, actor_id: str) -> Dict[str, Any]:
    """
    Updates the role of a user profile.
    Protects against demoting or removing the final administrator (Section 24 & 77).
    """
    profiles = list_profiles()
    target = next((p for p in profiles if p["id"] == target_id), None)
    if not target:
        raise ValueError(f"User profile with ID '{target_id}' not found.")

    if target.get("role") == "admin" and new_role != "admin":
        active_admins = [p for p in profiles if p.get("role") == "admin" and p.get("status") == "active"]
        if len(active_admins) <= 1:
            raise ValueError("Cannot demote the last remaining administrator.")

    now_iso = datetime.now(timezone.utc).isoformat()
    sb = get_supabase_client()
    if sb:
        try:
            sb.table("profiles").update({"role": new_role, "updated_at": now_iso}).eq("id", target_id).execute()
        except Exception:
            pass

    conn = sqlite3.connect(SQLITE_DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE profiles SET role = ?, updated_at = ? WHERE id = ?",
        (new_role, now_iso, target_id)
    )
    conn.commit()
    conn.close()

    # Log audit event
    log_audit_event(
        actor_user_id=actor_id,
        action="ROLE_CHANGE",
        target_resource_id=target_id,
        metadata={"old_role": target.get("role"), "new_role": new_role}
    )

    target["role"] = new_role
    target["updated_at"] = now_iso
    return target


def log_audit_event(
    actor_user_id: str,
    action: str,
    target_resource_id: str = "",
    actor_email: str = "",
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """Records an administrative security audit log entry (Section 27 & 79)."""
    import uuid
    log_id = f"audit-{uuid.uuid4().hex[:12]}"
    now_iso = datetime.now(timezone.utc).isoformat()
    meta_json = json.dumps(metadata or {})

    sb = get_supabase_client()
    if sb:
        try:
            sb.table("audit_logs").insert({
                "id": log_id,
                "actor_user_id": actor_user_id,
                "actor_email": actor_email,
                "action": action,
                "target_resource_id": target_resource_id,
                "metadata": metadata or {},
                "created_at": now_iso,
            }).execute()
        except Exception:
            pass

    conn = sqlite3.connect(SQLITE_DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO audit_logs (id, actor_user_id, actor_email, action, target_resource_id, metadata_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (log_id, actor_user_id, actor_email, action, target_resource_id, meta_json, now_iso)
    )
    conn.commit()
    conn.close()


def list_audit_logs(limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieves chronological security audit entries for administrative review."""
    sb = get_supabase_client()
    if sb:
        try:
            res = sb.table("audit_logs").select("*").order("created_at", desc=True).limit(limit).execute()
            if res.data:
                return res.data
        except Exception:
            pass

    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()

    result = []
    for r in rows:
        d = dict(r)
        d["metadata"] = _parse_json_field(d.get("metadata_json") or d.get("metadata"), {})
        result.append(d)
    return result


# ---------------------------------------------------------------------------
# Section 13, 14, 15: Admin Operational Review, Workflow & Internal Notes
# ---------------------------------------------------------------------------

def update_conversation_review(
    conv_id: str,
    reviewer_id: str,
    reviewer_email: str,
    overrides: Dict[str, Any],
    reason: str = "Manual administrative review & calibration",
) -> Optional[ConversationRecord]:
    """
    Applies human review corrections to a conversation record (Section 13 & 15).
    Preserves original AI values, records timestamped audit log and human overrides history.
    """
    record = get_conversation(conv_id)
    if not record:
        return None

    now_iso = datetime.now(timezone.utc).isoformat()
    existing_overrides = record.human_overrides or {}
    history = existing_overrides.get("history", [])

    # Store baseline original AI classification if this is the first review
    original = existing_overrides.get("original", {
        "category": record.category,
        "issue_label": record.issue_label,
        "priority": record.priority,
        "risk_level": record.security.risk_level,
        "threat_detected": record.security.threat_detected,
        "resolution_status": record.resolution_status,
    })

    correction_entry = {
        "reviewer_id": reviewer_id,
        "reviewer_email": reviewer_email,
        "timestamp": now_iso,
        "reason": reason,
        "changes": overrides,
    }
    history.append(correction_entry)

    new_overrides = {
        "original": original,
        "last_correction": correction_entry,
        "history": history,
    }

    # Apply overrides to record
    if "category" in overrides and overrides["category"]:
        record.category = overrides["category"]
    if "issue_label" in overrides and overrides["issue_label"]:
        record.issue_label = overrides["issue_label"]
    if "priority" in overrides and overrides["priority"]:
        record.priority = overrides["priority"]
    if "resolution_status" in overrides and overrides["resolution_status"]:
        record.resolution_status = overrides["resolution_status"]
    if "risk_level" in overrides and overrides["risk_level"]:
        record.security.risk_level = overrides["risk_level"]
        record.security.threat_detected = overrides["risk_level"] in ("High", "Critical")

    record.is_human_reviewed = True
    record.reviewed_by = reviewer_id
    record.reviewed_at = now_iso
    record.processing_status = "Human Reviewed"
    record.needs_human_review = False
    record.human_overrides = new_overrides

    # Persist updated record
    upsert_conversation(record)

    # Security Audit Trail
    log_audit_event(
        actor_user_id=reviewer_id,
        actor_email=reviewer_email,
        action="CONVERSATION_REVIEW_CORRECTION",
        target_resource_id=conv_id,
        metadata={"reason": reason, "changes": overrides},
    )

    return record


def update_conversation_status(
    conv_id: str,
    actor_id: str,
    actor_email: str = "",
    processing_status: Optional[str] = None,
    resolution_status: Optional[str] = None,
    assigned_to: Optional[str] = None,
) -> Optional[ConversationRecord]:
    """
    Updates operational workflow status, resolution state, and assignee (Section 15).
    """
    record = get_conversation(conv_id)
    if not record:
        return None

    now_iso = datetime.now(timezone.utc).isoformat()
    audit_changes = {}

    if processing_status and processing_status != record.processing_status:
        audit_changes["processing_status"] = {"old": record.processing_status, "new": processing_status}
        record.processing_status = processing_status
        if processing_status == "Escalated":
            record.escalated_at = now_iso

    if resolution_status and resolution_status != record.resolution_status:
        audit_changes["resolution_status"] = {"old": record.resolution_status, "new": resolution_status}
        record.resolution_status = resolution_status
        if resolution_status == "Resolved":
            record.resolved_at = now_iso

    if assigned_to is not None and assigned_to != record.assigned_to:
        audit_changes["assigned_to"] = {"old": record.assigned_to, "new": assigned_to}
        record.assigned_to = assigned_to if assigned_to != "" else None
        record.assigned_at = now_iso if assigned_to else None

    upsert_conversation(record)

    if audit_changes:
        log_audit_event(
            actor_user_id=actor_id,
            actor_email=actor_email,
            action="CONVERSATION_STATUS_CHANGE",
            target_resource_id=conv_id,
            metadata=audit_changes,
        )

    return record


def add_conversation_internal_note(
    conv_id: str,
    author_id: str,
    author_name: str,
    note_text: str,
    author_email: str = "",
) -> Optional[Dict[str, Any]]:
    """
    Appends an internal admin note to a conversation record (Section 14 & 15).
    Strictly private to administrators, never returned to customer endpoints.
    """
    record = get_conversation(conv_id)
    if not record:
        return None

    import uuid
    note_id = f"note-{uuid.uuid4().hex[:8]}"
    now_iso = datetime.now(timezone.utc).isoformat()

    note_entry = {
        "id": note_id,
        "author_id": author_id,
        "author_name": author_name or "Administrator",
        "text": note_text.strip(),
        "created_at": now_iso,
    }

    if not isinstance(record.internal_notes, list):
        record.internal_notes = []
    record.internal_notes.append(note_entry)

    upsert_conversation(record)

    log_audit_event(
        actor_user_id=author_id,
        actor_email=author_email,
        action="INTERNAL_NOTE_ADDED",
        target_resource_id=conv_id,
        metadata={"note_id": note_id, "snippet": note_text[:60]},
    )

    return note_entry


def set_conversation_needs_review(
    conv_id: str,
    actor_id: str,
    actor_email: str = "",
    reason: str = "Flagged for administrative review",
) -> Optional[ConversationRecord]:
    """Flags a conversation for manual human review queue."""
    record = get_conversation(conv_id)
    if not record:
        return None

    record.needs_human_review = True
    record.review_reason = reason
    record.processing_status = "Needs Review"
    upsert_conversation(record)

    log_audit_event(
        actor_user_id=actor_id,
        actor_email=actor_email,
        action="FLAGGED_FOR_REVIEW",
        target_resource_id=conv_id,
        metadata={"reason": reason},
    )

    return record


# ---------------------------------------------------------------------------
# Section 16 & 17: Admin Intelligence Analytics & Category Drill-Down
# ---------------------------------------------------------------------------

def get_admin_category_analytics() -> Dict[str, Any]:
    """Computes comprehensive category aggregates for Section 16."""
    all_convs = get_all_conversations(user_id=None)
    total = len(all_convs)
    if total == 0:
        return {"total_conversations": 0, "categories": []}

    from collections import defaultdict
    cat_counts = defaultdict(int)
    cat_unresolved = defaultdict(int)
    cat_critical = defaultdict(int)
    cat_threats = defaultdict(int)

    for c in all_convs:
        cat = c.category or "Other"
        cat_counts[cat] += 1
        if c.resolution_status in ("Unresolved", "Pending"):
            cat_unresolved[cat] += 1
        if c.priority == "Critical" or c.security.risk_level == "Critical":
            cat_critical[cat] += 1
        if c.security.threat_detected:
            cat_threats[cat] += 1

    categories_list = []
    for cat, count in sorted(cat_counts.items(), key=lambda x: x[1], reverse=True):
        categories_list.append({
            "category": cat,
            "count": count,
            "percentage": round((count / total) * 100, 1),
            "unresolved_count": cat_unresolved[cat],
            "critical_count": cat_critical[cat],
            "threat_count": cat_threats[cat],
        })

    return {
        "total_conversations": total,
        "categories": categories_list,
    }


def get_admin_security_analytics() -> Dict[str, Any]:
    """Computes threat intelligence analytics for Section 17 Security Center."""
    all_convs = get_all_conversations(user_id=None)
    threat_convs = [c for c in all_convs if c.security.threat_detected]

    from collections import Counter
    threat_types = Counter()
    techniques = Counter()
    domain_counts = Counter()
    email_domain_counts = Counter()

    for c in threat_convs:
        if c.security.threat_type and c.security.threat_type != "None":
            threat_types[c.security.threat_type] += 1
        for tech in (c.security.techniques or []):
            techniques[tech] += 1
        for u in (c.security.urls or []):
            if u.domain:
                domain_counts[u.domain] += 1
        for e in (c.security.emails or []):
            if e.domain:
                email_domain_counts[e.domain] += 1

    top_domains = [{"domain": d, "count": c} for d, c in domain_counts.most_common(10)]
    top_senders = [{"domain": d, "count": c} for d, c in email_domain_counts.most_common(10)]

    critical_count = sum(1 for c in threat_convs if c.security.risk_level == "Critical")
    high_count = sum(1 for c in threat_convs if c.security.risk_level == "High")

    return {
        "total_threats": len(threat_convs),
        "critical_count": critical_count,
        "high_count": high_count,
        "threat_types": dict(threat_types),
        "techniques": dict(techniques),
        "top_domains": top_domains,
        "top_senders": top_senders,
        "top_attachments": [],
    }


def get_admin_ai_performance() -> Dict[str, Any]:
    """Computes AI observability and monitoring metrics for Section 17."""
    all_convs = get_all_conversations(user_id=None)
    total = len(all_convs)
    if total == 0:
        return {
            "total_analyzed": 0,
            "gemini_count": 0,
            "fallback_count": 0,
            "fallback_rate": 0.0,
            "avg_processing_ms": 0,
            "human_corrections_count": 0,
            "human_correction_rate": 0.0,
            "review_queue_count": 0,
            "model_name": settings.GEMINI_MODEL,
            "prompt_injection_signals_caught": 0,
        }

    gemini_count = sum(1 for c in all_convs if c.ai_mode == "gemini")
    fallback_count = sum(1 for c in all_convs if c.ai_mode == "fallback")
    human_corrections = sum(1 for c in all_convs if c.is_human_reviewed)
    review_queue = sum(1 for c in all_convs if c.needs_human_review)
    total_ms = sum(c.processing_ms or 0 for c in all_convs)

    prompt_injections = sum(
        1 for c in all_convs
        if "Prompt Injection" in (c.security.techniques or [])
    )

    return {
        "total_analyzed": total,
        "gemini_count": gemini_count,
        "fallback_count": fallback_count,
        "fallback_rate": round((fallback_count / total) * 100, 1) if total else 0.0,
        "avg_processing_ms": int(total_ms / total) if total else 0,
        "human_corrections_count": human_corrections,
        "human_correction_rate": round((human_corrections / total) * 100, 1) if total else 0.0,
        "review_queue_count": review_queue,
        "model_name": settings.GEMINI_MODEL,
        "prompt_injection_signals_caught": prompt_injections,
    }


def list_customer_overviews() -> List[Dict[str, Any]]:
    """Returns directory of customers with ticket volume and threat statistics."""
    profiles = list_profiles()
    customers = [p for p in profiles if p.get("role") == "customer"]
    all_convs = get_all_conversations(user_id=None)

    result = []
    for cust in customers:
        cid = cust["id"]
        c_convs = [c for c in all_convs if c.user_id == cid]
        unresolved = sum(1 for c in c_convs if c.resolution_status in ("Unresolved", "Pending"))
        critical = sum(1 for c in c_convs if c.priority == "Critical" or c.security.risk_level == "Critical")
        last_act = c_convs[0].created_at if c_convs else cust.get("created_at") or datetime.now(timezone.utc).isoformat()

        result.append({
            "customer_id": cid,
            "email": cust["email"],
            "display_name": cust.get("display_name") or cust["email"].split("@")[0],
            "conversation_count": len(c_convs),
            "unresolved_count": unresolved,
            "critical_count": critical,
            "last_activity": last_act,
        })

    return result


def get_conversations_by_user(user_id: str) -> List[ConversationRecord]:
    """Retrieves all conversation records belonging to a given user."""
    return get_all_conversations(user_id=user_id)

