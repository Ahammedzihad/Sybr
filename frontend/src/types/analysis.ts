/**
 * Types and interfaces for AI Security Analytics.
 * Strict client-side alignment with backend Pydantic models and locked schema.json.
 */

export interface AnalysisRequest {
  sender?: string;
  subject?: string;
  message: string;
  urls?: string[];
  conversation_id?: string;
}

export interface StructuredSummary {
  issue?: string;
  customer_request?: string;
  actions_taken?: string;
  current_status?: string;
  priority?: string;
  overview?: string;
  [key: string]: any;
}

/**
 * Locked analysis result schema matching the 11-field backend contract.
 */
export interface AnalysisResult {
  category: string;
  sentiment: string;
  emotion: string;
  priority: string;
  summary: string | StructuredSummary;
  resolution_status: string;
  threat_type: string;
  social_engineering: boolean;
  suspicious_url: boolean;
  risk_level: string;
  recommended_action: string;
  suspicious_email?: boolean;
  url_risk?: string;
  url_reason?: string | null;
  email_risk?: string;
  email_reason?: string | null;
  technique?: string[];
  keywords?: string[];
  clean_text?: string;
  masked_text?: string;
}

export interface ConversationRecord {
  conversation_id: string;
  raw_text?: string;
  clean_text?: string;
  masked_text?: string;

  // Classification
  category: string;
  sentiment: string;
  emotion?: string;
  urgency?: string;
  priority: string;
  keywords?: string[];
  customer_request?: string;

  // Lifecycle
  resolution_status: string;
  summary?: string | StructuredSummary | null;

  // Security Heuristics - URL
  suspicious_url: boolean;
  url_risk?: string;
  url_reason?: string | null;

  // Security Heuristics - Email
  suspicious_email?: boolean;
  email_risk?: string;
  email_reason?: string | null;

  // Threat Intelligence
  threat_type: string;
  social_engineering: boolean;
  technique?: string[];
  risk_level: string;
  recommended_action: string;
  error?: string | null;

  // Optional UI / Compatibility fields
  id?: string;
  sender?: string;
  subject?: string;
  message?: string;
  urls?: string[];
  created_at?: string;
  analysis?: AnalysisResult;
  security_indicators?: string[];
}

export interface ConversationListResponse {
  items: ConversationRecord[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}

export interface DashboardStats {
  total_conversations: number;
  total_complaints?: number;
  high_risk_count: number;
  resolved_count: number;
  pending_count: number;
  unresolved_count?: number;
  critical_count?: number;
  most_common_complaint?: string;
  most_frequent_issue?: string;
  frequently_reported_issues?: {
    by_category?: [string, number][];
    by_keyword?: [string, number][];
  };
  categories: Record<string, number>;
  sentiments: Record<string, number>;
  emotions: Record<string, number>;
  risk_levels: Record<string, number>;
  threat_types: Record<string, number>;
}

export interface HealthStatus {
  status: string;
  version: string;
  mock_mode: string;
  database: string;
}

/**
 * Normalizes any conversation payload from backend into a strictly safe ConversationRecord.
 */
export function normalizeConversation(item: any): ConversationRecord {
  if (!item || typeof item !== 'object') {
    return {
      conversation_id: 'CS-UNKNOWN',
      id: 'CS-UNKNOWN',
      category: 'Unknown',
      sentiment: 'Neutral',
      priority: 'Medium',
      resolution_status: 'Pending',
      threat_type: 'None',
      social_engineering: false,
      suspicious_url: false,
      risk_level: 'Low',
      recommended_action: 'No action required.',
    };
  }

  const convId = item.conversation_id || item.id || `CS-${Math.random().toString(16).slice(2, 8).toUpperCase()}`;
  const category = item.category || item.analysis?.category || 'Unknown';
  const riskLevel = item.risk_level || item.analysis?.risk_level || 'Low';
  const priority = item.priority || item.analysis?.priority || 'Medium';
  const sentiment = item.sentiment || item.analysis?.sentiment || 'Neutral';
  const emotion = item.emotion || item.analysis?.emotion || 'Neutral';
  const resolutionStatus = item.resolution_status || item.analysis?.resolution_status || 'Pending';
  const threatType = item.threat_type || item.analysis?.threat_type || 'None';
  const socialEngineering = Boolean(item.social_engineering ?? item.analysis?.social_engineering);
  const suspiciousUrl = Boolean(item.suspicious_url ?? item.analysis?.suspicious_url);
  const suspiciousEmail = Boolean(item.suspicious_email ?? false);
  const recommendedAction = item.recommended_action || item.analysis?.recommended_action || 'Review conversation and verify sender details.';
  const rawText = item.raw_text || item.message || '';
  const cleanText = item.clean_text || '';
  const maskedText = item.masked_text || '';
  const summary = item.summary || item.analysis?.summary || null;

  // Extract URLs from raw text if missing
  let urls = item.urls || [];
  if (!urls.length && rawText) {
    const matches = rawText.match(/https?:\/\/[^\s]+/g);
    if (matches) urls = matches;
  }

  // Extract sender/subject if available in rawText
  let sender = item.sender || '';
  let subject = item.subject || '';
  if (!sender && rawText) {
    const senderMatch = rawText.match(/From:\s*([^\n\r]+)/i);
    if (senderMatch) sender = senderMatch[1].trim();
    const subjectMatch = rawText.match(/Subject:\s*([^\n\r]+)/i);
    if (subjectMatch) subject = subjectMatch[1].trim();
  }
  if (!sender) sender = 'Customer';
  if (!subject) subject = category !== 'Unknown' ? `${category} Inquiry` : 'Support Request';

  // Construct security indicators list
  const indicators: string[] = [];
  if (suspiciousUrl) indicators.push(`Suspicious URL (${item.url_risk || 'High'})`);
  if (item.url_reason) indicators.push(`URL Reason: ${item.url_reason}`);
  if (suspiciousEmail) indicators.push(`Suspicious Email (${item.email_risk || 'High'})`);
  if (item.email_reason) indicators.push(`Email Reason: ${item.email_reason}`);
  if (socialEngineering) indicators.push('Social Engineering Coercion Detected');
  if (Array.isArray(item.technique) && item.technique.length > 0) {
    indicators.push(...item.technique.map((t: string) => `Technique: ${t}`));
  }

  const normalized: ConversationRecord = {
    ...item,
    conversation_id: convId,
    id: convId,
    sender,
    subject,
    message: rawText,
    raw_text: rawText,
    clean_text: cleanText,
    masked_text: maskedText,
    category,
    sentiment,
    emotion,
    priority,
    resolution_status: resolutionStatus,
    threat_type: threatType,
    social_engineering: socialEngineering,
    suspicious_url: suspiciousUrl,
    suspicious_email: suspiciousEmail,
    url_risk: item.url_risk || (suspiciousUrl ? 'High' : 'Low'),
    url_reason: item.url_reason || null,
    email_risk: item.email_risk || (suspiciousEmail ? 'High' : 'Low'),
    email_reason: item.email_reason || null,
    risk_level: riskLevel,
    recommended_action: recommendedAction,
    summary,
    urls,
    created_at: item.created_at || new Date().toISOString(),
    security_indicators: indicators,
    // Provide locked analysis sub-object for nested components
    analysis: {
      category,
      sentiment,
      emotion,
      priority,
      summary: typeof summary === 'string' ? summary : summary?.issue || summary?.overview || 'No summary available.',
      resolution_status: resolutionStatus,
      threat_type: threatType,
      social_engineering: socialEngineering,
      suspicious_url: suspiciousUrl,
      suspicious_email: suspiciousEmail,
      url_risk: item.url_risk || (suspiciousUrl ? 'High' : 'Low'),
      url_reason: item.url_reason || null,
      email_risk: item.email_risk || (suspiciousEmail ? 'High' : 'Low'),
      email_reason: item.email_reason || null,
      risk_level: riskLevel,
      recommended_action: recommendedAction,
      technique: item.technique || [],
      keywords: item.keywords || [],
      clean_text: cleanText,
      masked_text: maskedText,
    },
  };

  return normalized;
}

/**
 * Format string or structured summary object safely for rendering in JSX.
 */
export function formatSummaryText(summary: any): string {
  if (!summary) return 'No summary provided.';
  if (typeof summary === 'string') return summary;
  if (typeof summary === 'object') {
    if (summary.issue) return summary.issue;
    if (summary.overview) return summary.overview;
    const parts = Object.entries(summary)
      .filter(([k, v]) => typeof v === 'string' && v.trim() && k !== 'error')
      .map(([k, v]) => `${k.replace(/_/g, ' ')}: ${v}`);
    if (parts.length > 0) return parts.join(' | ');
  }
  return String(summary);
}
