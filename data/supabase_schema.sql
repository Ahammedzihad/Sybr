-- =============================================================================
-- SybrV2 Supabase PostgreSQL Schema
-- Run this script in your Supabase Dashboard -> SQL Editor
-- =============================================================================

CREATE TABLE IF NOT EXISTS public.conversations (
    id TEXT PRIMARY KEY,
    channel TEXT DEFAULT 'chat',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    source TEXT DEFAULT 'real',
    raw_text_masked TEXT NOT NULL DEFAULT '',
    text_hash TEXT,
    category TEXT DEFAULT 'Other',
    issue_label TEXT DEFAULT 'Other',
    customer_issue TEXT DEFAULT '',
    sentiment TEXT DEFAULT 'Neutral',
    emotion TEXT DEFAULT 'Neutral',
    emotion_intensity INTEGER DEFAULT 1,
    is_angry BOOLEAN DEFAULT FALSE,
    urgency TEXT DEFAULT 'Low',
    priority TEXT DEFAULT 'Low',
    priority_reason TEXT DEFAULT '',
    resolution_status TEXT DEFAULT 'Pending',
    resolution_reason TEXT DEFAULT '',
    summary JSONB DEFAULT '{}'::jsonb,
    keywords JSONB DEFAULT '[]'::jsonb,
    threat_detected BOOLEAN DEFAULT FALSE,
    threat_type TEXT DEFAULT 'None',
    social_engineering TEXT DEFAULT 'No',
    techniques JSONB DEFAULT '[]'::jsonb,
    suspicious_url BOOLEAN DEFAULT FALSE,
    suspicious_domain BOOLEAN DEFAULT FALSE,
    suspicious_email BOOLEAN DEFAULT FALSE,
    suspicious_attachment BOOLEAN DEFAULT FALSE,
    credential_request BOOLEAN DEFAULT FALSE,
    otp_request BOOLEAN DEFAULT FALSE,
    rule_score INTEGER DEFAULT 0,
    risk_level TEXT DEFAULT 'Low',
    risk_reasons JSONB DEFAULT '[]'::jsonb,
    recommended_action TEXT DEFAULT '',
    security_detail JSONB DEFAULT '{}'::jsonb,
    messages JSONB DEFAULT '[]'::jsonb,
    ai_mode TEXT DEFAULT 'fallback',
    processing_ms INTEGER DEFAULT 0
);

-- Query optimization indexes
CREATE INDEX IF NOT EXISTS idx_conversations_category ON public.conversations(category);
CREATE INDEX IF NOT EXISTS idx_conversations_issue ON public.conversations(issue_label);
CREATE INDEX IF NOT EXISTS idx_conversations_risk ON public.conversations(risk_level);
CREATE INDEX IF NOT EXISTS idx_conversations_priority ON public.conversations(priority);
CREATE INDEX IF NOT EXISTS idx_conversations_created_at ON public.conversations(created_at DESC);

-- Enable Row Level Security (RLS)
ALTER TABLE public.conversations ENABLE ROW LEVEL SECURITY;

-- Allow service_role full access (FastAPI backend uses service_role key)
CREATE POLICY "Allow service_role full access"
ON public.conversations
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);
