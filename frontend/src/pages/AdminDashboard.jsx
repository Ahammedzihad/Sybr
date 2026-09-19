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
  AlertTriangle
} from 'lucide-react';
import { fetchAdminDashboard } from '../api';

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
              Admin Console
            </span>
            <span className="text-xs text-neutral-400">System Oversight & Security Governance</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white">
            Platform Operations & Threat Intelligence
          </h1>
          <p className="text-xs text-neutral-300 max-w-xl">
            Monitor platform-wide conversation ingestion, user tenancy, role access, and real-time cybersecurity telemetry.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="p-2 rounded-xl border border-neutral-700 bg-neutral-800/80 text-neutral-300 hover:bg-neutral-700 active:scale-95 transition"
            title="Refresh dashboard"
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
          </button>
          
          <Link
            to="/admin/users"
            className="inline-flex items-center gap-1.5 px-4 py-2 bg-white text-neutral-900 rounded-xl text-xs font-semibold hover:bg-neutral-100 transition active:scale-95"
          >
            <Users className="w-4 h-4" />
            <span>Manage Users</span>
          </Link>
        </div>
      </div>

      {/* Platform KPIs */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        
        {/* Total Users */}
        <div className="bg-white p-5 rounded-2xl border border-neutral-200/80 shadow-sm space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-neutral-500">Registered Accounts</span>
            <div className="w-8 h-8 rounded-xl bg-violet-50 text-violet-600 flex items-center justify-center">
              <Users className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-bold tracking-tight text-neutral-900">
            {loading ? '-' : data?.total_users ?? 0}
          </div>
          <div className="text-[11px] text-neutral-400">
            {loading ? 'Loading...' : `${data?.total_customers ?? 0} Customers • ${data?.total_admins ?? 0} Admins`}
          </div>
        </div>

        {/* Total Platform Conversations */}
        <div className="bg-white p-5 rounded-2xl border border-neutral-200/80 shadow-sm space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-neutral-500">Platform Ingested Tickets</span>
            <div className="w-8 h-8 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
              <FileText className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-bold tracking-tight text-neutral-900">
            {loading ? '-' : data?.total_platform_conversations ?? 0}
          </div>
          <div className="text-[11px] text-neutral-400">
            System-wide chat, email, and CSV logs
          </div>
        </div>

        {/* Total Threats */}
        <div className="bg-white p-5 rounded-2xl border border-neutral-200/80 shadow-sm space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-neutral-500">Threat Interceptions</span>
            <div className="w-8 h-8 rounded-xl bg-rose-50 text-rose-600 flex items-center justify-center">
              <ShieldAlert className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-bold tracking-tight text-neutral-900">
            {loading ? '-' : data?.total_platform_threats ?? 0}
          </div>
          <div className="text-[11px] text-rose-600 font-medium">
            Phishing, credential lures, lookalikes
          </div>
        </div>

        {/* High Risk Cases */}
        <div className="bg-white p-5 rounded-2xl border border-neutral-200/80 shadow-sm space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-neutral-500">High & Critical Risks</span>
            <div className="w-8 h-8 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center">
              <AlertTriangle className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-bold tracking-tight text-neutral-900">
            {loading ? '-' : data?.high_risk_threats ?? 0}
          </div>
          <div className="text-[11px] text-amber-700 font-medium">
            Requiring security team escalation
          </div>
        </div>

      </div>

      {/* Operational Telemetry & Quick Links */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* System Health Card */}
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
              <span className="font-mono text-neutral-700">{data?.ai_status?.model || 'gemini-2.5-flash'}</span>
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

        {/* Quick Admin Actions */}
        <div className="bg-white p-5 rounded-2xl border border-neutral-200/80 shadow-sm space-y-4 lg:col-span-2">
          <div className="flex items-center justify-between border-b border-neutral-100 pb-3">
            <h2 className="text-xs font-bold text-neutral-900 uppercase tracking-wide">Administrative Actions</h2>
            <span className="text-[11px] text-neutral-400">Governance & Oversight</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <Link
              to="/admin/users"
              className="p-4 rounded-xl border border-neutral-200/80 hover:border-neutral-900/30 hover:bg-neutral-50/60 transition group space-y-2 block"
            >
              <div className="w-8 h-8 rounded-lg bg-violet-50 text-violet-600 flex items-center justify-center">
                <Users className="w-4 h-4" />
              </div>
              <h3 className="text-xs font-bold text-neutral-900 group-hover:text-violet-600 transition">
                User Management
              </h3>
              <p className="text-[11px] text-neutral-500 leading-relaxed">
                Review tenant accounts, modify roles, and oversee permissions.
              </p>
            </Link>

            <Link
              to="/admin/conversations"
              className="p-4 rounded-xl border border-neutral-200/80 hover:border-neutral-900/30 hover:bg-neutral-50/60 transition group space-y-2 block"
            >
              <div className="w-8 h-8 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center">
                <FileText className="w-4 h-4" />
              </div>
              <h3 className="text-xs font-bold text-neutral-900 group-hover:text-blue-600 transition">
                Platform Oversight
              </h3>
              <p className="text-[11px] text-neutral-500 leading-relaxed">
                Inspect conversation logs across all customer workspaces.
              </p>
            </Link>

            <Link
              to="/admin/audit-logs"
              className="p-4 rounded-xl border border-neutral-200/80 hover:border-neutral-900/30 hover:bg-neutral-50/60 transition group space-y-2 block"
            >
              <div className="w-8 h-8 rounded-lg bg-neutral-100 text-neutral-700 flex items-center justify-center">
                <History className="w-4 h-4" />
              </div>
              <h3 className="text-xs font-bold text-neutral-900 group-hover:text-neutral-900 transition">
                Security Audit Log
              </h3>
              <p className="text-[11px] text-neutral-500 leading-relaxed">
                Trace role changes, privileged actions, and administrative operations.
              </p>
            </Link>
          </div>
        </div>

      </div>

      {/* Recent Security Audit Logs */}
      <div className="bg-white rounded-2xl border border-neutral-200/80 shadow-sm overflow-hidden">
        <div className="p-5 border-b border-neutral-100 flex items-center justify-between">
          <div>
            <h2 className="text-sm font-bold text-neutral-900">Recent Security Audit Trail</h2>
            <p className="text-xs text-neutral-500">Immutable record of security-sensitive operations.</p>
          </div>
          <Link
            to="/admin/audit-logs"
            className="inline-flex items-center gap-1 text-xs text-[#0071e3] font-medium hover:underline"
          >
            <span>View full audit log</span>
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
                <tr className="border-b border-neutral-100 bg-neutral-50/50 text-[11px] font-semibold text-neutral-500 uppercase tracking-wider">
                  <th className="py-3 px-4">Timestamp</th>
                  <th className="py-3 px-4">Actor</th>
                  <th className="py-3 px-4">Action</th>
                  <th className="py-3 px-4">Target Resource</th>
                  <th className="py-3 px-4">Metadata</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-100 font-mono text-[11px]">
                {data.recent_audit_logs.map((log) => (
                  <tr key={log.id} className="hover:bg-neutral-50/60 transition">
                    <td className="py-3 px-4 text-neutral-500">
                      {new Date(log.created_at).toLocaleString()}
                    </td>
                    <td className="py-3 px-4 font-sans font-medium text-neutral-800">
                      {log.actor_email || log.actor_user_id}
                    </td>
                    <td className="py-3 px-4 font-sans">
                      <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-neutral-100 text-neutral-800">
                        {log.action}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-neutral-600">
                      {log.target_resource_id || '-'}
                    </td>
                    <td className="py-3 px-4 text-neutral-400 max-w-xs truncate">
                      {JSON.stringify(log.metadata)}
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
