import React, { useState, useEffect } from 'react';
import {
  Inbox,
  Filter,
  RefreshCw,
  ChevronLeft,
  ChevronRight,
  Search,
  MessageSquare,
} from 'lucide-react';
import { api } from '../api/client';
import { ConversationRecord } from '../types/analysis';
import { ConversationCard } from '../components/ConversationCard';

interface ConversationsProps {
  onNavigateToAnalyze: () => void;
}

export const Conversations: React.FC<ConversationsProps> = ({ onNavigateToAnalyze }) => {
  const [items, setItems] = useState<ConversationRecord[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [page, setPage] = useState<number>(1);
  const [pages, setPages] = useState<number>(1);
  const [riskFilter, setRiskFilter] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchConversations = async (currentPage: number, currentRisk: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getConversations(currentPage, 12, currentRisk);
      setItems(data.items);
      setTotal(data.total);
      setPages(data.pages);
      setPage(data.page);
    } catch (err: any) {
      setError(err.message || 'Failed to retrieve conversation history');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchConversations(page, riskFilter);
  }, [page, riskFilter]);

  const handleFilterChange = (filter: string) => {
    setRiskFilter(filter);
    setPage(1);
  };

  const filteredItems = items.filter((item) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    const idMatch = item.conversation_id?.toLowerCase().includes(q) || item.id?.toLowerCase().includes(q);
    const subjectMatch = item.subject?.toLowerCase().includes(q);
    const senderMatch = item.sender?.toLowerCase().includes(q);
    const messageMatch = item.message?.toLowerCase().includes(q) || item.raw_text?.toLowerCase().includes(q);
    const categoryMatch = item.category?.toLowerCase().includes(q);
    const keywordMatch = item.keywords?.some((k) => k.toLowerCase().includes(q));

    return Boolean(idMatch || subjectMatch || senderMatch || messageMatch || categoryMatch || keywordMatch);
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800/80 pb-5">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-sky-400 bg-sky-950/80 px-2 py-0.5 rounded border border-sky-800/60">
              <MessageSquare className="h-3 w-3" /> Database Records
            </span>
            <span className="text-xs text-slate-500">• {total} Loaded Conversations</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            Conversation History
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Browse and inspect customer support threads, security heuristic indicators, and AI verdicts
          </p>
        </div>

        <button
          type="button"
          onClick={() => fetchConversations(page, riskFilter)}
          className="flex items-center gap-1.5 self-start sm:self-auto rounded-lg border border-slate-700 bg-slate-800/80 px-3.5 py-2 text-xs sm:text-sm font-medium text-slate-300 hover:bg-slate-700 hover:text-white transition"
        >
          <RefreshCw className="h-4 w-4" /> Refresh History
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col md:flex-row items-center justify-between gap-3 bg-slate-900/60 p-3.5 rounded-xl border border-slate-800 shadow">
        {/* Risk Filter Buttons */}
        <div className="flex items-center gap-1.5 flex-wrap w-full md:w-auto">
          <span className="text-xs text-slate-400 font-semibold uppercase mr-1 flex items-center gap-1">
            <Filter className="h-3 w-3" /> Filter:
          </span>
          {['ALL', 'Critical', 'High', 'Medium', 'Low'].map((r) => (
            <button
              key={r}
              type="button"
              onClick={() => handleFilterChange(r)}
              className={`px-3 py-1 rounded-lg text-xs font-semibold transition ${
                riskFilter === r
                  ? 'bg-sky-600 text-white shadow-md'
                  : 'bg-slate-800 text-slate-300 hover:bg-slate-700 hover:text-white'
              }`}
            >
              {r}
            </button>
          ))}
        </div>

        {/* Search Input */}
        <div className="relative w-full md:w-72">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
          <input
            type="text"
            placeholder="Search by ID, keyword, content..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full rounded-lg border border-slate-700 bg-slate-950 pl-9 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500"
          />
        </div>
      </div>

      {/* Loading state */}
      {loading && (
        <div className="flex h-64 items-center justify-center">
          <div className="flex flex-col items-center gap-2">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-sky-500 border-t-transparent" />
            <p className="text-xs text-slate-400 font-medium">Retrieving stored records...</p>
          </div>
        </div>
      )}

      {/* Error state */}
      {error && !loading && (
        <div className="rounded-xl border border-rose-900/40 bg-rose-950/20 p-6 text-center text-rose-300 text-sm">
          {error}
        </div>
      )}

      {/* Empty state */}
      {!loading && !error && filteredItems.length === 0 && (
        <div className="rounded-xl border border-slate-800 bg-slate-900/30 p-12 text-center">
          <Inbox className="mx-auto h-12 w-12 text-slate-600 mb-3" />
          <h3 className="text-base font-bold text-slate-300">No conversations matched</h3>
          <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
            {searchQuery || riskFilter !== 'ALL'
              ? 'No messages match your selected search or risk filter criteria.'
              : 'Submit your first message on the Analyze page to see it recorded in storage.'}
          </p>
          <button
            type="button"
            onClick={onNavigateToAnalyze}
            className="mt-4 inline-flex items-center gap-2 rounded-lg bg-sky-600 px-4 py-2 text-xs font-semibold text-white hover:bg-sky-500 transition shadow"
          >
            Analyze a Message
          </button>
        </div>
      )}

      {/* Conversation Cards List */}
      {!loading && !error && filteredItems.length > 0 && (
        <div className="space-y-3">
          {filteredItems.map((conv) => (
            <ConversationCard
              key={conv.conversation_id || conv.id || Math.random().toString()}
              conversation={conv}
            />
          ))}
        </div>
      )}

      {/* Pagination Controls */}
      {!loading && total > 0 && (
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 border-t border-slate-800 pt-4 text-xs text-slate-400">
          <div>
            Showing <span className="font-semibold text-slate-200">{filteredItems.length}</span> of{' '}
            <span className="font-semibold text-slate-200">{total}</span> total stored records
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1}
              className="flex items-center gap-1 rounded-lg border border-slate-700 bg-slate-800 px-3 py-1 font-medium text-slate-300 hover:bg-slate-700 hover:text-white disabled:opacity-40 disabled:cursor-not-allowed transition"
            >
              <ChevronLeft className="h-3.5 w-3.5" /> Prev
            </button>
            <span className="font-medium text-slate-300 px-1">
              Page {page} of {pages || 1}
            </span>
            <button
              type="button"
              onClick={() => setPage((p) => Math.min(pages, p + 1))}
              disabled={page >= pages}
              className="flex items-center gap-1 rounded-lg border border-slate-700 bg-slate-800 px-3 py-1 font-medium text-slate-300 hover:bg-slate-700 hover:text-white disabled:opacity-40 disabled:cursor-not-allowed transition"
            >
              Next <ChevronRight className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
