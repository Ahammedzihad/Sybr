"""
SQLite read/write helpers for Conversation Intelligence.
Stores conversation records as JSON documents indexed by conversation_id.
"""

import json
import os
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

DB_FILE_DEFAULT = Path(__file__).resolve().parent / "data" / "conversations.db"


def get_db_path() -> str:
    """Returns active database path, respecting DATABASE_PATH environment variable."""
    env_path = os.getenv("DATABASE_PATH")
    if not env_path:
        return str(DB_FILE_DEFAULT)

    p = Path(env_path)
    if p.is_absolute() or p.exists():
        return str(p)

    backend_relative = Path(__file__).resolve().parent / env_path
    if backend_relative.exists():
        return str(backend_relative)

    return str(p)


def get_db_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Returns a SQLite connection."""
    active_path = db_path or get_db_path()
    Path(active_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(active_path)
    return conn


def init_db(db_path: Optional[str] = None) -> None:
    """
    Creates a 'conversations' table with columns:
    conversation_id (TEXT PRIMARY KEY) and record_json (TEXT).
    """
    with get_db_connection(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                conversation_id TEXT PRIMARY KEY,
                record_json TEXT NOT NULL
            )
        """)
        conn.commit()


def save(record: Dict[str, Any], db_path: Optional[str] = None) -> None:
    """Inserts or replaces a row, storing the record as JSON text."""
    init_db(db_path)
    conversation_id = str(record.get("conversation_id", ""))
    record_json = json.dumps(record)

    with get_db_connection(db_path) as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO conversations (conversation_id, record_json)
            VALUES (?, ?)
            """,
            (conversation_id, record_json),
        )
        conn.commit()


def get_all(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Reads all rows, parses record_json back to dict, and returns list."""
    init_db(db_path)
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT record_json FROM conversations")
        rows = cursor.fetchall()
        results = []
        for (raw_json,) in rows:
            try:
                results.append(json.loads(raw_json))
            except (json.JSONDecodeError, TypeError):
                continue
        return results


def get_by_id(conversation_id: str, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Fetches a single record by conversation_id."""
    init_db(db_path)
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT record_json FROM conversations WHERE conversation_id = ?",
            (conversation_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        try:
            return json.loads(row[0])
        except (json.JSONDecodeError, TypeError):
            return None
