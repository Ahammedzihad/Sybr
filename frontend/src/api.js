/**
 * Centralized API Client for SybrV2.
 * Communicates strictly with the FastAPI backend, supporting Supabase Authentication,
 * Role-Based Access Control (Customer vs Admin), Copilot Studio, Gmail Integration,
 * and built-in Offline Demo Mode.
 */
import { createClient } from '@supabase/supabase-js';

const API_BASE = import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_URL || (import.meta.env.DEV ? 'http://localhost:8000' : '');

const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL;
const SUPABASE_ANON_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY;

// Direct client-side Supabase client (only uses public/anon key; never service_role)
export const supabase = (SUPABASE_URL && SUPABASE_ANON_KEY)
  ? createClient(SUPABASE_URL, SUPABASE_ANON_KEY)
  : null;

// Listen to Supabase Auth state changes if configured
if (supabase) {
  supabase.auth.onAuthStateChange(async (event, session) => {
    if (event === 'SIGNED_IN' && session) {
      try {
        const res = await fetch(`${API_BASE}/auth/me`, {
          headers: { Authorization: `Bearer ${session.access_token}` },
        });
        if (res.ok) {
          const user = await res.json();
          setAuthSession(session.access_token, user, false);
          return;
        }
      } catch (err) {
        // quiet fallback
      }
      const u = session.user;
      setAuthSession(session.access_token, {
        id: u.id,
        email: u.email,
        display_name: u.user_metadata?.display_name || u.email?.split('@')[0],
        role: u.user_metadata?.role || 'customer',
        status: 'active',
      }, false);
    } else if (event === 'SIGNED_OUT') {
      clearAuthSession();
    }
  });
}

// ---------------------------------------------------------------------------
// Offline & Auth Token Management
// ---------------------------------------------------------------------------

export function isOfflineMode() {
  const stored = localStorage.getItem('sybr_offline_mode');
  if (stored !== null) {
    return stored === 'true';
  }
  // In production without an explicit live backend URL, default to safe offline demo mode
  if (import.meta.env.PROD && !API_BASE) {
    return true;
  }
  return false;
}

export function setOfflineMode(enabled) {
  localStorage.setItem('sybr_offline_mode', enabled ? 'true' : 'false');
  window.dispatchEvent(new Event('offline-mode-changed'));
}

export function getAuthToken() {
  return localStorage.getItem('sybr_auth_token');
}

export function getCurrentUser() {
  const data = localStorage.getItem('sybr_user_data');
  if (!data) return null;
  try {
    return JSON.parse(data);
  } catch {
    return null;
  }
}

export function getUserRole() {
  const user = getCurrentUser();
  return user?.role || 'customer';
}

export function isAdmin() {
  return getUserRole() === 'admin';
}

export function setAuthSession(token, user, isDemo = false) {
  localStorage.setItem('sybr_auth_token', token);
  localStorage.setItem('sybr_user_data', JSON.stringify({ ...user, is_demo: isDemo }));
  window.dispatchEvent(new Event('auth-state-changed'));
}

export function clearAuthSession() {
  localStorage.removeItem('sybr_auth_token');
  localStorage.removeItem('sybr_user_data');
  window.dispatchEvent(new Event('auth-state-changed'));
}

export function isAuthenticated() {
  return Boolean(getAuthToken());
}

function getHeaders(extra = {}) {
  const headers = { ...extra };
  const token = getAuthToken();
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

async function handleResponse(res) {
  if (res.status === 401) {
    clearAuthSession();
    throw new Error('Session expired. Please log in again.');
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Request failed with status ${res.status}`);
  }
  return await res.json();
}

async function fetchDemoCache() {
  const res = await fetch('/demo-cache.json');
  return await res.json();
}

// ---------------------------------------------------------------------------
// Authentication API
// ---------------------------------------------------------------------------

export async function login(email, password) {
  // 1. Supabase Auth if client-side credentials are configured
  if (supabase) {
    const { data: sbData, error: sbErr } = await supabase.auth.signInWithPassword({
      email: email.trim(),
      password,
    });
    if (sbErr) {
      throw new Error(sbErr.message || 'Invalid email or password.');
    }
    if (sbData?.session) {
      try {
        const profileRes = await fetch(`${API_BASE}/auth/me`, {
          headers: { Authorization: `Bearer ${sbData.session.access_token}` },
        });
        if (profileRes.ok) {
          const userProfile = await profileRes.json();
          setAuthSession(sbData.session.access_token, userProfile, false);
          return { access_token: sbData.session.access_token, user: userProfile, is_demo: false };
        }
      } catch (e) {
        // quiet fallback
      }
      const u = sbData.user;
      const userProfile = {
        id: u.id,
        email: u.email,
        display_name: u.user_metadata?.display_name || u.email?.split('@')[0],
        role: u.user_metadata?.role || 'customer',
        status: 'active',
      };
      setAuthSession(sbData.session.access_token, userProfile, false);
      return { access_token: sbData.session.access_token, user: userProfile, is_demo: false };
    }
  }

  // 2. FastAPI Backend /auth/login
  if (!isOfflineMode() && API_BASE) {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });

    const data = await handleResponse(res);
    setAuthSession(data.access_token, data.user, data.is_demo);
    return data;
  }

  // 3. Demo Mode Fallback (Deterministic offline simulation)
  const isDemoAdmin = email.toLowerCase().includes('admin');
  const demoUser = {
    id: isDemoAdmin ? 'admin-user-001' : 'demo-user-001',
    email,
    display_name: isDemoAdmin ? 'System Administrator' : 'Demo Customer',
    role: isDemoAdmin ? 'admin' : 'customer',
    status: 'active',
    is_demo: true,
  };
  const token = isDemoAdmin ? 'admin-demo-token' : 'demo-token';
  setAuthSession(token, demoUser, true);
  return { access_token: token, user: demoUser, is_demo: true };
}

export async function signup(email, password, displayName = '') {
  // Public signups always receive role 'customer'
  if (supabase) {
    const { data, error } = await supabase.auth.signUp({
      email: email.trim(),
      password,
      options: {
        data: {
          display_name: displayName || email.split('@')[0],
          role: 'customer',
        },
      },
    });
    if (error) {
      throw new Error(error.message);
    }
    return {
      status: 'ok',
      message: 'Account created! Please check your email inbox to verify your account.',
    };
  }

  if (!isOfflineMode() && API_BASE) {
    const res = await fetch(`${API_BASE}/auth/signup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, display_name: displayName }),
    });
    return await handleResponse(res);
  }

  return {
    status: 'ok',
    message: 'Account registered successfully in Demo Mode. Default role: customer.',
  };
}

export async function resetPassword(email) {
  if (supabase) {
    await supabase.auth.resetPasswordForEmail(email.trim(), {
      redirectTo: `${window.location.origin}/reset-password`,
    });
    return {
      status: 'ok',
      message: 'If this email is registered, instructions to reset your password have been sent.',
    };
  }

  if (!isOfflineMode() && API_BASE) {
    const res = await fetch(`${API_BASE}/auth/reset-password`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email }),
    });
    return await handleResponse(res);
  }

  return {
    status: 'ok',
    message: 'If this email is registered, instructions to reset your password have been sent.',
  };
}

export async function updatePassword(newPassword) {
  if (supabase) {
    const { error } = await supabase.auth.updateUser({ password: newPassword });
    if (error) throw new Error(error.message);
    return { status: 'ok', message: 'Password updated successfully.' };
  }
  return { status: 'ok', message: 'Password updated in Demo Mode.' };
}

export async function logout() {
  try {
    if (supabase) {
      await supabase.auth.signOut();
    }
    if (!isOfflineMode() && isAuthenticated() && API_BASE) {
      await fetch(`${API_BASE}/auth/logout`, {
        method: 'POST',
        headers: getHeaders(),
      });
    }
  } catch (err) {
    // quiet logout
  } finally {
    clearAuthSession();
  }
}

export async function fetchMe() {
  if (isOfflineMode()) {
    return getCurrentUser() || { id: 'demo-user-001', email: 'demo@sybr.local', role: 'customer', is_demo: true };
  }
  const res = await fetch(`${API_BASE}/auth/me`, {
    headers: getHeaders(),
  });
  return await handleResponse(res);
}

// ---------------------------------------------------------------------------
// Section 15 & 16: Customer Portal APIs
// ---------------------------------------------------------------------------

export async function fetchCustomerDashboard() {
  if (isOfflineMode()) {
    const data = await fetchDemoCache();
    const convs = data.conversations || [];
    return {
      total_my_conversations: convs.length,
      my_threats_detected: convs.filter(c => c.security?.threat_detected).length,
      my_pending_reviews: convs.filter(c => c.resolution_status === 'Pending').length,
      my_resolved_tickets: convs.filter(c => c.resolution_status === 'Resolved').length,
      recent_activity: convs.slice(0, 8).map(c => ({
        id: c.conversation_id,
        created_at: c.created_at,
        issue: c.customer_issue || c.raw_text_masked?.slice(0, 60),
        category: c.category,
        priority: c.priority,
        risk_level: c.security?.risk_level || 'Low',
        threat_detected: c.security?.threat_detected || false,
      })),
    };
  }
  const res = await fetch(`${API_BASE}/customer/dashboard`, {
    headers: getHeaders(),
  });
  return await handleResponse(res);
}

// ---------------------------------------------------------------------------
// Section 21-27: Admin Portal APIs
// ---------------------------------------------------------------------------

export async function fetchAdminDashboard() {
  if (isOfflineMode()) {
    return {
      total_users: 12,
      total_customers: 10,
      total_admins: 2,
      total_platform_conversations: 48,
      total_platform_threats: 14,
      high_risk_threats: 6,
      ai_status: {
        provider: 'Google Gemini',
        model: 'gemini-2.5-flash',
        fallback: 'Rule-Based Deterministic Engine',
        status: 'online',
      },
      database_status: {
        mode: 'supabase_postgresql',
        rls_enforced: true,
      },
      recent_audit_logs: [
        {
          id: 'audit-001',
          actor_user_id: 'admin-user-001',
          actor_email: 'admin@sybr.local',
          action: 'LOGIN',
          target_resource_id: 'admin-user-001',
          created_at: new Date().toISOString(),
          metadata: {},
        }
      ],
    };
  }
  const res = await fetch(`${API_BASE}/admin/dashboard`, {
    headers: getHeaders(),
  });
  return await handleResponse(res);
}

export async function fetchAdminUsers() {
  if (isOfflineMode()) {
    return [
      { id: 'admin-user-001', email: 'admin@sybr.local', display_name: 'System Administrator', role: 'admin', status: 'active', created_at: new Date().toISOString() },
      { id: 'demo-user-001', email: 'demo@sybr.local', display_name: 'Demo Customer', role: 'customer', status: 'active', created_at: new Date().toISOString() },
      { id: 'demo-user-002', email: 'alice@enterprise.com', display_name: 'Alice Smith', role: 'customer', status: 'active', created_at: new Date().toISOString() },
    ];
  }
  const res = await fetch(`${API_BASE}/admin/users`, {
    headers: getHeaders(),
  });
  return await handleResponse(res);
}

export async function updateUserRole(userId, newRole) {
  if (isOfflineMode()) {
    return { id: userId, role: newRole };
  }
  const res = await fetch(`${API_BASE}/admin/users/${userId}/role`, {
    method: 'PATCH',
    headers: getHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({ role: newRole }),
  });
  return await handleResponse(res);
}

export async function fetchAdminAuditLogs(limit = 50) {
  if (isOfflineMode()) {
    return [
      {
        id: 'audit-demo-1',
        actor_user_id: 'admin-user-001',
        actor_email: 'admin@sybr.local',
        action: 'ROLE_CHANGE',
        target_resource_id: 'demo-user-002',
        metadata: { old_role: 'customer', new_role: 'admin' },
        created_at: new Date().toISOString(),
      }
    ];
  }
  const res = await fetch(`${API_BASE}/admin/audit-logs?limit=${limit}`, {
    headers: getHeaders(),
  });
  return await handleResponse(res);
}

export async function fetchAdminConversations(params = {}) {
  if (isOfflineMode()) {
    return await fetchConversations(params);
  }
  const query = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '') query.append(k, v);
  });
  const res = await fetch(`${API_BASE}/admin/conversations?${query.toString()}`, {
    headers: getHeaders(),
  });
  return await handleResponse(res);
}


// ---------------------------------------------------------------------------
// Telemetry & Health
// ---------------------------------------------------------------------------

export async function fetchHealth() {
  if (isOfflineMode()) {
    return {
      status: 'ok',
      ai_mode: 'fallback',
      model: 'demo-cache',
      database: 'local_cache',
      version: '1.0.0',
    };
  }
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error('Health check failed');
  return await res.json();
}

// ---------------------------------------------------------------------------
// Dashboard & Analytics
// ---------------------------------------------------------------------------

export async function fetchDashboard() {
  if (isOfflineMode()) {
    const data = await fetchDemoCache();
    return {
      kpis: data.kpis,
      sentiment_distribution: data.sentiment_distribution,
      category_distribution: data.category_distribution,
      issue_frequency: data.issue_frequency,
      risk_distribution: data.risk_distribution,
      emotion_distribution: data.emotion_distribution,
      daily_trend: data.daily_trend,
    };
  }
  const res = await fetch(`${API_BASE}/dashboard`, {
    headers: getHeaders(),
  });
  return await handleResponse(res);
}

export async function fetchIssues() {
  if (isOfflineMode()) {
    const data = await fetchDemoCache();
    return { total_conversations: data.kpis.total_conversations, issues: data.issue_frequency };
  }
  const res = await fetch(`${API_BASE}/issues`, {
    headers: getHeaders(),
  });
  return await handleResponse(res);
}

export async function fetchTrends(bucket = 'day') {
  if (isOfflineMode()) {
    const data = await fetchDemoCache();
    return data.daily_trend.map(d => ({
      period: d.date,
      total: d.total,
      complaints: d.complaints,
      threats: d.threats,
      unresolved: 1,
    }));
  }
  const res = await fetch(`${API_BASE}/trends?bucket=${bucket}`, {
    headers: getHeaders(),
  });
  return await handleResponse(res);
}

export async function fetchSystemEval() {
  if (isOfflineMode()) {
    return {
      total_eval_samples: 25,
      recall: 100.0,
      precision: 100.0,
      f1_score: 100.0,
      false_positive_rate: 0.0,
      avg_latency_ms: 18.5,
      ai_mode: 'fallback',
    };
  }
  const res = await fetch(`${API_BASE}/eval`, {
    headers: getHeaders(),
  });
  return await handleResponse(res);
}

// ---------------------------------------------------------------------------
// Conversations
// ---------------------------------------------------------------------------

export async function fetchConversations(params = {}) {
  if (isOfflineMode()) {
    const data = await fetchDemoCache();
    let items = data.conversations || [];
    if (params.category) items = items.filter(c => c.category === params.category);
    if (params.priority) items = items.filter(c => c.priority === params.priority);
    if (params.risk) items = items.filter(c => c.security.risk_level === params.risk);
    if (params.sentiment) items = items.filter(c => c.sentiment === params.sentiment);
    if (params.q) {
      const q = params.q.toLowerCase();
      items = items.filter(c => 
        c.customer_issue.toLowerCase().includes(q) || 
        c.raw_text_masked.toLowerCase().includes(q) ||
        c.conversation_id.toLowerCase().includes(q)
      );
    }
    return { items, total: items.length, page: 1, limit: 50 };
  }

  const query = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '') query.append(k, v);
  });
  const res = await fetch(`${API_BASE}/conversations?${query.toString()}`, {
    headers: getHeaders(),
  });
  return await handleResponse(res);
}

export async function fetchConversationById(id) {
  if (isOfflineMode()) {
    const data = await fetchDemoCache();
    const item = (data.conversations || []).find(c => c.conversation_id === id);
    if (!item) throw new Error(`Conversation ${id} not found`);
    return item;
  }
  const res = await fetch(`${API_BASE}/conversations/${id}`, {
    headers: getHeaders(),
  });
  return await handleResponse(res);
}

export async function deleteConversation(id) {
  if (isOfflineMode()) return { status: 'deleted', id };
  const res = await fetch(`${API_BASE}/conversations/${id}`, {
    method: 'DELETE',
    headers: getHeaders(),
  });
  return await handleResponse(res);
}

export async function reanalyzeConversation(id) {
  if (isOfflineMode()) return await fetchConversationById(id);
  const res = await fetch(`${API_BASE}/conversations/${id}/reanalyze`, {
    method: 'POST',
    headers: getHeaders(),
  });
  return await handleResponse(res);
}

// ---------------------------------------------------------------------------
// Live Analyzer
// ---------------------------------------------------------------------------

export async function analyzeLive(payload) {
  if (isOfflineMode()) {
    const isPhish = /otp|password|verify|click|login|suspended/i.test(payload.text || '');
    return {
      conversation_id: `DEMO-${Date.now().toString().slice(-4)}`,
      channel: payload.channel || 'chat',
      created_at: new Date().toISOString(),
      customer_issue: isPhish ? 'Phishing alert' : 'Customer Inquiry',
      category: isPhish ? 'Security Concern' : 'Billing/Payment',
      issue_label: isPhish ? 'Phishing Attempt' : 'Payment Failure',
      keywords: ['payment', 'account', 'verify'],
      sentiment: isPhish ? 'Negative' : 'Neutral',
      emotion: isPhish ? 'Urgency' : 'Frustration',
      emotion_intensity: isPhish ? 4 : 2,
      is_angry: isPhish,
      urgency: isPhish ? 'High' : 'Medium',
      priority: isPhish ? 'Critical' : 'High',
      priority_reason: isPhish ? 'Active security threat detected' : 'Payment query requiring review',
      resolution_status: 'Pending',
      resolution_reason: 'Awaiting agent/security action',
      summary: {
        issue: payload.text?.slice(0, 100) || 'Analyzed input',
        customer_request: 'Urgent investigation',
        actions_taken: 'Evaluated against security rules',
        current_status: 'Completed',
        priority: isPhish ? 'Critical' : 'High'
      },
      security: {
        threat_detected: isPhish,
        threat_type: isPhish ? 'Phishing' : 'None',
        social_engineering: isPhish ? 'Yes' : 'No',
        techniques: isPhish ? ['Urgency', 'Credential Harvesting'] : [],
        suspicious_url: isPhish,
        suspicious_domain: isPhish,
        suspicious_email: false,
        suspicious_attachment: false,
        credential_request: isPhish,
        otp_request: isPhish,
        urls: isPhish ? [{
          url: 'http://paypa1-security.example/login',
          domain: 'paypa1-security.example',
          subdomain: '',
          https: false,
          ip_literal: false,
          shortener: false,
          length: 38,
          lookalike_of: 'paypal',
          risk: 'High',
          reasons: ['Lookalike domain mimicking protected brand paypal (+35)']
        }] : [],
        emails: [],
        attachments: [],
        rule_score: isPhish ? 85 : 0,
        risk_level: isPhish ? 'Critical' : 'Low',
        risk_reasons: isPhish ? ['Lookalike domain detected', 'Credential/OTP requested'] : ['No threats identified'],
        recommended_action: isPhish ? 'Escalate to security team immediately' : 'Normal support handling'
      },
      ai_mode: 'fallback',
      processing_ms: 12,
      raw_text_masked: payload.text,
      messages: [{ sender: 'customer', text: payload.text, timestamp: new Date().toISOString() }]
    };
  }

  const res = await fetch(`${API_BASE}/analyze`, {
    method: 'POST',
    headers: getHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify(payload),
  });
  return await handleResponse(res);
}

// ---------------------------------------------------------------------------
// Ingestion & Uploads
// ---------------------------------------------------------------------------

export async function uploadDatasetFile(file) {
  const formData = new FormData();
  formData.append('file', file);

  const res = await fetch(`${API_BASE}/upload`, {
    method: 'POST',
    headers: getHeaders(), // note: don't set Content-Type so browser sets boundary
    body: formData,
  });
  return await handleResponse(res);
}

export async function pollJobStatus(jobId) {
  const res = await fetch(`${API_BASE}/jobs/${jobId}`, {
    headers: getHeaders(),
  });
  return await handleResponse(res);
}

// ---------------------------------------------------------------------------
// Multimodal Copilot Studio
// ---------------------------------------------------------------------------

export async function diagnoseIssue(payload) {
  if (isOfflineMode()) {
    return {
      session_id: `COPILOT-DEMO-${Date.now().toString().slice(-4)}`,
      created_at: new Date().toISOString(),
      issue_title: 'Checkout 3DS Timeout & Pending Hold',
      category: 'Billing & Payments',
      severity: 'Medium',
      root_cause: 'Customer bank put a temporary authorization hold during 3DS challenge timeout.',
      visual_findings: ['Declined banner visible', 'Error code ERR_3DS_TIMEOUT'],
      is_threat: false,
      threat_details: null,
      troubleshooting_steps: [
        'Confirm if payment authorization expired on gateway.',
        'Advise customer that authorization hold releases automatically in 48 hours.',
        'Offer alternate payment link or invoice method.'
      ],
      suggested_response: 'Dear customer, your bank placed a temporary verification hold which will reverse automatically within 24-48 business hours.',
      prevention_tip: 'Enable automatic retry with alternate card network.',
      image_attached: Boolean(payload.image_data),
      image_name: payload.image_name || null,
      processing_ms: 18,
      ai_mode: 'fallback',
      raw_message: payload.message || ''
    };
  }

  const res = await fetch(`${API_BASE}/copilot/diagnose`, {
    method: 'POST',
    headers: getHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify(payload),
  });
  return await handleResponse(res);
}

export async function fetchCopilotHistory(limit = 20) {
  if (isOfflineMode()) {
    return [];
  }
  const res = await fetch(`${API_BASE}/copilot/history?limit=${limit}`, {
    headers: getHeaders(),
  });
  return await handleResponse(res);
}

// ---------------------------------------------------------------------------
// Gmail Integration
// ---------------------------------------------------------------------------

export async function fetchGmailStatus() {
  if (isOfflineMode()) {
    return { configured: false, connected: false, message: 'Offline Demo Mode' };
  }
  const res = await fetch(`${API_BASE}/gmail/status`, {
    headers: getHeaders(),
  });
  return await handleResponse(res);
}

export async function fetchGmailAuthUrl() {
  if (isOfflineMode()) {
    return { configured: false, auth_url: null };
  }
  const res = await fetch(`${API_BASE}/gmail/auth-url`, {
    headers: getHeaders(),
  });
  return await handleResponse(res);
}

export async function disconnectGmail() {
  if (isOfflineMode()) {
    return { status: 'ok', disconnected: true };
  }
  const res = await fetch(`${API_BASE}/gmail/disconnect`, {
    method: 'POST',
    headers: getHeaders(),
  });
  return await handleResponse(res);
}

export async function syncGmail(limit = 10) {
  if (isOfflineMode()) {
    return { status: 'ok', synced_count: 0, message: 'Offline Mode: Gmail sync simulated' };
  }
  const res = await fetch(`${API_BASE}/gmail/sync?limit=${limit}`, {
    method: 'POST',
    headers: getHeaders(),
  });
  return await handleResponse(res);
}
