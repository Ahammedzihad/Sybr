import React, { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { 
  Search, 
  Filter, 
  ArrowRight, 
  RefreshCw, 
  RotateCcw,
  MessageSquareText,
  ShieldAlert,
  ChevronLeft,
  ChevronRight
} from 'lucide-react';
import { fetchConversations } from '../api';
import { PriorityBadge, RiskBadge, EmotionBadge, ResolutionBadge } from '../components/Badges';
import Input from '../components/ui/Input';
import Select from '../components/ui/Select';
import Button from '../components/ui/Button';
import EmptyState from '../components/ui/EmptyState';
import { TableRowSkeleton } from '../components/ui/Skeleton';

const CATEGORIES = [
  "Billing/Payment", "Account/Login", "Product Issue", "Delivery/Shipping",
  "Refund Request", "Subscription Issue", "Technical Problem", "Service Quality",
  "Security Concern", "Other"
];

export default function Conversations() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [conversations, setConversations] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters initialized from URL query params (supports Sidebar Quick Tags)
  const [search, setSearch] = useState(searchParams.get('q') || '');
  const [category, setCategory] = useState(searchParams.get('category') || '');
  const [priority, setPriority] = useState(searchParams.get('priority') || '');
  const [risk, setRisk] = useState(searchParams.get('risk') || '');
  const [sentiment, setSentiment] = useState(searchParams.get('sentiment') || '');
  const [status, setStatus] = useState(searchParams.get('status') || '');

  // Synchronize state if URL query params change (e.g. from sidebar tag click)
  useEffect(() => {
    const qParam = searchParams.get('q') || '';
    const catParam = searchParams.get('category') || '';
    const prioParam = searchParams.get('priority') || '';
    const riskParam = searchParams.get('risk') || '';
    const sentParam = searchParams.get('sentiment') || '';
    const statusParam = searchParams.get('status') || '';

    setSearch(qParam);
    setCategory(catParam);
    setPriority(prioParam);
    setRisk(riskParam);
    setSentiment(sentParam);
    setStatus(statusParam);
    setPage(1);
  }, [searchParams]);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchConversations({
        q: search,
        category,
        priority,
        risk,
        sentiment,
        status,
        page,
        limit: 15,
      });
      setConversations(res.items || []);
      setTotal(res.total || 0);
    } catch (err) {
      setError(err.message || 'Failed to load conversations');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const handleModeChange = () => loadData();
    window.addEventListener('offline-mode-changed', handleModeChange);
    return () => window.removeEventListener('offline-mode-changed', handleModeChange);
  }, [page, category, priority, risk, sentiment, status]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setPage(1);
    loadData();
  };

  const resetFilters = () => {
    setSearch('');
    setCategory('');
    setPriority('');
    setRisk('');
    setSentiment('');
    setStatus('');
    setPage(1);
    setSearchParams({});
  };

  const totalPages = Math.ceil(total / 15) || 1;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6 animate-fade-in">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-neutral-200/80 pb-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-neutral-900 tracking-tight flex items-center gap-2.5 font-sans">
            <MessageSquareText className="w-5 h-5 text-neutral-900" />
            Conversations
          </h1>
          <p className="text-neutral-500 text-xs sm:text-sm mt-0.5">
            Filter, inspect, and audit customer interactions with automated risk triage
          </p>
        </div>
        <div className="flex items-center gap-2 self-start sm:self-auto">
          <Button
            variant="secondary"
            size="sm"
            onClick={loadData}
            icon={RefreshCw}
          >
            Refresh
          </Button>
        </div>
      </div>

      {/* Stripe-Style Unified Search & Filter Card */}
      <div className="p-3.5 rounded-xl bg-white border border-neutral-200/80 shadow-xs space-y-3">
        <form onSubmit={handleSearchSubmit} className="flex flex-col sm:flex-row gap-2">
          <div className="flex-1">
            <Input
              placeholder="Search by ticket ID, customer issue text, or indicators..."
              icon={Search}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              onClear={() => { setSearch(''); setPage(1); }}
            />
          </div>
          <Button type="submit" variant="primary" size="sm">
            Search
          </Button>
          {(search || category || priority || risk || sentiment || status) && (
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={resetFilters}
              icon={RotateCcw}
              title="Reset all filters"
            >
              Reset
            </Button>
          )}
        </form>

        {/* Filter Dropdowns Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 pt-2 border-t border-neutral-100">
          <Select
            value={category}
            onChange={(e) => { setCategory(e.target.value); setPage(1); }}
          >
            <option value="">All Categories</option>
            {CATEGORIES.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </Select>

          <Select
            value={risk}
            onChange={(e) => { setRisk(e.target.value); setPage(1); }}
          >
            <option value="">All Risk Levels</option>
            <option value="Critical">Critical Risk</option>
            <option value="High">High Risk</option>
            <option value="Medium">Medium Risk</option>
            <option value="Low">Low Risk</option>
          </Select>

          <Select
            value={priority}
            onChange={(e) => { setPriority(e.target.value); setPage(1); }}
          >
            <option value="">All Priorities</option>
            <option value="Critical">Critical</option>
            <option value="High">High</option>
            <option value="Medium">Medium</option>
            <option value="Low">Low</option>
          </Select>

          <Select
            value={sentiment}
            onChange={(e) => { setSentiment(e.target.value); setPage(1); }}
          >
            <option value="">All Sentiments</option>
            <option value="Positive">Positive</option>
            <option value="Neutral">Neutral</option>
            <option value="Negative">Negative</option>
          </Select>

          <Select
            value={status}
            onChange={(e) => { setStatus(e.target.value); setPage(1); }}
            containerClassName="col-span-2 sm:col-span-1"
          >
            <option value="">All Statuses</option>
            <option value="Unresolved">Unresolved</option>
            <option value="Resolved">Resolved</option>
            <option value="Pending">Pending</option>
          </Select>
        </div>
      </div>

      {/* Stripe-Grade Desktop Table View */}
      <div className="hidden md:block rounded-xl bg-white border border-neutral-200/80 shadow-xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-neutral-50/75 border-b border-neutral-200/80 text-neutral-500 font-medium text-[11px] uppercase tracking-wider">
              <tr>
                <th className="py-2.5 px-4 font-semibold">Ticket ID</th>
                <th className="py-2.5 px-3 font-semibold">Channel</th>
                <th className="py-2.5 px-4 min-w-[240px] font-semibold">Customer Issue & Excerpt</th>
                <th className="py-2.5 px-3 font-semibold">Emotion</th>
                <th className="py-2.5 px-3 font-semibold">Priority</th>
                <th className="py-2.5 px-3 font-semibold">Threat Risk</th>
                <th className="py-2.5 px-3 font-semibold">Status</th>
                <th className="py-2.5 px-3 text-right font-semibold">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-100">
              {loading ? (
                Array.from({ length: 6 }).map((_, i) => (
                  <TableRowSkeleton key={i} cols={8} />
                ))
              ) : conversations.length > 0 ? (
                conversations.map((c) => (
                  <tr 
                    key={c.conversation_id}
                    className="hover:bg-neutral-50/80 transition-colors group cursor-pointer"
                  >
                    <td className="py-3 px-4 font-mono font-medium text-neutral-900">
                      <Link 
                        to={`/conversations/${c.conversation_id}`}
                        className="text-neutral-900 font-semibold hover:text-indigo-600 flex items-center gap-1.5 focus-visible:outline-none rounded"
                      >
                        {c.conversation_id}
                        {c.security?.threat_detected && (
                          <span className="w-1.5 h-1.5 rounded-full bg-rose-500 shadow-xs" title="Threat Flagged"></span>
                        )}
                      </Link>
                    </td>
                    <td className="py-3 px-3">
                      <span className="px-2 py-0.5 rounded bg-neutral-100 text-[10px] font-mono text-neutral-600 font-medium uppercase border border-neutral-200/60">
                        {c.channel || 'ticket'}
                      </span>
                    </td>
                    <td className="py-3 px-4 max-w-xs sm:max-w-md">
                      <div className="font-medium text-neutral-900 truncate">
                        {c.customer_issue || c.category}
                      </div>
                      <div className="text-[11px] text-neutral-500 truncate mt-0.5">
                        {c.raw_text_masked || (c.messages && c.messages[0]?.text) || 'No message preview'}
                      </div>
                    </td>
                    <td className="py-3 px-3">
                      <EmotionBadge emotion={c.emotion} intensity={c.emotion_intensity} />
                    </td>
                    <td className="py-3 px-3">
                      <PriorityBadge level={c.priority} />
                    </td>
                    <td className="py-3 px-3">
                      <RiskBadge level={c.security?.risk_level || 'Low'} />
                    </td>
                    <td className="py-3 px-3">
                      <ResolutionBadge status={c.resolution_status} />
                    </td>
                    <td className="py-3 px-3 text-right">
                      <Link
                        to={`/conversations/${c.conversation_id}`}
                        aria-label={`Inspect ticket ${c.conversation_id}`}
                        className="inline-flex items-center gap-1 text-neutral-400 group-hover:text-neutral-900 font-medium transition-colors"
                      >
                        <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
                      </Link>
                    </td>
                  </tr>
                ))
              ) : null}
            </tbody>
          </table>
        </div>

        {!loading && conversations.length === 0 && (
          <EmptyState
            title="No matching conversations"
            description="No conversations found matching your search and filter criteria."
            actionLabel="Clear Filters"
            onAction={resetFilters}
          />
        )}
      </div>

      {/* iPadOS Mobile Card List View (Screen < 768px) */}
      <div className="md:hidden space-y-3">
        {loading ? (
          Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="p-4 rounded-2xl bg-white border border-black/[0.08] space-y-2 animate-pulse">
              <div className="h-4 bg-black/[0.06] rounded w-24" />
              <div className="h-4 bg-black/[0.06] rounded w-3/4" />
            </div>
          ))
        ) : conversations.length > 0 ? (
          conversations.map((c) => (
            <Link
              key={c.conversation_id}
              to={`/conversations/${c.conversation_id}`}
              className="block p-4 rounded-2xl bg-white border border-black/[0.08] hover:border-black/[0.14] shadow-sm hover:shadow-md transition-all space-y-3 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#007aff]"
            >
              <div className="flex items-center justify-between">
                <span className="font-mono text-xs font-semibold text-[#007aff] flex items-center gap-1.5">
                  {c.conversation_id}
                  {c.security?.threat_detected && (
                    <span className="w-2 h-2 rounded-full bg-[#ff3b30]" title="Threat Flagged"></span>
                  )}
                </span>
                <span className="px-2 py-0.5 rounded-md bg-black/[0.04] text-[10px] font-mono text-[#59595e] font-semibold uppercase">
                  {c.channel || 'ticket'}
                </span>
              </div>
              <div>
                <h4 className="text-xs font-semibold text-[#1d1d1f] line-clamp-1">
                  {c.customer_issue || c.category}
                </h4>
                <p className="text-[11px] text-[#59595e] line-clamp-2 mt-0.5">
                  {c.raw_text_masked || (c.messages && c.messages[0]?.text)}
                </p>
              </div>
              <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-black/[0.04]">
                <RiskBadge level={c.security?.risk_level || 'Low'} />
                <PriorityBadge level={c.priority} />
                <ResolutionBadge status={c.resolution_status} />
              </div>
            </Link>
          ))
        ) : (
          <EmptyState
            title="No matching conversations"
            description="No conversations found matching your search and filter criteria."
            actionLabel="Clear Filters"
            onAction={resetFilters}
          />
        )}
      </div>

      {/* Pagination Footer */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-[#59595e] pt-2">
        <div className="font-mono">
          Showing <span className="text-[#1d1d1f] font-semibold">{conversations.length}</span> of <span className="text-[#1d1d1f] font-semibold">{total}</span> records
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="secondary"
            size="sm"
            disabled={page <= 1}
            onClick={() => setPage(page - 1)}
            icon={ChevronLeft}
          >
            Prev
          </Button>
          <span className="px-3 py-1 font-mono text-[#1d1d1f] font-medium">
            {page} / {totalPages}
          </span>
          <Button
            variant="secondary"
            size="sm"
            disabled={page >= totalPages}
            onClick={() => setPage(page + 1)}
            icon={ChevronRight}
          >
            Next
          </Button>
        </div>
      </div>

    </div>
  );
}
