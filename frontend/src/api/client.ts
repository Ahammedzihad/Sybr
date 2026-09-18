/**
 * Centralized API client communicating with FastAPI backend.
 * Resilient to polymorphic response structures and guarantees type-safe outputs.
 */

import {
  AnalysisRequest,
  AnalysisResult,
  ConversationListResponse,
  DashboardStats,
  HealthStatus,
  normalizeConversation,
} from '../types/analysis';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl.replace(/\/+$/, '');
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      Accept: 'application/json',
      ...options.headers,
    };

    try {
      const response = await fetch(url, { ...options, headers });
      if (!response.ok) {
        let errorDetail = `Request failed with status ${response.status}`;
        try {
          const errJson = await response.json();
          if (errJson.detail) errorDetail = errJson.detail;
        } catch {
          // ignore non-json error
        }
        throw new Error(errorDetail);
      }
      return await response.json();
    } catch (err: any) {
      console.error(`[API Error] ${options.method || 'GET'} ${endpoint}:`, err.message);
      throw err;
    }
  }

  /**
   * Health check endpoint.
   */
  async getHealth(): Promise<HealthStatus> {
    return this.request<HealthStatus>('/health');
  }

  /**
   * Submits a message for security & threat analysis.
   */
  async analyze(payload: AnalysisRequest): Promise<AnalysisResult> {
    const rawResult = await this.request<any>('/analyze', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    const normalized = normalizeConversation(rawResult);
    return normalized.analysis!;
  }

  /**
   * Retrieves paginated conversation history.
   * Seamlessly adapts to both raw array responses and paginated { items, total } envelopes.
   */
  async getConversations(
    page: number = 1,
    limit: number = 20,
    riskLevel?: string
  ): Promise<ConversationListResponse> {
    const params = new URLSearchParams();
    if (page) params.append('page', page.toString());
    if (limit) params.append('limit', limit.toString());
    if (riskLevel && riskLevel !== 'ALL') {
      params.append('risk_level', riskLevel);
    }

    const queryStr = params.toString() ? `?${params.toString()}` : '';
    const response = await this.request<any>(`/conversations${queryStr}`);

    if (Array.isArray(response)) {
      // Backend returned flat array of ConversationRecords
      let items = response.map(normalizeConversation);
      if (riskLevel && riskLevel !== 'ALL') {
        items = items.filter(
          (item) => item.risk_level?.toLowerCase() === riskLevel.toLowerCase()
        );
      }
      const total = items.length;
      const totalPages = Math.max(1, Math.ceil(total / limit));
      const startIndex = (page - 1) * limit;
      const pagedItems = items.slice(startIndex, startIndex + limit);

      return {
        items: pagedItems,
        total,
        page,
        limit,
        pages: totalPages,
      };
    }

    if (response && Array.isArray(response.items)) {
      return {
        items: response.items.map(normalizeConversation),
        total: response.total ?? response.items.length,
        page: response.page ?? page,
        limit: response.limit ?? limit,
        pages: response.pages ?? Math.max(1, Math.ceil((response.total || response.items.length) / limit)),
      };
    }

    return {
      items: [],
      total: 0,
      page: 1,
      limit,
      pages: 1,
    };
  }

  /**
   * Retrieves aggregated dashboard metrics.
   */
  async getDashboard(): Promise<DashboardStats> {
    const stats = await this.request<any>('/dashboard');
    return {
      total_conversations: stats.total_conversations ?? 0,
      total_complaints: stats.total_complaints ?? 0,
      high_risk_count: stats.high_risk_count ?? 0,
      resolved_count: stats.resolved_count ?? 0,
      pending_count: stats.pending_count ?? 0,
      unresolved_count: stats.unresolved_count ?? 0,
      critical_count: stats.critical_count ?? 0,
      most_common_complaint: stats.most_common_complaint || 'N/A',
      most_frequent_issue: stats.most_frequent_issue || 'N/A',
      frequently_reported_issues: stats.frequently_reported_issues || { by_category: [], by_keyword: [] },
      categories: stats.categories || stats.category_distribution || {},
      sentiments: stats.sentiments || stats.sentiment_split || {},
      emotions: stats.emotions || {},
      risk_levels: stats.risk_levels || stats.risk_level_distribution || {},
      threat_types: stats.threat_types || {},
    };
  }
}

export const api = new ApiClient(BASE_URL);
