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
    (e.g., sb_publishable_...), server-side Supabase is treated as disabled.
    """
    key = settings.SUPABASE_SERVICE_ROLE_KEY
    if not (settings.SUPABASE_URL and key):
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
        recommended_action, security_detail_json, messages_json, ai_mode, processing_ms
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
        processing_ms=excluded.processing_ms;
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

