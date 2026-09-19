import React, { useState, useEffect } from 'react';
import { 
  History, 
  RefreshCw, 
  ShieldCheck, 
  Search, 
  Filter, 
  Calendar, 
  User, 
  KeyRound 
} from 'lucide-react';
import { fetchAdminAuditLogs } from '../api';

export default function AdminAuditLog() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [search, setSearch] = useState('');

  const loadLogs = async () => {
    try {
      const res = await fetchAdminAuditLogs(100);
      setLogs(res || []);
    } catch (err) {
      console.error('Failed to load audit logs:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadLogs();
  }, []);

  const filteredLogs = logs.filter((l) => {
    const q = search.toLowerCase();
    return (
      (l.action || '').toLowerCase().includes(q) ||
      (l.actor_email || '').toLowerCase().includes(q) ||
      (l.actor_user_id || '').toLowerCase().includes(q) ||
      (l.target_resource_id || '').toLowerCase().includes(q) ||
      JSON.stringify(l.metadata || {}).toLowerCase().includes(q)
    );
  });

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6 animate-fade-in text-left">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-neutral-200/80 pb-5">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-semibold tracking-wide uppercase bg-neutral-100 text-neutral-800 border border-neutral-200">
              Audit & Compliance
            </span>
            <span className="text-xs text-neutral-400">Section 27 & 79</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-neutral-900">
            Security & Role Audit Trail
          </h1>
          <p className="text-xs text-neutral-500">
            Immutable log of role modifications, administrative operations, and security-sensitive events.
          </p>
        </div>

        <button
          onClick={() => { setRefreshing(true); loadLogs(); }}
          disabled={refreshing}
          className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl border border-neutral-200 text-neutral-700 hover:bg-neutral-50 text-xs font-semibold transition active:scale-95"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin' : ''}`} />
          <span>Refresh Audit Logs</span>
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex items-center justify-between gap-4 bg-white p-4 rounded-2xl border border-neutral-200/80 shadow-sm">
        <div className="relative flex-1 max-w-sm">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-neutral-400 pointer-events-none" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search audit actions, actor, or target ID..."
            className="w-full pl-9 pr-3 py-1.5 text-xs bg-neutral-50 border border-neutral-200 rounded-xl focus:bg-white focus:border-neutral-900 outline-none transition"
          />
        </div>

        <div className="text-xs text-neutral-500">
          Showing <span className="font-semibold text-neutral-800">{filteredLogs.length}</span> recorded audit entries
        </div>
      </div>

      {/* Audit Log Table */}
      <div className="bg-white rounded-2xl border border-neutral-200/80 shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-xs text-neutral-400">Loading security audit records...</div>
        ) : filteredLogs.length === 0 ? (
          <div className="p-12 text-center text-xs text-neutral-400">No audit records match your query.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-neutral-100 bg-neutral-50/50 text-[11px] font-semibold text-neutral-500 uppercase tracking-wider">
                  <th className="py-3 px-4">Timestamp</th>
                  <th className="py-3 px-4">Action</th>
                  <th className="py-3 px-4">Actor</th>
                  <th className="py-3 px-4">Target Resource</th>
                  <th className="py-3 px-4">Event Details & Metadata</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-100 font-mono text-[11px]">
                {filteredLogs.map((log) => (
                  <tr key={log.id} className="hover:bg-neutral-50/60 transition">
                    <td className="py-3 px-4 text-neutral-500 whitespace-nowrap">
                      {new Date(log.created_at).toLocaleString()}
                    </td>

                    <td className="py-3 px-4 font-sans font-medium">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                        log.action === 'ROLE_CHANGE'
                          ? 'bg-violet-50 text-violet-700 border border-violet-200'
                          : 'bg-neutral-100 text-neutral-800'
                      }`}>
                        {log.action}
                      </span>
                    </td>

                    <td className="py-3 px-4 font-sans text-neutral-800 font-medium">
                      {log.actor_email || log.actor_user_id}
                    </td>

                    <td className="py-3 px-4 text-neutral-600 select-all">
                      {log.target_resource_id || '-'}
                    </td>

                    <td className="py-3 px-4 text-neutral-500 max-w-md truncate">
                      {typeof log.metadata === 'object' ? JSON.stringify(log.metadata) : log.metadata}
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
