"""SQL database schema definitions."""

CREATE_CONVERSATIONS_TABLE = """
CREATE TABLE IF NOT EXISTS conversations (
    id TEXT PRIMARY KEY,
    sender TEXT NOT NULL,
    subject TEXT NOT NULL,
    message TEXT NOT NULL,
    urls TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""

CREATE_ANALYSIS_TABLE = """
CREATE TABLE IF NOT EXISTS analysis_results (
    id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL,
    category TEXT NOT NULL,
    sentiment TEXT NOT NULL,
    emotion TEXT NOT NULL,
    priority TEXT NOT NULL,
    summary TEXT NOT NULL,
    resolution_status TEXT NOT NULL,
    threat_type TEXT NOT NULL,
    social_engineering INTEGER NOT NULL,
    suspicious_url INTEGER NOT NULL,
    risk_level TEXT NOT NULL,
    recommended_action TEXT NOT NULL,
    security_indicators TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
);
"""

CREATE_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_conversations_created_at ON conversations(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_analysis_risk_level ON analysis_results(risk_level);
CREATE INDEX IF NOT EXISTS idx_analysis_category ON analysis_results(category);
"""
