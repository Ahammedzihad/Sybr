/**
 * Centralized API Client.
 * Communicates strictly with the FastAPI backend, with built-in Offline Demo Mode.
 */

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export function isOfflineMode() {
  return localStorage.getItem('sybr_offline_mode') === 'true';
}

export function setOfflineMode(enabled) {
  localStorage.setItem('sybr_offline_mode', enabled ? 'true' : 'false');
  window.dispatchEvent(new Event('offline-mode-changed'));
}

async function fetchDemoCache() {
  const res = await fetch('/demo-cache.json');
  return await res.json();
}

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
  const res = await fetch(`${API_BASE}/dashboard`);
  if (!res.ok) throw new Error('Failed to load dashboard metrics');
  return await res.json();
}

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
  const res = await fetch(`${API_BASE}/conversations?${query.toString()}`);
  if (!res.ok) throw new Error('Failed to load conversations');
  return await res.json();
}

export async function fetchConversationById(id) {
  if (isOfflineMode()) {
    const data = await fetchDemoCache();
    const item = (data.conversations || []).find(c => c.conversation_id === id);
    if (!item) throw new Error(`Conversation ${id} not found`);
    return item;
  }
  const res = await fetch(`${API_BASE}/conversations/${id}`);
  if (!res.ok) throw new Error('Failed to load conversation details');
  return await res.json();
}

export async function analyzeLive(payload) {
  if (isOfflineMode()) {
    // Offline simulated analysis
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
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Analysis request failed');
  }
  return await res.json();
}

export async function uploadDatasetFile(file, onProgress) {
  const formData = new FormData();
  formData.append('file', file);

  const res = await fetch(`${API_BASE}/upload`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'File upload failed');
  }
  return await res.json();
}

export async function pollJobStatus(jobId) {
  const res = await fetch(`${API_BASE}/jobs/${jobId}`);
  if (!res.ok) throw new Error('Failed to query job status');
  return await res.json();
}

export async function fetchIssues() {
  if (isOfflineMode()) {
    const data = await fetchDemoCache();
    return { total_conversations: data.kpis.total_conversations, issues: data.issue_frequency };
  }
  const res = await fetch(`${API_BASE}/issues`);
  if (!res.ok) throw new Error('Failed to load issues');
  return await res.json();
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
  const res = await fetch(`${API_BASE}/trends?bucket=${bucket}`);
  if (!res.ok) throw new Error('Failed to load trends');
  return await res.json();
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
  const res = await fetch(`${API_BASE}/eval`);
  if (!res.ok) throw new Error('Failed to load evaluation metrics');
  return await res.json();
}

export async function deleteConversation(id) {
  if (isOfflineMode()) return { status: 'deleted', id };
  const res = await fetch(`${API_BASE}/conversations/${id}`, { method: 'DELETE' });
  if (!res.ok) throw new Error('Failed to delete conversation');
  return await res.json();
}

export async function reanalyzeConversation(id) {
  if (isOfflineMode()) return await fetchConversationById(id);
  const res = await fetch(`${API_BASE}/conversations/${id}/reanalyze`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to reanalyze conversation');
  return await res.json();
}
