"""Data access repository for conversations and security analyses."""

import json
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
import sqlite3

from app.core.logging import logger
from app.database.database import get_db_connection
from app.schemas.analysis import AnalysisResult
from app.schemas.conversation import ConversationRecord
from app.schemas.dashboard import DashboardStats


class ConversationRepository:
    """Repository abstraction over SQLite for conversation persistence and aggregation."""

    def __init__(self, conn: Optional[sqlite3.Connection] = None):
        self._conn = conn

    def _get_connection(self) -> sqlite3.Connection:
        if self._conn:
            return self._conn
        return get_db_connection()

    def save(
        self,
        sender: str,
        subject: str,
        message: str,
        urls: List[str],
        analysis: AnalysisResult,
        security_indicators: List[str],
    ) -> ConversationRecord:
        """Persists a conversation and its analysis result."""
        conv_id = f"conv-{uuid.uuid4().hex[:8]}"
        analysis_id = f"an-{uuid.uuid4().hex[:8]}"
        created_at = datetime.now(timezone.utc).isoformat()

        conn = self._get_connection()
        should_close = self._conn is None

        try:
            with conn:
                conn.execute(
                    """
                    INSERT INTO conversations (id, sender, subject, message, urls, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        conv_id,
                        sender,
                        subject,
                        message,
                        json.dumps(urls),
                        created_at,
                    ),
                )
                conn.execute(
                    """
                    INSERT INTO analysis_results (
                        id, conversation_id, category, sentiment, emotion, priority,
                        summary, resolution_status, threat_type, social_engineering,
                        suspicious_url, risk_level, recommended_action, security_indicators, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        analysis_id,
                        conv_id,
                        analysis.category,
                        analysis.sentiment,
                        analysis.emotion,
                        analysis.priority,
                        analysis.summary,
                        analysis.resolution_status,
                        analysis.threat_type,
                        1 if analysis.social_engineering else 0,
                        1 if analysis.suspicious_url else 0,
                        analysis.risk_level,
                        analysis.recommended_action,
                        json.dumps(security_indicators),
                        created_at,
                    ),
                )

            return ConversationRecord(
                id=conv_id,
                sender=sender,
                subject=subject,
                message=message,
                urls=urls,
                created_at=created_at,
                analysis=analysis,
                security_indicators=security_indicators,
            )
        finally:
            if should_close:
                conn.close()

    def get_all(
        self,
        page: int = 1,
        limit: int = 20,
        risk_level: Optional[str] = None,
    ) -> Tuple[List[ConversationRecord], int]:
        """Retrieves paginated conversation records with optional risk level filter."""
        conn = self._get_connection()
        should_close = self._conn is None
        offset = (page - 1) * limit

        try:
            # Query count
            count_query = """
                SELECT COUNT(*) as total
                FROM conversations c
                JOIN analysis_results a ON c.id = a.conversation_id
            """
            params: List[str] = []
            if risk_level:
                count_query += " WHERE a.risk_level = ?"
                params.append(risk_level)

            cursor = conn.execute(count_query, params)
            total = cursor.fetchone()["total"]

            # Query records
            select_query = """
                SELECT 
                    c.id, c.sender, c.subject, c.message, c.urls, c.created_at,
                    a.category, a.sentiment, a.emotion, a.priority, a.summary,
                    a.resolution_status, a.threat_type, a.social_engineering,
                    a.suspicious_url, a.risk_level, a.recommended_action, a.security_indicators
                FROM conversations c
                JOIN analysis_results a ON c.id = a.conversation_id
            """
            if risk_level:
                select_query += " WHERE a.risk_level = ?"
            select_query += " ORDER BY c.created_at DESC LIMIT ? OFFSET ?"

            query_params = params + [limit, offset]
            cursor = conn.execute(select_query, query_params)
            rows = cursor.fetchall()

            items = []
            for row in rows:
                try:
                    urls_list = json.loads(row["urls"])
                except Exception:
                    urls_list = []
                try:
                    sec_ind = json.loads(row["security_indicators"])
                except Exception:
                    sec_ind = []

                analysis = AnalysisResult(
                    category=row["category"],
                    sentiment=row["sentiment"],
                    emotion=row["emotion"],
                    priority=row["priority"],
                    summary=row["summary"],
                    resolution_status=row["resolution_status"],
                    threat_type=row["threat_type"],
                    social_engineering=bool(row["social_engineering"]),
                    suspicious_url=bool(row["suspicious_url"]),
                    risk_level=row["risk_level"],
                    recommended_action=row["recommended_action"],
                )

                items.append(
                    ConversationRecord(
                        id=row["id"],
                        sender=row["sender"],
                        subject=row["subject"],
                        message=row["message"],
                        urls=urls_list,
                        created_at=row["created_at"],
                        analysis=analysis,
                        security_indicators=sec_ind,
                    )
                )

            return items, total
        finally:
            if should_close:
                conn.close()

    def get_dashboard_stats(self) -> DashboardStats:
        """Aggregates security metrics for dashboard visualizations."""
        conn = self._get_connection()
        should_close = self._conn is None

        try:
            total_cursor = conn.execute("SELECT COUNT(*) as count FROM conversations")
            total = total_cursor.fetchone()["count"]

            if total == 0:
                return DashboardStats()

            # High risk count
            high_risk_cursor = conn.execute(
                "SELECT COUNT(*) as count FROM analysis_results WHERE risk_level IN ('High', 'Critical')"
            )
            high_risk = high_risk_cursor.fetchone()["count"]

            # Resolved count
            resolved_cursor = conn.execute(
                "SELECT COUNT(*) as count FROM analysis_results WHERE resolution_status IN ('Resolved', 'Dismissed')"
            )
            resolved = resolved_cursor.fetchone()["count"]

            # Pending count
            pending_cursor = conn.execute(
                "SELECT COUNT(*) as count FROM analysis_results WHERE resolution_status IN ('Flagged', 'Blocked', 'Under Review')"
            )
            pending = pending_cursor.fetchone()["count"]

            # Distribution helper
            def _get_distribution(column: str) -> Dict[str, int]:
                cur = conn.execute(
                    f"SELECT {column} as name, COUNT(*) as cnt FROM analysis_results GROUP BY {column}"
                )
                return {row["name"]: row["cnt"] for row in cur.fetchall() if row["name"]}

            return DashboardStats(
                total_conversations=total,
                high_risk_count=high_risk,
                resolved_count=resolved,
                pending_count=pending,
                categories=_get_distribution("category"),
                sentiments=_get_distribution("sentiment"),
                emotions=_get_distribution("emotion"),
                risk_levels=_get_distribution("risk_level"),
                threat_types=_get_distribution("threat_type"),
            )
        finally:
            if should_close:
                conn.close()
