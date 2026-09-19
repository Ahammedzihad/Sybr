import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  FileText, 
  Search, 
  Filter, 
  ExternalLink, 
  RefreshCw, 
  ShieldAlert, 
  User, 
  ArrowRight 
} from 'lucide-react';
import { fetchAdminConversations } from '../api';
import { PriorityBadge, RiskBadge, CategoryBadge, SentimentBadge } from '../components/Badges';

export default function AdminConversations() {
  const [conversations, setConversations] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('');
  const [risk, setRisk] = useState('');
  const [priority, setPriority] = useState('');
  const [page, setPage] = useState(1);

  const loadData = async () => {
    try {
      const res = await fetchAdminConversations({
        q: search,
        category,
        risk,
        priority,
        page,
        limit: 20,
      });
      setConversations(res.items || []);
      setTotal(res.total || 0);
    } catch (err) {
      console.error('Failed to load admin conversations:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [category, risk, priority, page]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setPage(1);
    loadData();
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6 animate-fade-in text-left">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-neutral-200/80 pb-5">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-semibold tracking-wide uppercase bg-blue-50 text-blue-700 border border-blue-200">
              Platform Oversight
            </span>
            <span className="text-xs text-neutral-400">Global Tenant Conversation Registry</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-neutral-900">
            System-Wide Conversations
          </h1>
          <p className="text-xs text-neutral-500">
            Inspect customer support inquiries and threat interceptions across all registered workspaces.
          </p>
        </div>

        <button
          onClick={() => { setRefreshing(true); loadData(); }}
          disabled={refreshing}
          className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl border border-neutral-200 text-neutral-700 hover:bg-neutral-50 text-xs font-semibold transition active:scale-95"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Filter & Search Bar */}
      <div className="bg-white p-4 rounded-2xl border border-neutral-200/80 shadow-sm space-y-3">
        <form onSubmit={handleSearchSubmit} className="flex flex-col md:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-neutral-400 pointer-events-none" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search across all conversations by text, issue, or ID..."
              className="w-full pl-9 pr-3 py-1.5 text-xs bg-neutral-50 border border-neutral-200 rounded-xl focus:bg-white focus:border-neutral-900 outline-none transition"
            />
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <select
              value={category}
              onChange={(e) => { setCategory(e.target.value); setPage(1); }}
              className="px-2.5 py-1.5 text-xs bg-neutral-50 border border-neutral-200 rounded-xl outline-none"
            >
              <option value="">All Categories</option>
              <option value="Billing/Payment">Billing/Payment</option>
              <option value="Account/Login">Account/Login</option>
              <option value="Security Concern">Security Concern</option>
              <option value="Technical Problem">Technical Problem</option>
              <option value="Product Issue">Product Issue</option>
              <option value="Other">Other</option>
            </select>

            <select
              value={risk}
              onChange={(e) => { setRisk(e.target.value); setPage(1); }}
              className="px-2.5 py-1.5 text-xs bg-neutral-50 border border-neutral-200 rounded-xl outline-none"
            >
              <option value="">All Threat Risks</option>
              <option value="Low">Low</option>
              <option value="Medium">Medium</option>
              <option value="High">High</option>
              <option value="Critical">Critical</option>
            </select>

            <select
              value={priority}
              onChange={(e) => { setPriority(e.target.value); setPage(1); }}
              className="px-2.5 py-1.5 text-xs bg-neutral-50 border border-neutral-200 rounded-xl outline-none"
            >
              <option value="">All Priorities</option>
              <option value="Low">Low</option>
              <option value="Medium">Medium</option>
              <option value="High">High</option>
              <option value="Critical">Critical</option>
            </select>

            <button
              type="submit"
              className="px-3.5 py-1.5 text-xs font-semibold bg-neutral-900 text-white rounded-xl hover:bg-neutral-800 transition"
            >
              Filter
            </button>
          </div>
        </form>

        <div className="text-[11px] text-neutral-400">
          Showing <span className="font-semibold text-neutral-700">{conversations.length}</span> of {total} platform records
        </div>
      </div>

      {/* Conversations Table */}
      <div className="bg-white rounded-2xl border border-neutral-200/80 shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-xs text-neutral-400">Loading platform conversations...</div>
        ) : conversations.length === 0 ? (
          <div className="p-12 text-center text-xs text-neutral-400">No conversations found matching filters.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-neutral-100 bg-neutral-50/50 text-[11px] font-semibold text-neutral-500 uppercase tracking-wider">
                  <th className="py-3 px-4">Ticket ID</th>
                  <th className="py-3 px-4">Tenant / Owner</th>
                  <th className="py-3 px-4">Customer Issue</th>
                  <th className="py-3 px-4">Category</th>
                  <th className="py-3 px-4">Priority</th>
                  <th className="py-3 px-4">Risk Level</th>
                  <th className="py-3 px-4 text-right">Inspect</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-100">
                {conversations.map((c) => (
                  <tr key={c.conversation_id} className="hover:bg-neutral-50/60 transition group">
                    <td className="py-3 px-4 font-mono text-[11px] font-medium text-neutral-500">
                      {c.conversation_id}
                    </td>

                    <td className="py-3 px-4 font-mono text-[11px] text-neutral-400">
                      <span className="px-2 py-0.5 rounded bg-neutral-100 text-neutral-700 font-sans">
                        {c.user_id ? c.user_id.slice(0, 10) + '...' : 'System Demo'}
                      </span>
                    </td>

                    <td className="py-3 px-4 font-medium text-neutral-900 max-w-xs truncate">
                      {c.customer_issue || c.raw_text_masked?.slice(0, 50) || 'Customer Ticket'}
                    </td>

                    <td className="py-3 px-4">
                      <CategoryBadge category={c.category} />
                    </td>

                    <td className="py-3 px-4">
                      <PriorityBadge priority={c.priority} />
                    </td>

                    <td className="py-3 px-4">
                      <RiskBadge risk={c.security?.risk_level || 'Low'} />
                    </td>

                    <td className="py-3 px-4 text-right">
                      <Link
                        to={`/conversations/${c.conversation_id}`}
                        className="inline-flex items-center gap-1 text-[11px] text-[#0071e3] font-medium hover:underline"
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

    </div>
  );
}
