"""SQLite connection manager and lifecycle setup."""

import os
import sqlite3
from pathlib import Path
from app.core.config import settings
from app.core.logging import logger
from app.database.models import (
    CREATE_ANALYSIS_TABLE,
    CREATE_CONVERSATIONS_TABLE,
    CREATE_INDEXES,
)


def get_db_connection() -> sqlite3.Connection:
    """Creates a configured SQLite connection with foreign keys and row factory."""
    db_path = Path(settings.DATABASE_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(
        str(db_path),
        check_same_thread=False,
        timeout=10.0,
    )
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn


def init_db() -> None:
    """Initializes tables and indexes in SQLite."""
    logger.info(f"Initializing database at: {settings.DATABASE_PATH}")
    conn = get_db_connection()
    try:
        with conn:
            conn.execute(CREATE_CONVERSATIONS_TABLE)
            conn.execute(CREATE_ANALYSIS_TABLE)
            conn.executescript(CREATE_INDEXES)
        logger.info("Database initialized successfully with WAL mode and indexes")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    finally:
        conn.close()
