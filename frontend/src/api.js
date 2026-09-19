/**
 * Centralized API Client for SybrV2.
 * Communicates strictly with the FastAPI backend, supporting Supabase Authentication,
 * Role-Based Access Control (Customer vs Admin), Copilot Studio, Gmail Integration,
 * and built-in Offline Demo Mode.
 */
import { createClient } from '@supabase/supabase-js';

const API_BASE = import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_URL || (import.meta.env.DEV ? 'http://localhost:8000' : '');

// ---------------------------------------------------------------------------
// Supabase Client Management (Strictly from Frontend Environment)
// ---------------------------------------------------------------------------

const SUPABASE_URL = (import.meta.env.VITE_SUPABASE_URL || '').trim();
const SUPABASE_ANON_KEY = (import.meta.env.VITE_SUPABASE_ANON_KEY || '').trim();

export function isSupabaseConfigured() {
  return Boolean(SUPABASE_URL && SUPABASE_ANON_KEY);
}

let _supabaseInstance = null;
let _authListenerAttached = false;

export function getSupabaseClient() {
  if (SUPABASE_URL && SUPABASE_ANON_KEY) {
    if (!_supabaseInstance) {
      _supabaseInstance = createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
        auth: {
          persistSession: true,
          autoRefreshToken: true,
          detectSessionInUrl: true,
        },
      });

      if (!_authListenerAttached) {
        _authListenerAttached = true;
        _supabaseInstance.auth.onAuthStateChange(async (event, session) => {
          if ((event === 'SIGNED_IN' || event === 'INITIAL_SESSION' || event === 'TOKEN_REFRESHED') && session) {
            const u = session.user;
            let userRole = u.user_metadata?.role || u.app_metadata?.role || 'customer';

            // Check public.profiles in Supabase via PostgREST
            if (_supabaseInstance && userRole !== 'admin') {
              try {
                const { data: prof } = await _supabaseInstance
                  .from('profiles')
                  .select('role, display_name, status')
                  .eq('id', u.id)
                  .maybeSingle();
                if (prof?.role) {
                  userRole = prof.role;
                }
              } catch {
                // quiet fallback
              }
            }

            // Also check backend /auth/me if available
            if (API_BASE && !API_BASE.startsWith(window.location.origin)) {
              try {
                const res = await fetch(`${API_BASE}/auth/me`, {
                  headers: { Authorization: `Bearer ${session.access_token}` },
                });
                if (res.ok) {
                  const meData = await res.json();
                  if (meData?.role) userRole = meData.role;
                }
              } catch {
                // quiet fallback
              }
            }

            setAuthSession(session.access_token, {
              id: u.id,
              email: u.email,
              display_name: u.user_metadata?.display_name || u.email?.split('@')[0],
              role: userRole,
              status: 'active',
              is_demo: false,
            }, false);
          } else if (event === 'SIGNED_OUT') {
            clearAuthSession();
          }
        });
      }
    }
    return _supabaseInstance;
  }
  return null;
}

// Proxied supabase client preserving backward compatibility and preventing tree-shaking
export const supabase = new Proxy({}, {
  get(target, prop) {
    const client = getSupabaseClient();
    if (!client) return undefined;
    const val = client[prop];
    if (typeof val === 'function') {
      return val.bind(client);
    }
    return val;
  }
});

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
    throw new Error('Invalid email or password. Please verify your credentials.');
  }
  if (res.status === 405) {
    throw new Error(
      'Authentication endpoint returned HTTP 405 Method Not Allowed. The frontend is requesting a static URL. Please configure VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY in your deployment environment variables, or ensure VITE_API_URL points to the live FastAPI backend.'
    );
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
  const cleanEmail = email.trim().toLowerCase();

  // 1. Supabase Auth if client-side credentials are configured
  const client = getSupabaseClient();
  if (client) {
    let sbData, sbErr;
    try {
      const res = await client.auth.signInWithPassword({
        email: cleanEmail,
        password,
      });
      sbData = res.data;
      sbErr = res.error;
    } catch (err) {
      // quiet fallback to backend or demo mode
    }

    if (sbErr) {
      const msg = (sbErr.message || '').toLowerCase();
      if (msg.includes('email not confirmed')) {
        throw new Error('Please confirm your email address to continue.');
      }
      if (msg.includes('invalid login credentials') || msg.includes('invalid_grant')) {
        throw new Error('Invalid email or password.');
      }
      if (!msg.includes('network') && !msg.includes('fetch')) {
        throw new Error(sbErr.message || 'Invalid email or password.');
      }
    }

    if (sbData?.session) {
      const token = sbData.session.access_token;
      const u = sbData.user;

      // Retrieve user role from Supabase metadata, public.profiles, or backend /auth/me
      let userRole = u.user_metadata?.role || u.app_metadata?.role || 'customer';

      // Check public.profiles in Supabase
      try {
        const { data: prof } = await client
          .from('profiles')
          .select('role, display_name, status')
          .eq('id', u.id)
          .maybeSingle();
        if (prof?.role) {
          userRole = prof.role;
        }
      } catch {
        // quiet fallback
      }

      // Validate with backend /auth/me server-side if backend is configured
      let userProfile = null;
      if (API_BASE && !API_BASE.startsWith(window.location.origin)) {
        try {
          const profileRes = await fetch(`${API_BASE}/auth/me`, {
            headers: { Authorization: `Bearer ${token}` },
          });
          if (profileRes.ok) {
            userProfile = await profileRes.json();
          }
        } catch {
          // quiet fallback
        }
      }

      if (!userProfile) {
        userProfile = {
          id: u.id,
          email: u.email,
          display_name: u.user_metadata?.display_name || u.email?.split('@')[0],
          role: userRole,
          status: 'active',
          is_demo: false,
        };
      }

      setAuthSession(token, userProfile, false);
      return { access_token: token, user: userProfile, is_demo: false };
    }
  }

  // 2. FastAPI Backend /auth/login (handles Supabase server-side and backend Demo Mode)
  if (!isOfflineMode() && API_BASE) {
    try {
      const res = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: cleanEmail, password }),
      });
      const data = await handleResponse(res);
      setAuthSession(data.access_token, data.user, data.is_demo);
      return data;
    } catch (err) {
      if (err.message && !err.message.toLowerCase().includes('failed to fetch') && !err.message.toLowerCase().includes('networkerror')) {
        throw err;
      }
    }
  }

  // 3. Demo Mode Fallback (Deterministic offline simulation)
  const isDemoAdmin = cleanEmail.includes('admin');
  const demoUser = {
    id: isDemoAdmin ? 'admin-user-001' : 'demo-user-001',
    email: cleanEmail,
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
  const cleanEmail = email.trim().toLowerCase();

  // 1. Supabase Auth if client-side credentials are configured
  const client = getSupabaseClient();
  if (client) {
    try {
      const { data, error } = await client.auth.signUp({
        email: cleanEmail,
        password,
        options: {
          data: {
            display_name: displayName || cleanEmail.split('@')[0],
            role: 'customer',
          },
        },
      });

      if (error) {
        throw new Error(error.message || 'Signup failed.');
      }

      return {
        status: 'ok',
        message: 'Account created! Please check your email inbox to verify your account.',
      };
    } catch (err) {
      if (err.message && !err.message.toLowerCase().includes('fetch')) {
        throw err;
      }
    }
  }

  // 2. FastAPI Backend /auth/signup
  if (!isOfflineMode() && API_BASE) {
    try {
      const res = await fetch(`${API_BASE}/auth/signup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: cleanEmail, password, display_name: displayName }),
      });
      return await handleResponse(res);
    } catch (err) {
      if (err.message && !err.message.toLowerCase().includes('failed to fetch') && !err.message.toLowerCase().includes('networkerror')) {
        throw err;
      }
    }
  }

  // 3. Offline / Demo Mode Fallback
  return {
    status: 'ok',
    message: 'Account registered successfully in Demo Mode. Default role: customer.',
  };
}

export async function resetPassword(email) {
  const cleanEmail = email.trim().toLowerCase();

  // 1. Supabase Auth if client-side credentials are configured
  const client = getSupabaseClient();
  if (client) {
    try {
      const { error } = await client.auth.resetPasswordForEmail(cleanEmail, {
        redirectTo: `${window.location.origin}/reset-password`,
      });

      if (error) {
        throw new Error(error.message || 'Password reset failed.');
      }

      return {
        status: 'ok',
        message: 'If this email is registered, instructions to reset your password have been sent.',
      };
    } catch (err) {
      if (err.message && !err.message.toLowerCase().includes('fetch')) {
        throw err;
      }
    }
  }

  // 2. FastAPI Backend /auth/reset-password
  if (!isOfflineMode() && API_BASE) {
    try {
      const res = await fetch(`${API_BASE}/auth/reset-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: cleanEmail }),
      });
      return await handleResponse(res);
    } catch (err) {
      if (err.message && !err.message.toLowerCase().includes('failed to fetch') && !err.message.toLowerCase().includes('networkerror')) {
        throw err;
      }
    }
  }

  // 3. Offline / Demo Mode Fallback
  return {
    status: 'ok',
    message: 'If this email is registered, instructions to reset your password have been sent.',
  };
}

export async function updatePassword(newPassword) {
  const client = getSupabaseClient();
  if (client) {
    const { error } = await client.auth.updateUser({ password: newPassword });
    if (error) throw new Error(error.message);
    return { status: 'ok', message: 'Password updated successfully.' };
  }
  return { status: 'ok', message: 'Password updated in Demo Mode.' };
}

export async function logout() {
  try {
    const client = getSupabaseClient();
    if (client) {
      await client.auth.signOut();
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

export async function submitAdminReviewCorrection(convId, correctionData) {
  if (isOfflineMode()) {
    return {
      conversation_id: convId,
      ...correctionData,
      is_human_reviewed: true,
      reviewed_by: 'admin-user-001',
      processing_status: 'Human Reviewed',
    };
  }
  const res = await fetch(`${API_BASE}/admin/conversations/${convId}/review`, {
    method: 'PATCH',
    headers: getHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify(correctionData),
  });
  return await handleResponse(res);
}

export async function updateAdminConversationStatus(convId, statusData) {
  if (isOfflineMode()) {
    return { conversation_id: convId, ...statusData };
  }
  const res = await fetch(`${API_BASE}/admin/conversations/${convId}/status`, {
    method: 'PATCH',
    headers: getHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify(statusData),
  });
  return await handleResponse(res);
}

export async function addAdminInternalNote(convId, text) {
  if (isOfflineMode()) {
    return {
      id: `note-${Date.now().toString().slice(-6)}`,
      author_id: 'admin-user-001',
      author_name: 'System Administrator',
      text,
      created_at: new Date().toISOString(),
    };
  }
  const res = await fetch(`${API_BASE}/admin/conversations/${convId}/notes`, {
    method: 'POST',
    headers: getHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({ text }),
  });
  return await handleResponse(res);
}

export async function requestHumanReview(convId, reason = 'Flagged for review') {
  if (isOfflineMode()) {
    return { conversation_id: convId, needs_human_review: true, review_reason: reason };
  }
  const res = await fetch(`${API_BASE}/admin/conversations/${convId}/request-review?reason=${encodeURIComponent(reason)}`, {
    method: 'POST',
    headers: getHeaders(),
  });
  return await handleResponse(res);
}

export async function generateDraftResponse(convId, options = {}) {
  if (isOfflineMode()) {
    return {
      draft_response: `Dear Customer,\n\nThank you for reaching out regarding your support inquiry. Our administrative team has reviewed your ticket and is actively resolving the issue.\n\nBest regards,\nSybr Support Team`,
      recommended_action: 'Standard operational support follow-up',
      rationale: 'Customer inquiry under active administrative monitoring',
    };
  }
  const res = await fetch(`${API_BASE}/admin/conversations/${convId}/draft-response`, {
    method: 'POST',
    headers: getHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify(options),
  });
  return await handleResponse(res);
}

export async function fetchAdminCategoryAnalytics() {
  if (isOfflineMode()) {
    const data = await fetchDemoCache();
    const categories = Object.entries(data.category_distribution || {}).map(([cat, count]) => ({
      category: cat,
      count,
      percentage: Math.round((count / (data.kpis?.total_conversations || 1)) * 100),
      unresolved_count: Math.floor(count * 0.3),
      critical_count: Math.floor(count * 0.1),
      threat_count: cat === 'Security Concern' ? count : 0,
    }));
    return { total_conversations: data.kpis?.total_conversations || 48, categories };
  }
  const res = await fetch(`${API_BASE}/admin/analytics/categories`, {
    headers: getHeaders(),
  });
  return await handleResponse(res);
}

export async function fetchAdminSecurityAnalytics() {
  if (isOfflineMode()) {
    return {
      total_threats: 14,
      critical_count: 6,
      high_count: 8,
      threat_types: { 'Phishing': 9, 'Social Engineering': 3, 'Impersonation': 2 },
      techniques: { 'Urgency': 12, 'Credential Harvesting': 9, 'OTP Request': 8, 'Lookalike Domains': 7 },
      top_domains: [
        { domain: 'paypa1-security.example', count: 5 },
        { domain: 'bank-auth-verify.net', count: 4 },
        { domain: 'account-update-portal.org', count: 3 },
      ],
      top_senders: [
        { domain: 'gmail.com', count: 8 },
        { domain: 'sec-alert.com', count: 3 },
      ],
      top_attachments: [],
    };
  }
  const res = await fetch(`${API_BASE}/admin/analytics/security`, {
    headers: getHeaders(),
  });
  return await handleResponse(res);
}

export async function fetchAdminAIPerformance() {
  if (isOfflineMode()) {
    return {
      total_analyzed: 48,
      gemini_count: 36,
      fallback_count: 12,
      fallback_rate: 25.0,
      avg_processing_ms: 22,
      human_corrections_count: 5,
      human_correction_rate: 10.4,
      review_queue_count: 3,
      model_name: 'gemini-2.5-flash',
      prompt_injection_signals_caught: 2,
    };
  }
  const res = await fetch(`${API_BASE}/admin/analytics/ai`, {
    headers: getHeaders(),
  });
  return await handleResponse(res);
}

export async function fetchAdminCustomers() {
  if (isOfflineMode()) {
    return [
      { customer_id: 'demo-user-001', email: 'demo@sybr.local', display_name: 'Demo Customer', conversation_count: 11, unresolved_count: 3, critical_count: 2, last_activity: new Date().toISOString() },
      { customer_id: 'demo-user-999', email: 'user999@sybr.local', display_name: 'Customer B', conversation_count: 1, unresolved_count: 0, critical_count: 0, last_activity: new Date().toISOString() },
    ];
  }
  const res = await fetch(`${API_BASE}/admin/customers`, {
    headers: getHeaders(),
  });
  return await handleResponse(res);
}

export async function fetchAdminCustomerHistory(customerId) {
  if (isOfflineMode()) {
    const data = await fetchDemoCache();
    return {
      customer_id: customerId,
      email: `${customerId}@sybr.local`,
      display_name: 'Customer Account',
      total_conversations: (data.conversations || []).length,
      conversations: data.conversations || [],
    };
  }
  const res = await fetch(`${API_BASE}/admin/customers/${customerId}`, {
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
