import React from 'react';
import {
  ShieldAlert,
  CheckCircle2,
  Clock,
  Inbox,
  AlertTriangle,
  RefreshCw,
  ArrowRight,
  TrendingUp,
  Tag,
  FolderOpen,
} from 'lucide-react';
import { api } from '../api/client';
import { useApiQuery } from '../hooks/useApi';
import { KPICard } from '../components/KPICard';
import { CategoryPieChart } from '../components/charts/CategoryPieChart';
import { RiskBarChart } from '../components/charts/RiskBarChart';
import { ThreatTypeChart } from '../components/charts/ThreatTypeChart';
import { SentimentChart } from '../components/charts/SentimentChart';

interface DashboardProps {
  onNavigateToAnalyze: () => void;
}

export const Dashboard: React.FC<DashboardProps> = ({ onNavigateToAnalyze }) => {
  const {
    data: stats,
    loading,
    error,
    refetch,
  } = useApiQuery(() => api.getDashboard(), []);

  if (loading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="h-9 w-9 animate-spin rounded-full border-4 border-sky-500 border-t-transparent" />
          <p className="text-sm font-medium text-slate-400">Loading security intelligence telemetry...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-xl border border-rose-900/50 bg-rose-950/20 p-8 text-center my-6">
        <AlertTriangle className="mx-auto h-12 w-12 text-rose-400 mb-3" />
        <h3 className="text-lg font-bold text-rose-300">Unable to load dashboard telemetry</h3>
        <p className="mt-1 text-sm text-slate-400">{error}</p>
        <button
          type="button"
          onClick={refetch}
          className="mt-4 inline-flex items-center gap-2 rounded-lg bg-slate-800 px-4 py-2 text-sm font-medium text-slate-200 hover:bg-slate-700 transition"
        >
          <RefreshCw className="h-4 w-4" /> Retry
        </button>
      </div>
    );
  }

  const defaultStats = stats || {
    total_conversations: 0,
    total_complaints: 0,
    high_risk_count: 0,
    resolved_count: 0,
    pending_count: 0,
    most_common_complaint: 'N/A',
    most_frequent_issue: 'N/A',
    frequently_reported_issues: { by_category: [], by_keyword: [] },
    categories: {},
    sentiments: {},
    emotions: {},
    risk_levels: {},
    threat_types: {},
  };

  const topKeywords = defaultStats.frequently_reported_issues?.by_keyword || [];
  const topCategories = defaultStats.frequently_reported_issues?.by_category || [];

  return (
    <div className="space-y-8">
      {/* Header & Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800/80 pb-5">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-400 bg-emerald-950/80 px-2 py-0.5 rounded border border-emerald-800/60">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" /> Live Telemetry
            </span>
            <span className="text-xs text-slate-500">• Port 8000 Sync</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            Security Intelligence Dashboard
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Real-time heuristic threat detection, customer sentiment aggregation, and phishing analytics
          </p>
        </div>

        <div className="flex items-center gap-3 self-start sm:self-auto">
          <button
            type="button"
            onClick={refetch}
            className="flex items-center gap-1.5 rounded-lg border border-slate-700 bg-slate-800/80 px-3 py-2 text-xs sm:text-sm font-medium text-slate-300 hover:bg-slate-700 hover:text-white transition"
          >
            <RefreshCw className="h-4 w-4" /> Refresh
          </button>
          <button
            type="button"
            onClick={onNavigateToAnalyze}
            className="flex items-center gap-2 rounded-lg bg-sky-600 px-4 py-2 text-xs sm:text-sm font-semibold text-white shadow-lg shadow-sky-950 hover:bg-sky-500 transition"
          >
            Analyze Message <ArrowRight className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        <KPICard
          title="Total Tickets"
          value={defaultStats.total_conversations}
          subtitle="Analyzed communications"
          icon={<Inbox className="h-5 w-5 text-sky-400" />}
          variant="default"
        />
        <KPICard
          title="High Risk Alerts"
          value={defaultStats.high_risk_count}
          subtitle="Critical & High threats"
          icon={<ShieldAlert className="h-5 w-5 text-rose-400" />}
          variant="danger"
        />
        <KPICard
          title="Pending Triage"
          value={defaultStats.pending_count}
          subtitle="Under active review"
          icon={<Clock className="h-5 w-5 text-amber-400" />}
          variant="warning"
        />
        <KPICard
          title="Resolved Cases"
          value={defaultStats.resolved_count}
          subtitle="Safely resolved"
          icon={<CheckCircle2 className="h-5 w-5 text-emerald-400" />}
          variant="success"
        />
        <KPICard
          title="Top Complaint"
          value={defaultStats.most_common_complaint || 'N/A'}
          subtitle={`${defaultStats.total_complaints ?? 0} total complaints`}
          icon={<FolderOpen className="h-5 w-5 text-indigo-400" />}
          variant="info"
        />
        <KPICard
          title="Frequent Keyword"
          value={defaultStats.most_frequent_issue ? `#${defaultStats.most_frequent_issue}` : 'N/A'}
          subtitle="Trending issue signal"
          icon={<TrendingUp className="h-5 w-5 text-teal-400" />}
          variant="default"
        />
      </div>

      {/* Analytics Visualizations Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Risk Distribution */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 shadow-lg">
          <div className="flex items-center justify-between mb-3">
            <div>
              <h3 className="text-base font-bold text-white">Risk Level Severity Distribution</h3>
              <p className="text-xs text-slate-400">
                Threat severity distribution across all stored communications
              </p>
            </div>
            <span className="text-[10px] font-mono text-slate-500 uppercase bg-slate-950 px-2 py-1 rounded border border-slate-800">
              Heuristic + AI
            </span>
          </div>
          <RiskBarChart data={defaultStats.risk_levels} />
        </div>

        {/* Category Breakdown */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 shadow-lg">
          <div className="flex items-center justify-between mb-3">
            <div>
              <h3 className="text-base font-bold text-white">Ticket Categories</h3>
              <p className="text-xs text-slate-400">
                Classification breakdown across Billing, Account, Security, etc.
              </p>
            </div>
            <span className="text-[10px] font-mono text-slate-500 uppercase bg-slate-950 px-2 py-1 rounded border border-slate-800">
              Gemini Classifier
            </span>
          </div>
          <CategoryPieChart data={defaultStats.categories} />
        </div>

        {/* Threat Signatures */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 shadow-lg">
          <div className="flex items-center justify-between mb-3">
            <div>
              <h3 className="text-base font-bold text-white">Attack Vectors & Threat Types</h3>
              <p className="text-xs text-slate-400">
                Identified phishing signatures and social engineering vectors
              </p>
            </div>
            <span className="text-[10px] font-mono text-slate-500 uppercase bg-slate-950 px-2 py-1 rounded border border-slate-800">
              Security Rules
            </span>
          </div>
          <ThreatTypeChart data={defaultStats.threat_types} />
        </div>

        {/* Sentiment Analysis */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 shadow-lg">
          <div className="flex items-center justify-between mb-3">
            <div>
              <h3 className="text-base font-bold text-white">Sentiment & Coercion Indicators</h3>
              <p className="text-xs text-slate-400">
                Urgency and emotional pressure index detected in customer threads
              </p>
            </div>
            <span className="text-[10px] font-mono text-slate-500 uppercase bg-slate-950 px-2 py-1 rounded border border-slate-800">
              Tone Analysis
            </span>
          </div>
          <SentimentChart data={defaultStats.sentiments} />
        </div>
      </div>

      {/* Frequently Reported Issues & Keywords Cloud */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 shadow-lg">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4">
          <div className="flex items-center gap-2">
            <div className="rounded-lg bg-sky-950/80 p-2 text-sky-400 border border-sky-800/50">
              <Tag className="h-4 w-4" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">Trending Issues & Aggregated Keywords</h3>
              <p className="text-xs text-slate-400">
                High-frequency tokens and categories aggregated from real customer support interactions
              </p>
            </div>
          </div>
          <span className="text-xs font-mono text-slate-400">
            {topKeywords.length} Keywords Tracked
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
          {/* Top Keywords */}
          <div>
            <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
              Top Keywords By Frequency:
            </h4>
            {topKeywords.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {topKeywords.map(([kw, count], idx) => (
                  <span
                    key={idx}
                    className="inline-flex items-center gap-1.5 rounded-lg bg-slate-950 px-3 py-1 text-xs font-mono text-slate-200 border border-slate-800 hover:border-slate-700 transition"
                  >
                    <span className="text-sky-400 font-bold">#{kw}</span>
                    <span className="rounded-full bg-slate-800 px-1.5 py-0.2 text-[10px] text-slate-400">
                      {count}
                    </span>
                  </span>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-500 italic">No keyword frequencies calculated yet</p>
            )}
          </div>

          {/* Top Issue Categories */}
          <div>
            <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
              Category Volume Breakdown:
            </h4>
            {topCategories.length > 0 ? (
              <div className="space-y-1.5">
                {topCategories.map(([cat, count], idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between rounded-lg bg-slate-950/80 px-3 py-1.5 border border-slate-800 text-xs"
                  >
                    <span className="font-medium text-slate-300">{cat}</span>
                    <span className="font-mono text-sky-400 font-semibold">{count} tickets</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-500 italic">No categories recorded</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
