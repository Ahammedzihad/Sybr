-- =============================================================================
-- SybrV2 Supabase PostgreSQL Schema
-- Run this script in your Supabase Dashboard -> SQL Editor
-- =============================================================================

CREATE TABLE IF NOT EXISTS public.conversations (
    id TEXT PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
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

-- Ensure user_id column exists if table was previously created without it
ALTER TABLE public.conversations 
ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE;

-- Query optimization indexes
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON public.conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_category ON public.conversations(category);
CREATE INDEX IF NOT EXISTS idx_conversations_issue ON public.conversations(issue_label);
CREATE INDEX IF NOT EXISTS idx_conversations_risk ON public.conversations(risk_level);
CREATE INDEX IF NOT EXISTS idx_conversations_priority ON public.conversations(priority);
CREATE INDEX IF NOT EXISTS idx_conversations_created_at ON public.conversations(created_at DESC);

-- Enable Row Level Security (RLS)
ALTER TABLE public.conversations ENABLE ROW LEVEL SECURITY;

-- Allow service_role full access (FastAPI backend uses service_role key)
DROP POLICY IF EXISTS "Allow service_role full access" ON public.conversations;
CREATE POLICY "Allow service_role full access"
ON public.conversations
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- Allow authenticated users to view/modify only their own conversations
DROP POLICY IF EXISTS "Users can access own conversations" ON public.conversations;
CREATE POLICY "Users can access own conversations"
ON public.conversations
FOR ALL
TO authenticated
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

-- =============================================================================
-- User Profiles & Role-Based Access Control (RBAC)
-- =============================================================================

CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT NOT NULL,
    display_name TEXT DEFAULT '',
    role TEXT NOT NULL DEFAULT 'customer' CHECK (role IN ('customer', 'admin')),
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'disabled')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Ensure columns exist if table was previously created
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS display_name TEXT DEFAULT '';
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS role TEXT NOT NULL DEFAULT 'customer';
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'active';

CREATE INDEX IF NOT EXISTS idx_profiles_role ON public.profiles(role);
CREATE INDEX IF NOT EXISTS idx_profiles_email ON public.profiles(email);

-- Enable RLS on profiles
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

-- Allow service_role full access to profiles
DROP POLICY IF EXISTS "Allow service_role full access to profiles" ON public.profiles;
CREATE POLICY "Allow service_role full access to profiles"
ON public.profiles
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- Allow users to view their own profile
DROP POLICY IF EXISTS "Users can view own profile" ON public.profiles;
CREATE POLICY "Users can view own profile"
ON public.profiles
FOR SELECT
TO authenticated
USING (auth.uid() = id);

-- Allow users to update only their own profile details (excluding role changes)
DROP POLICY IF EXISTS "Users can update own display profile" ON public.profiles;
CREATE POLICY "Users can update own display profile"
ON public.profiles
FOR UPDATE
TO authenticated
USING (auth.uid() = id)
WITH CHECK (auth.uid() = id);

-- =============================================================================
-- Security Audit Logs Table
-- =============================================================================

CREATE TABLE IF NOT EXISTS public.audit_logs (
    id TEXT PRIMARY KEY,
    actor_user_id TEXT NOT NULL,
    actor_email TEXT DEFAULT '',
    action TEXT NOT NULL,
    target_resource_id TEXT DEFAULT '',
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_actor ON public.audit_logs(actor_user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON public.audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON public.audit_logs(created_at DESC);

-- Enable RLS on audit_logs
ALTER TABLE public.audit_logs ENABLE ROW LEVEL SECURITY;

-- Allow service_role full access to audit_logs
DROP POLICY IF EXISTS "Allow service_role full access to audit_logs" ON public.audit_logs;
CREATE POLICY "Allow service_role full access to audit_logs"
ON public.audit_logs
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);
