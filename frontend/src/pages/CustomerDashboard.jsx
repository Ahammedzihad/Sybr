import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  MessageSquare, 
  ShieldAlert, 
  Clock, 
  CheckCircle2, 
  Plus, 
  ArrowRight, 
  Sparkles,
  ExternalLink,
  ShieldCheck,
  RefreshCw
} from 'lucide-react';
import { fetchCustomerDashboard, getCurrentUser } from '../api';
import { PriorityBadge, RiskBadge, CategoryBadge } from '../components/Badges';

export default function CustomerDashboard() {
  const user = getCurrentUser();
  const [data, setData] = useState({
    total_my_conversations: 0,
    my_threats_detected: 0,
    my_pending_reviews: 0,
    my_resolved_tickets: 0,
    recent_activity: [],
  });
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const loadData = async () => {
    try {
      const res = await fetchCustomerDashboard();
      setData(res);
    } catch (err) {
      console.error('Failed to load customer dashboard:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    loadData();
  };

  const displayName = user?.display_name || user?.email?.split('@')[0] || 'Customer';

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 animate-fade-in">
      
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white p-6 rounded-2xl border border-neutral-200/80 shadow-sm">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-semibold tracking-wide uppercase bg-emerald-50 text-emerald-700 border border-emerald-200">
              Customer Workspace
            </span>
            <span className="text-xs text-neutral-400">| Tenant ID: {user?.id?.slice(0, 12) || 'demo'}...</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-neutral-900">
            Welcome back, {displayName}
          </h1>
          <p className="text-xs text-neutral-500 max-w-xl leading-relaxed">
            Your private support intelligence and threat monitoring hub. Only interactions associated with your account are visible here.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="p-2 rounded-xl border border-neutral-200 text-neutral-600 hover:bg-neutral-50 active:scale-95 transition"
            title="Refresh dashboard"
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
          </button>
          
          <Link
            to="/analyze"
            className="inline-flex items-center gap-2 px-4 py-2 bg-neutral-900 hover:bg-neutral-800 text-white rounded-xl text-xs font-semibold shadow-sm transition active:scale-95"
          >
            <Plus className="w-4 h-4" />
            <span>Analyze New Ticket</span>
          </Link>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        
        {/* Card 1: My Conversations */}
        <div className="bg-white p-5 rounded-2xl border border-neutral-200/80 shadow-sm space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-neutral-500">My Analyzed Tickets</span>
            <div className="w-8 h-8 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
              <MessageSquare className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-bold tracking-tight text-neutral-900">
            {loading ? '-' : data.total_my_conversations}
          </div>
          <div className="text-[11px] text-neutral-400">
            Ingested across chat, email, and tickets
          </div>
        </div>

        {/* Card 2: Threats Detected */}
        <div className="bg-white p-5 rounded-2xl border border-neutral-200/80 shadow-sm space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-neutral-500">Threat Alerts Intercepted</span>
            <div className="w-8 h-8 rounded-xl bg-rose-50 text-rose-600 flex items-center justify-center">
              <ShieldAlert className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-bold tracking-tight text-neutral-900">
            {loading ? '-' : data.my_threats_detected}
          </div>
          <div className="text-[11px] text-rose-600 font-medium">
            Phishing, credential lures, or lookalikes
          </div>
        </div>

        {/* Card 3: Pending Reviews */}
        <div className="bg-white p-5 rounded-2xl border border-neutral-200/80 shadow-sm space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-neutral-500">Pending Resolutions</span>
            <div className="w-8 h-8 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center">
              <Clock className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-bold tracking-tight text-neutral-900">
            {loading ? '-' : data.my_pending_reviews}
          </div>
          <div className="text-[11px] text-neutral-400">
            Awaiting agent follow-up or confirmation
          </div>
        </div>

        {/* Card 4: Resolved Tickets */}
        <div className="bg-white p-5 rounded-2xl border border-neutral-200/80 shadow-sm space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-neutral-500">Resolved Cases</span>
            <div className="w-8 h-8 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center">
              <CheckCircle2 className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-bold tracking-tight text-neutral-900">
            {loading ? '-' : data.my_resolved_tickets}
          </div>
          <div className="text-[11px] text-emerald-600 font-medium">
            Successfully closed interactions
          </div>
        </div>

      </div>

      {/* Quick Action Callout */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-neutral-900 to-neutral-800 text-white flex flex-col md:flex-row items-center justify-between gap-6 shadow-md">
        <div className="space-y-1.5 text-center md:text-left">
          <div className="inline-flex items-center gap-1.5 text-amber-400 text-xs font-medium">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Dual-Call Intelligence Engine</span>
          </div>
          <h3 className="text-lg font-bold">Have a suspicious message or urgent support ticket?</h3>
          <p className="text-xs text-neutral-300 max-w-xl">
            Submit customer messages or email threads into the Live Threat Analyzer for immediate sentiment, root cause categorization, and automated phishing risk evaluation.
          </p>
        </div>
        <Link
          to="/analyze"
          className="inline-flex items-center gap-2 px-5 py-2.5 bg-white text-neutral-900 rounded-xl text-xs font-bold hover:bg-neutral-100 transition shrink-0 active:scale-95"
        >
          <span>Open Live Analyzer</span>
          <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      {/* Recent Activity Table */}
      <div className="bg-white rounded-2xl border border-neutral-200/80 shadow-sm overflow-hidden">
        <div className="p-5 border-b border-neutral-100 flex items-center justify-between">
          <div>
            <h2 className="text-sm font-bold text-neutral-900">My Recent Analyzed Tickets</h2>
            <p className="text-xs text-neutral-500">Your recent interactions and real-time security findings.</p>
          </div>
          <Link
            to="/conversations"
            className="inline-flex items-center gap-1 text-xs text-[#0071e3] font-medium hover:underline"
          >
            <span>View all my conversations</span>
            <ArrowRight className="w-3 h-3" />
          </Link>
        </div>

        {loading ? (
          <div className="p-12 text-center text-xs text-neutral-400">Loading your conversations...</div>
        ) : data.recent_activity.length === 0 ? (
          <div className="p-12 text-center space-y-3">
            <div className="w-10 h-10 rounded-full bg-neutral-100 text-neutral-400 flex items-center justify-center mx-auto">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div className="text-sm font-semibold text-neutral-700">No conversations analyzed yet</div>
            <p className="text-xs text-neutral-400 max-w-sm mx-auto">
              When you submit tickets to the Live Analyzer or import support logs, they will appear here under your tenant account.
            </p>
            <Link
              to="/analyze"
              className="inline-flex items-center gap-1.5 text-xs text-[#0071e3] font-medium hover:underline pt-1"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Submit your first ticket</span>
            </Link>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-neutral-100 bg-neutral-50/50 text-[11px] font-semibold text-neutral-500 uppercase tracking-wider">
                  <th className="py-3 px-4">Ticket ID</th>
                  <th className="py-3 px-4">Issue Description</th>
                  <th className="py-3 px-4">Category</th>
                  <th className="py-3 px-4">Priority</th>
                  <th className="py-3 px-4">Threat Risk</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-100">
                {data.recent_activity.map((item) => (
                  <tr key={item.id} className="hover:bg-neutral-50/60 transition group">
                    <td className="py-3 px-4 font-mono text-[11px] text-neutral-500 font-medium">
                      {item.id}
                    </td>
                    <td className="py-3 px-4 font-medium text-neutral-900 max-w-xs truncate">
                      {item.issue || 'Customer ticket inquiry'}
                    </td>
                    <td className="py-3 px-4">
                      <CategoryBadge category={item.category || 'Other'} />
                    </td>
                    <td className="py-3 px-4">
                      <PriorityBadge priority={item.priority || 'Low'} />
                    </td>
                    <td className="py-3 px-4">
                      <RiskBadge risk={item.risk_level || 'Low'} />
                    </td>
                    <td className="py-3 px-4 text-right">
                      <Link
                        to={`/conversations/${item.id}`}
                        className="inline-flex items-center gap-1 text-[11px] text-[#0071e3] font-medium hover:underline"
                      >
                        <span>Inspect</span>
                        <ExternalLink className="w-3 h-3" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

    </div>
  );
}
