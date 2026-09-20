import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  Users, 
  ShieldAlert, 
  Database, 
  Cpu, 
  FileText, 
  ArrowRight, 
  RefreshCw, 
  ShieldCheck, 
  History,
  Activity,
  AlertTriangle,
  Flag,
  CheckCircle2,
  Clock,
  PieChart,
  BarChart3,
  Flame,
  Shield,
  ExternalLink
} from 'lucide-react';
import { fetchAdminDashboard } from '../api';
import { PriorityBadge, RiskBadge, CategoryBadge } from '../components/Badges';

export default function AdminDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const loadData = async () => {
    try {
      const res = await fetchAdminDashboard();
      setData(res);
    } catch (err) {
      console.error('Failed to load admin dashboard:', err);
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

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 animate-fade-in text-left">
      
      {/* Admin Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-gradient-to-r from-neutral-900 to-neutral-800 text-white p-6 rounded-2xl shadow-sm">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-semibold tracking-wide uppercase bg-violet-500/20 text-violet-300 border border-violet-500/40">
              Admin Intelligence Portal
            </span>
            <span className="text-xs text-neutral-400">System Oversight & Security Governance</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white">
            Operational Overview & Threat Intelligence
          </h1>
          <p className="text-xs text-neutral-300 max-w-2xl">
            Real-time platform oversight: inspect conversations, calibrate AI classifications, monitor cyber threats, and track multi-tenant user access.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="p-2 rounded-xl border border-neutral-700 bg-neutral-800/80 text-neutral-300 hover:bg-neutral-700 active:scale-95 transition"
            title="Refresh dashboard"
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
          </button>
          
          <Link
            to="/admin/conversations"
            className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-neutral-800 hover:bg-neutral-700 text-white rounded-xl text-xs font-semibold border border-neutral-700 transition active:scale-95"
          >
            <FileText className="w-4 h-4" />
            <span>Admin Inbox</span>
          </Link>

          <Link
            to="/admin/security"
            className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-rose-600/90 hover:bg-rose-600 text-white rounded-xl text-xs font-semibold transition active:scale-95 shadow-xs"
          >
            <Shield className="w-4 h-4" />
            <span>Security Center</span>
          </Link>
        </div>
      </div>

      {/* Operational KPI Grid (Section 9) */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3.5">
        
        {/* Total Platform Conversations */}
        <div className="bg-white p-4 rounded-2xl border border-neutral-200/80 shadow-xs space-y-2">
          <div className="flex items-center justify-between text-neutral-500">
            <span className="text-[11px] font-medium">Total Ingested</span>
            <FileText className="w-3.5 h-3.5 text-blue-600" />
          </div>
          <div className="text-2xl font-bold tracking-tight text-neutral-900">
            {loading ? '-' : data?.total_platform_conversations ?? 0}
          </div>
          <div className="text-[10px] text-neutral-400">All channels & CSVs</div>
        </div>

        {/* Threat Interceptions */}
        <div className="bg-white p-4 rounded-2xl border border-neutral-200/80 shadow-xs space-y-2">
          <div className="flex items-center justify-between text-neutral-500">
            <span className="text-[11px] font-medium">Cyber Threats</span>
            <ShieldAlert className="w-3.5 h-3.5 text-rose-600" />
          </div>
          <div className="text-2xl font-bold tracking-tight text-rose-600">
            {loading ? '-' : data?.total_platform_threats ?? 0}
          </div>
          <div className="text-[10px] text-rose-500">Phishing & OTP lures</div>
        </div>

        {/* High/Critical Risk */}
        <div className="bg-white p-4 rounded-2xl border border-neutral-200/80 shadow-xs space-y-2">
          <div className="flex items-center justify-between text-neutral-500">
            <span className="text-[11px] font-medium">Critical/High</span>
            <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
          </div>
          <div className="text-2xl font-bold tracking-tight text-amber-600">
            {loading ? '-' : data?.high_risk_threats ?? 0}
          </div>
          <div className="text-[10px] text-amber-600">Urgent escalation</div>
        </div>

        {/* Review Queue */}
        <div className="bg-white p-4 rounded-2xl border border-neutral-200/80 shadow-xs space-y-2">
          <div className="flex items-center justify-between text-neutral-500">
            <span className="text-[11px] font-medium">Review Queue</span>
            <Flag className="w-3.5 h-3.5 text-indigo-600" />
          </div>
          <div className="text-2xl font-bold tracking-tight text-indigo-600">
            {loading ? '-' : data?.needs_review_count ?? 0}
          </div>
          <div className="text-[10px] text-indigo-500">Requires supervisor</div>
        </div>

        {/* Unresolved Tickets */}
        <div className="bg-white p-4 rounded-2xl border border-neutral-200/80 shadow-xs space-y-2">
          <div className="flex items-center justify-between text-neutral-500">
            <span className="text-[11px] font-medium">Unresolved</span>
            <Clock className="w-3.5 h-3.5 text-amber-500" />
          </div>
          <div className="text-2xl font-bold tracking-tight text-neutral-900">
            {loading ? '-' : data?.unresolved_count ?? 0}
          </div>
          <div className="text-[10px] text-neutral-400">Pending customer fix</div>
        </div>

        {/* Registered Accounts */}
        <div className="bg-white p-4 rounded-2xl border border-neutral-200/80 shadow-xs space-y-2">
          <div className="flex items-center justify-between text-neutral-500">
            <span className="text-[11px] font-medium">Tenants</span>
            <Users className="w-3.5 h-3.5 text-violet-600" />
          </div>
          <div className="text-2xl font-bold tracking-tight text-neutral-900">
            {loading ? '-' : data?.total_users ?? 0}
          </div>
          <div className="text-[10px] text-neutral-400">{data?.total_customers ?? 0} Customers • {data?.total_admins ?? 0} Admins</div>
        </div>

      </div>

      {/* Triage Queue: Needs Attention Cases */}
      <div className="bg-white rounded-2xl border border-neutral-200/80 shadow-sm overflow-hidden">
        <div className="p-5 border-b border-neutral-100 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-rose-500 animate-ping" />
              <h2 className="text-sm font-bold text-neutral-900">Triage Queue — Requiring Attention</h2>
            </div>
            <p className="text-xs text-neutral-500">Cases flagged for high risk, supervisor review, or critical priority.</p>
          </div>
          <Link
            to="/admin/conversations?risk=Critical"
            className="inline-flex items-center gap-1 text-xs text-[#0071e3] font-medium hover:underline self-start sm:self-auto"
          >
            <span>View all in operational inbox</span>
            <ArrowRight className="w-3 h-3" />
          </Link>
        </div>

        {loading ? (
          <div className="p-8 text-center text-xs text-neutral-400">Loading triage cases...</div>
        ) : !data?.needs_attention?.length ? (
          <div className="p-8 text-center text-xs text-neutral-400">
            No urgent triage cases currently pending. All conversations within normal parameters.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-neutral-100 bg-neutral-50/50 text-[11px] font-semibold text-neutral-500 uppercase tracking-wider">
                  <th className="py-3 px-4">Ticket ID</th>
                  <th className="py-3 px-4">Customer Issue</th>
                  <th className="py-3 px-4">Category</th>
                  <th className="py-3 px-4">Priority</th>
                  <th className="py-3 px-4">Threat Risk</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-100">
                {data.needs_attention.map((c) => (
                  <tr key={c.id} className="hover:bg-neutral-50/60 transition group">
                    <td className="py-3 px-4 font-mono text-[11px] font-medium text-neutral-500">
                      {c.id}
                    </td>
                    <td className="py-3 px-4 font-medium text-neutral-900 max-w-xs truncate">
                      {c.issue || 'Customer Ticket'}
                    </td>
                    <td className="py-3 px-4">
                      <CategoryBadge category={c.category} />
                    </td>
                    <td className="py-3 px-4">
                      <PriorityBadge priority={c.priority} />
                    </td>
                    <td className="py-3 px-4">
                      <RiskBadge risk={c.risk_level} />
                    </td>
                    <td className="py-3 px-4 font-mono text-[11px] text-neutral-600">
                      {c.processing_status}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <Link
                        to={`/conversations/${c.id}`}
                        className="inline-flex items-center gap-1 text-[11px] text-[#0071e3] font-semibold hover:underline"
                      >
                        <span>Examine</span>
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

      {/* Operational Navigation Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Link
          to="/admin/analytics"
          className="p-5 bg-white rounded-2xl border border-neutral-200/80 hover:border-neutral-900/30 hover:shadow-sm transition group space-y-2 block"
        >
          <div className="w-8 h-8 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
            <BarChart3 className="w-4 h-4" />
          </div>
          <h3 className="text-xs font-bold text-neutral-900 group-hover:text-blue-600 transition">
            Operational & Category Analytics
          </h3>
          <p className="text-[11px] text-neutral-500 leading-relaxed">
            Drill down into category volume, issue labels, AI vs fallback rates, and human calibration activity.
          </p>
        </Link>

        <Link
          to="/admin/security"
          className="p-5 bg-white rounded-2xl border border-neutral-200/80 hover:border-neutral-900/30 hover:shadow-sm transition group space-y-2 block"
        >
          <div className="w-8 h-8 rounded-xl bg-rose-50 text-rose-600 flex items-center justify-center">
            <ShieldAlert className="w-4 h-4" />
          </div>
          <h3 className="text-xs font-bold text-neutral-900 group-hover:text-rose-600 transition">
            Security Intelligence Center
          </h3>
          <p className="text-[11px] text-neutral-500 leading-relaxed">
            Monitor phishing attacks, lookalike brand domains, credential harvesters, and malicious senders.
          </p>
        </Link>

        <Link
          to="/admin/customers"
          className="p-5 bg-white rounded-2xl border border-neutral-200/80 hover:border-neutral-900/30 hover:shadow-sm transition group space-y-2 block"
        >
          <div className="w-8 h-8 rounded-xl bg-violet-50 text-violet-600 flex items-center justify-center">
            <Users className="w-4 h-4" />
          </div>
          <h3 className="text-xs font-bold text-neutral-900 group-hover:text-violet-600 transition">
            Customer Directory & History
          </h3>
          <p className="text-[11px] text-neutral-500 leading-relaxed">
            Inspect tenant accounts, cross-customer support histories, and tenant-specific threat incidents.
          </p>
        </Link>
      </div>

      {/* System Telemetry & Recent Security Audit Logs */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Telemetry Card */}
        <div className="bg-white p-5 rounded-2xl border border-neutral-200/80 shadow-sm space-y-4 lg:col-span-1">
          <div className="flex items-center justify-between border-b border-neutral-100 pb-3">
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-emerald-600" />
              <h2 className="text-xs font-bold text-neutral-900 uppercase tracking-wide">System Telemetry</h2>
            </div>
            <Link to="/health" className="text-[11px] text-[#0071e3] hover:underline font-medium">
              Full Status
            </Link>
          </div>

          <div className="space-y-3 text-xs">
            <div className="flex items-center justify-between py-1.5 border-b border-neutral-50">
              <span className="text-neutral-500">AI Intelligence Provider</span>
              <span className="font-semibold text-neutral-800">{data?.ai_status?.provider || 'Google Gemini'}</span>
            </div>

            <div className="flex items-center justify-between py-1.5 border-b border-neutral-50">
              <span className="text-neutral-500">Primary AI Model</span>
              <span className="font-mono text-neutral-700">{data?.ai_status?.model || 'gemini-3.6-flash'}</span>
            </div>

            <div className="flex items-center justify-between py-1.5 border-b border-neutral-50">
              <span className="text-neutral-500">Fallback Engine</span>
              <span className="font-semibold text-emerald-700">Deterministic Rules Active</span>
            </div>

            <div className="flex items-center justify-between py-1.5 border-b border-neutral-50">
              <span className="text-neutral-500">Database Layer</span>
              <span className="font-mono text-neutral-700 capitalize">
                {data?.database_status?.mode === 'supabase_postgresql' ? 'Supabase PostgreSQL' : 'Local SQLite Dual-Write'}
              </span>
            </div>

            <div className="flex items-center justify-between py-1.5">
              <span className="text-neutral-500">Row Level Security</span>
              <span className="inline-flex items-center gap-1 font-semibold text-emerald-600">
                <ShieldCheck className="w-3.5 h-3.5" />
                <span>Enforced</span>
              </span>
            </div>
          </div>
        </div>

        {/* Recent Audit Logs */}
        <div className="bg-white rounded-2xl border border-neutral-200/80 shadow-sm overflow-hidden lg:col-span-2 flex flex-col justify-between">
          <div>
            <div className="p-4 border-b border-neutral-100 flex items-center justify-between">
              <div>
                <h2 className="text-xs font-bold text-neutral-900 uppercase tracking-wide">Security Audit Trail</h2>
                <p className="text-[11px] text-neutral-500">Immutable record of administrative operations.</p>
              </div>
              <Link
                to="/admin/audit-logs"
                className="inline-flex items-center gap-1 text-[11px] text-[#0071e3] font-medium hover:underline"
              >
                <span>Full log</span>
                <ArrowRight className="w-3 h-3" />
              </Link>
            </div>

            {loading ? (
              <div className="p-8 text-center text-xs text-neutral-400">Loading audit records...</div>
            ) : !data?.recent_audit_logs?.length ? (
              <div className="p-8 text-center text-xs text-neutral-400">No security audit logs recorded yet.</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse text-xs">
                  <thead>
                    <tr className="border-b border-neutral-100 bg-neutral-50/50 text-[10px] font-semibold text-neutral-500 uppercase tracking-wider">
                      <th className="py-2.5 px-3">Timestamp</th>
                      <th className="py-2.5 px-3">Actor</th>
                      <th className="py-2.5 px-3">Action</th>
                      <th className="py-2.5 px-3">Target</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-neutral-100 font-mono text-[11px]">
                    {data.recent_audit_logs.slice(0, 5).map((log) => (
                      <tr key={log.id} className="hover:bg-neutral-50/60 transition">
                        <td className="py-2 px-3 text-neutral-500 text-[10px]">
                          {new Date(log.created_at).toLocaleTimeString()}
                        </td>
                        <td className="py-2 px-3 font-sans font-medium text-neutral-800 text-[11px]">
                          {log.actor_email || log.actor_user_id}
                        </td>
                        <td className="py-2 px-3 font-sans">
                          <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-neutral-100 text-neutral-800">
                            {log.action}
                          </span>
                        </td>
                        <td className="py-2 px-3 text-neutral-600 text-[10px]">
                          {log.target_resource_id || '-'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>

      </div>

    </div>
  );
}
