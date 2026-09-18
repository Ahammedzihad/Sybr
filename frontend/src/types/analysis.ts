/**
 * Types and interfaces for AI Security Analytics.
 * Strict client-side alignment with backend Pydantic models.
 */

export interface AnalysisRequest {
  sender: string;
  subject: string;
  message: string;
  urls: string[];
}

/**
 * Locked analysis result schema matching the 11-field backend contract.
 */
export interface AnalysisResult {
  category: string;
  sentiment: string;
  emotion: string;
  priority: string;
  summary: string;
  resolution_status: string;
  threat_type: string;
  social_engineering: boolean;
  suspicious_url: boolean;
  risk_level: string;
  recommended_action: string;
}

export interface ConversationRecord {
  id: string;
  sender: string;
  subject: string;
  message: string;
  urls: string[];
  created_at: string;
  analysis: AnalysisResult;
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
  high_risk_count: number;
  resolved_count: number;
  pending_count: number;
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
