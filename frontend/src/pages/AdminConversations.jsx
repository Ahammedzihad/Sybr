import React, { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { 
  FileText, 
  Search, 
  Filter, 
  ExternalLink, 
  RefreshCw, 
  ShieldAlert, 
  User, 
  ArrowRight,
  Flag,
  UserCheck,
  ChevronLeft,
  ChevronRight,
  AlertCircle
} from 'lucide-react';
import { fetchAdminConversations } from '../api';
import { PriorityBadge, RiskBadge, CategoryBadge, SentimentBadge } from '../components/Badges';

const CANONICAL_CATEGORIES = [
  "Billing/Payment", "Account/Login", "Product Issue", "Delivery/Shipping",
  "Refund Request", "Subscription Issue", "Technical Problem", "Service Quality",
  "Security Concern", "Other"
];

export default function AdminConversations() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [conversations, setConversations] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [search, setSearch] = useState(searchParams.get('q') || '');
  const [category, setCategory] = useState(searchParams.get('category') || '');
  const [risk, setRisk] = useState(searchParams.get('risk') || '');
  const [priority, setPriority] = useState(searchParams.get('priority') || '');
  const [status, setStatus] = useState(searchParams.get('status') || '');
  const [activeTab, setActiveTab] = useState(searchParams.get('tab') || 'all');
  const [page, setPage] = useState(1);

  const loadData = async () => {
    try {
      const params = {
        q: search,
        category,
        risk: activeTab === 'threats' ? 'Critical' : risk,
        priority: activeTab === 'high_priority' ? 'High' : priority,
        status: activeTab === 'unresolved' ? 'Unresolved' : status,
        page,
        limit: 20,
      };
      const res = await fetchAdminConversations(params);
      let items = res.items || [];
      if (activeTab === 'review') {
        items = items.filter((c) => c.needs_human_review);
      }
      setConversations(items);
      setTotal(activeTab === 'review' ? items.length : res.total || 0);
    } catch (err) {
      console.error('Failed to load admin conversations:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [category, risk, priority, status, activeTab, page]);

  const handleTabChange = (tab) => {
    setActiveTab(tab);
    setPage(1);
    if (tab === 'threats') {
      setRisk('Critical');
      setPriority('');
      setStatus('');
    } else if (tab === 'high_priority') {
      setPriority('High');
      setRisk('');
      setStatus('');
    } else if (tab === 'unresolved') {
      setStatus('Unresolved');
      setRisk('');
      setPriority('');
    } else {
      setRisk('');
      setPriority('');
      setStatus('');
    }
  };

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setPage(1);
    loadData();
  };

  const totalPages = Math.max(1, Math.ceil(total / 20));

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
            System-Wide Conversations Inbox
          </h1>
          <p className="text-xs text-neutral-500">
            Inspect customer inquiries, analyze threat interceptions, and review AI classifications across all registered workspaces.
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

      {/* Triage Tabs */}
      <div className="flex border-b border-neutral-200 gap-2 overflow-x-auto text-xs">
        <button
          onClick={() => handleTabChange('all')}
          className={`px-4 py-2 font-semibold border-b-2 transition whitespace-nowrap ${
            activeTab === 'all'
              ? 'border-neutral-900 text-neutral-900'
              : 'border-transparent text-neutral-500 hover:text-neutral-700'
          }`}
        >
          All Conversations
        </button>
        <button
          onClick={() => handleTabChange('review')}
          className={`px-4 py-2 font-semibold border-b-2 transition whitespace-nowrap flex items-center gap-1.5 ${
            activeTab === 'review'
              ? 'border-indigo-600 text-indigo-600'
              : 'border-transparent text-neutral-500 hover:text-neutral-700'
          }`}
        >
          <Flag className="w-3.5 h-3.5" />
          <span>Review Queue</span>
        </button>
        <button
          onClick={() => handleTabChange('threats')}
          className={`px-4 py-2 font-semibold border-b-2 transition whitespace-nowrap flex items-center gap-1.5 ${
            activeTab === 'threats'
              ? 'border-rose-600 text-rose-600'
              : 'border-transparent text-neutral-500 hover:text-neutral-700'
          }`}
        >
          <ShieldAlert className="w-3.5 h-3.5" />
          <span>Critical Threats</span>
        </button>
        <button
          onClick={() => handleTabChange('high_priority')}
          className={`px-4 py-2 font-semibold border-b-2 transition whitespace-nowrap flex items-center gap-1.5 ${
            activeTab === 'high_priority'
              ? 'border-amber-600 text-amber-600'
              : 'border-transparent text-neutral-500 hover:text-neutral-700'
          }`}
        >
          <AlertCircle className="w-3.5 h-3.5" />
          <span>High Priority</span>
        </button>
        <button
          onClick={() => handleTabChange('unresolved')}
          className={`px-4 py-2 font-semibold border-b-2 transition whitespace-nowrap ${
            activeTab === 'unresolved'
              ? 'border-neutral-900 text-neutral-900'
              : 'border-transparent text-neutral-500 hover:text-neutral-700'
          }`}
        >
          Unresolved
        </button>
      </div>

      {/* Filter & Search Bar */}
      <div className="bg-white p-4 rounded-2xl border border-neutral-200/80 shadow-xs space-y-3">
        <form onSubmit={handleSearchSubmit} className="flex flex-col md:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-neutral-400 pointer-events-none" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search across all platform conversations by text, customer issue, or ID..."
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
              {CANONICAL_CATEGORIES.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
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
                  <th className="py-3 px-4">Customer</th>
                  <th className="py-3 px-4">Customer Issue</th>
                  <th className="py-3 px-4">Category</th>
                  <th className="py-3 px-4">Priority</th>
                  <th className="py-3 px-4">Threat Risk</th>
                  <th className="py-3 px-4">Review Status</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Inspect</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-100">
                {conversations.map((c) => (
                  <tr key={c.conversation_id} className="hover:bg-neutral-50/60 transition group">
                    <td className="py-3 px-4 font-mono text-[11px] font-medium text-neutral-500">
                      <div>{c.conversation_id}</div>
                      <span className="text-[10px] text-neutral-400 uppercase font-sans">[{c.channel || 'ticket'}]</span>
                    </td>

                    <td className="py-3 px-4 font-mono text-[11px] text-neutral-500">
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

                    <td className="py-3 px-4 text-[11px]">
                      {c.is_human_reviewed ? (
                        <span className="inline-flex items-center gap-1 font-semibold text-amber-700">
                          <UserCheck className="w-3 h-3" />
                          <span>Audited</span>
                        </span>
                      ) : c.needs_human_review ? (
                        <span className="inline-flex items-center gap-1 font-semibold text-rose-600">
                          <Flag className="w-3 h-3" />
                          <span>Flagged</span>
                        </span>
                      ) : (
                        <span className="text-neutral-400 font-mono">AI Classified</span>
                      )}
                    </td>

                    <td className="py-3 px-4 font-mono text-[11px] text-neutral-600">
                      {c.resolution_status}
                    </td>

                    <td className="py-3 px-4 text-right">
                      <Link
                        to={`/conversations/${c.conversation_id}`}
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

        {/* Pagination Footer */}
        {totalPages > 1 && (
          <div className="p-4 border-t border-neutral-100 flex items-center justify-between text-xs text-neutral-500">
            <span>Page {page} of {totalPages}</span>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1}
                className="p-1.5 rounded-lg border border-neutral-200 hover:bg-neutral-50 disabled:opacity-40 transition"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page >= totalPages}
                className="p-1.5 rounded-lg border border-neutral-200 hover:bg-neutral-50 disabled:opacity-40 transition"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>

    </div>
  );
}
