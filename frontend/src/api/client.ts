/**
 * Centralized API client communicating with FastAPI backend.
 */

import {
  AnalysisRequest,
  AnalysisResult,
  ConversationListResponse,
  DashboardStats,
  HealthStatus,
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
    return this.request<AnalysisResult>('/analyze', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  /**
   * Retrieves paginated conversation history.
   */
  async getConversations(
    page: number = 1,
    limit: number = 20,
    riskLevel?: string
  ): Promise<ConversationListResponse> {
    const params = new URLSearchParams({
      page: page.toString(),
      limit: limit.toString(),
    });
    if (riskLevel && riskLevel !== 'ALL') {
      params.append('risk_level', riskLevel);
    }
    return this.request<ConversationListResponse>(`/conversations?${params.toString()}`);
  }

  /**
   * Retrieves aggregated dashboard metrics.
   */
  async getDashboard(): Promise<DashboardStats> {
    return this.request<DashboardStats>('/dashboard');
  }
}

export const api = new ApiClient(BASE_URL);
