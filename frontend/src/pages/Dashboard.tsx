import React from 'react';
import {
  ShieldAlert,
  CheckCircle2,
  Clock,
  Inbox,
  AlertTriangle,
  RefreshCw,
  ArrowRight,
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
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-sky-500 border-t-transparent" />
          <p className="text-sm font-medium text-slate-400">Loading security analytics...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-xl border border-rose-900/50 bg-rose-950/20 p-8 text-center my-6">
        <AlertTriangle className="mx-auto h-12 w-12 text-rose-400 mb-3" />
        <h3 className="text-lg font-bold text-rose-300">Unable to load dashboard data</h3>
        <p className="mt-1 text-sm text-slate-400">{error}</p>
        <button
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
    high_risk_count: 0,
    resolved_count: 0,
    pending_count: 0,
    categories: {},
    sentiments: {},
    emotions: {},
    risk_levels: {},
    threat_types: {},
  };

  return (
    <div className="space-y-8">
      {/* Header & Quick Action */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            Security Intelligence Dashboard
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Real-time heuristic threat detection and AI sentiment analytics
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={refetch}
            className="flex items-center gap-1.5 rounded-lg border border-slate-700 bg-slate-800/80 px-3 py-2 text-xs sm:text-sm font-medium text-slate-300 hover:bg-slate-700 transition"
          >
            <RefreshCw className="h-4 w-4" /> Refresh
          </button>
          <button
            onClick={onNavigateToAnalyze}
            className="flex items-center gap-2 rounded-lg bg-sky-600 px-4 py-2 text-xs sm:text-sm font-semibold text-white shadow-md hover:bg-sky-500 transition"
          >
            Analyze Message <ArrowRight className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* KPI Cards Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard
          title="Total Conversations"
          value={defaultStats.total_conversations}
          subtitle="Analyzed communications"
          icon={<Inbox className="h-5 w-5 text-sky-400" />}
          variant="default"
        />
        <KPICard
          title="High Risk Alerts"
          value={defaultStats.high_risk_count}
          subtitle="Critical & High risk items"
          icon={<ShieldAlert className="h-5 w-5 text-rose-400" />}
          variant="danger"
        />
        <KPICard
          title="Pending Triage"
          value={defaultStats.pending_count}
          subtitle="Flagged or Under Review"
          icon={<Clock className="h-5 w-5 text-amber-400" />}
          variant="warning"
        />
        <KPICard
          title="Resolved Cases"
          value={defaultStats.resolved_count}
          subtitle="Safely resolved or dismissed"
          icon={<CheckCircle2 className="h-5 w-5 text-emerald-400" />}
          variant="success"
        />
      </div>

      {/* Analytics Visualizations Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Risk Distribution */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 shadow">
          <h3 className="text-base font-bold text-white mb-1">Risk Level Distribution</h3>
          <p className="text-xs text-slate-400 mb-4">
            Aggregated threat severity across all analyzed messages
          </p>
          <RiskBarChart data={defaultStats.risk_levels} />
        </div>

        {/* Category Breakdown */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 shadow">
          <h3 className="text-base font-bold text-white mb-1">Message Classifications</h3>
          <p className="text-xs text-slate-400 mb-4">
            Proportion of Phishing, Malicious, Spam, and Clean communications
          </p>
          <CategoryPieChart data={defaultStats.categories} />
        </div>

        {/* Threat Signatures */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 shadow">
          <h3 className="text-base font-bold text-white mb-1">Detected Threat Types</h3>
          <p className="text-xs text-slate-400 mb-4">
            Breakdown of specific attack vectors and fraudulent behaviors
          </p>
          <ThreatTypeChart data={defaultStats.threat_types} />
        </div>

        {/* Sentiment Analysis */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 shadow">
          <h3 className="text-base font-bold text-white mb-1">Sentiment & Urgency Index</h3>
          <p className="text-xs text-slate-400 mb-4">
            Emotional manipulation and urgency indicators identified by Gemini
          </p>
          <SentimentChart data={defaultStats.sentiments} />
        </div>
      </div>
    </div>
  );
};
