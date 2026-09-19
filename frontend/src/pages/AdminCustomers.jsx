import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  Users, 
  User, 
  Search, 
  RefreshCw, 
  MessageSquareText, 
  AlertTriangle, 
  ShieldAlert, 
  Clock, 
  ArrowRight, 
  ExternalLink,
  X,
  Calendar,
  CheckCircle2,
  ChevronRight
} from 'lucide-react';
import { fetchAdminCustomers, fetchAdminCustomerHistory } from '../api';

export default function AdminCustomers() {
  const [customers, setCustomers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [search, setSearch] = useState('');
  
  // Slide-over drawer state for selected customer
  const [selectedCustomer, setSelectedCustomer] = useState(null);
  const [customerHistory, setCustomerHistory] = useState(null);
  const [loadingHistory, setLoadingHistory] = useState(false);

  const loadCustomers = async () => {
    try {
      const res = await fetchAdminCustomers();
      setCustomers(res || []);
    } catch (err) {
      console.error('Failed to load customers:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadCustomers();
  }, []);

  const openCustomerDossier = async (customer) => {
    setSelectedCustomer(customer);
    setLoadingHistory(true);
    try {
      const history = await fetchAdminCustomerHistory(customer.customer_id);
      setCustomerHistory(history);
    } catch (err) {
      console.error('Failed to load customer history:', err);
    } finally {
      setLoadingHistory(false);
    }
  };

  const closeDossier = () => {
    setSelectedCustomer(null);
    setCustomerHistory(null);
  };

  const filteredCustomers = customers.filter((c) => {
    const term = search.toLowerCase();
    return (
      (c.display_name && c.display_name.toLowerCase().includes(term)) ||
      (c.email && c.email.toLowerCase().includes(term)) ||
      (c.customer_id && c.customer_id.toLowerCase().includes(term))
    );
  });

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6 animate-fade-in text-left">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-neutral-200/80 pb-5">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-semibold tracking-wide uppercase bg-emerald-50 text-emerald-700 border border-emerald-200">
              Customer Accounts
            </span>
            <span className="text-xs text-neutral-400">Section 8 & 14 Multi-Tenant Directory</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-neutral-900">
            Customer Directory & Account Oversight
          </h1>
          <p className="text-xs text-neutral-500">
            Inspect individual customer tenant accounts, conversation volumes, unresolved issues, and security encounters.
          </p>
        </div>

        <button
          onClick={() => { setRefreshing(true); loadCustomers(); }}
          disabled={refreshing}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-neutral-700 bg-white border border-neutral-200 rounded-lg hover:bg-neutral-50 hover:text-neutral-900 transition shadow-xs disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin' : ''}`} />
          {refreshing ? 'Refreshing...' : 'Refresh Directory'}
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex items-center justify-between gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 text-neutral-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search by customer name, email, or account ID..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2 text-xs bg-white border border-neutral-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-neutral-900/10 focus:border-neutral-900 transition"
          />
        </div>

        <span className="text-xs text-neutral-500 font-mono">
          Showing {filteredCustomers.length} of {customers.length} Accounts
        </span>
      </div>

      {loading ? (
        <div className="py-20 flex flex-col items-center justify-center space-y-3">
          <div className="w-8 h-8 border-2 border-neutral-900 border-t-transparent rounded-full animate-spin" />
          <p className="text-xs text-neutral-500 font-mono">Loading tenant directories...</p>
        </div>
      ) : (
        /* Customer Table */
        <div className="bg-white rounded-xl border border-neutral-200/80 shadow-xs overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-neutral-50/75 border-b border-neutral-200/80 text-neutral-500 uppercase tracking-wider font-semibold text-[11px]">
                  <th className="py-3 px-4">Customer Account</th>
                  <th className="py-3 px-4">Total Conversations</th>
                  <th className="py-3 px-4">Unresolved Tickets</th>
                  <th className="py-3 px-4">Threat Encounters</th>
                  <th className="py-3 px-4">Last Activity</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-100">
                {filteredCustomers.map((customer) => (
                  <tr key={customer.customer_id} className="hover:bg-neutral-50/70 transition">
                    {/* Account */}
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-2.5">
                        <div className="w-8 h-8 rounded-full bg-neutral-100 border border-neutral-200 flex items-center justify-center text-neutral-700 font-bold shrink-0 text-xs">
                          {customer.display_name ? customer.display_name[0].toUpperCase() : 'U'}
                        </div>
                        <div className="min-w-0">
                          <p className="font-semibold text-neutral-900 truncate">
                            {customer.display_name || 'Anonymous Customer'}
                          </p>
                          <p className="text-[11px] text-neutral-400 font-mono truncate">
                            {customer.email}
                          </p>
                        </div>
                      </div>
                    </td>

                    {/* Total Conversations */}
                    <td className="py-3 px-4">
                      <span className="font-mono font-medium text-neutral-800">
                        {customer.conversation_count}
                      </span>
                    </td>

                    {/* Unresolved */}
                    <td className="py-3 px-4">
                      {customer.unresolved_count > 0 ? (
                        <span className="inline-flex items-center gap-1 font-semibold text-amber-600">
                          <AlertTriangle className="w-3 h-3" />
                          {customer.unresolved_count} open
                        </span>
                      ) : (
                        <span className="text-emerald-600 inline-flex items-center gap-1">
                          <CheckCircle2 className="w-3 h-3" />
                          All clear
                        </span>
                      )}
                    </td>

                    {/* Threat Encounters */}
                    <td className="py-3 px-4">
                      {customer.critical_count > 0 ? (
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-50 text-rose-700 border border-rose-200 inline-flex items-center gap-1">
                          <ShieldAlert className="w-3 h-3" />
                          {customer.critical_count} threats
                        </span>
                      ) : (
                        <span className="text-neutral-400 text-[11px]">0 detected</span>
                      )}
                    </td>

                    {/* Last Activity */}
                    <td className="py-3 px-4 text-neutral-500 font-mono text-[11px]">
                      {customer.last_activity ? new Date(customer.last_activity).toLocaleDateString() : 'N/A'}
                    </td>

                    {/* Action */}
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={() => openCustomerDossier(customer)}
                        className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-semibold text-neutral-900 bg-neutral-100 hover:bg-neutral-200 rounded-lg transition"
                      >
                        Inspect Dossier
                        <ChevronRight className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))}

                {filteredCustomers.length === 0 && (
                  <tr>
                    <td colSpan="6" className="py-12 text-center text-xs text-neutral-500">
                      No customer accounts matching query.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Customer Dossier Slide-Over Drawer */}
      {selectedCustomer && (
        <div className="fixed inset-0 z-50 overflow-hidden bg-neutral-900/40 backdrop-blur-xs flex justify-end animate-fade-in">
          <div className="w-full max-w-2xl bg-white h-full shadow-2xl flex flex-col transform transition-transform">
            
            {/* Drawer Header */}
            <div className="p-5 border-b border-neutral-200 flex items-center justify-between bg-neutral-50">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-neutral-900 text-white font-bold flex items-center justify-center text-sm">
                  {selectedCustomer.display_name ? selectedCustomer.display_name[0].toUpperCase() : 'U'}
                </div>
                <div>
                  <h2 className="text-base font-bold text-neutral-900">
                    {selectedCustomer.display_name}
                  </h2>
                  <p className="text-xs text-neutral-500 font-mono">
                    {selectedCustomer.email} • ID: {selectedCustomer.customer_id}
                  </p>
                </div>
              </div>

              <button
                onClick={closeDossier}
                className="p-1.5 rounded-lg text-neutral-400 hover:text-neutral-900 hover:bg-neutral-200/60 transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Drawer Body */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6 text-xs">
              
              {/* Metric Summary Cards */}
              <div className="grid grid-cols-3 gap-3">
                <div className="p-3 bg-neutral-50 rounded-lg border border-neutral-200">
                  <span className="text-[10px] text-neutral-500 uppercase tracking-wider block">Total Ingested</span>
                  <span className="text-lg font-bold text-neutral-900 font-mono">
                    {customerHistory?.total_conversations || selectedCustomer.conversation_count}
                  </span>
                </div>
                <div className="p-3 bg-neutral-50 rounded-lg border border-neutral-200">
                  <span className="text-[10px] text-neutral-500 uppercase tracking-wider block">Unresolved</span>
                  <span className={`text-lg font-bold font-mono ${selectedCustomer.unresolved_count > 0 ? 'text-amber-600' : 'text-neutral-900'}`}>
                    {selectedCustomer.unresolved_count}
                  </span>
                </div>
                <div className="p-3 bg-neutral-50 rounded-lg border border-neutral-200">
                  <span className="text-[10px] text-neutral-500 uppercase tracking-wider block">Critical Threats</span>
                  <span className={`text-lg font-bold font-mono ${selectedCustomer.critical_count > 0 ? 'text-rose-600' : 'text-neutral-900'}`}>
                    {selectedCustomer.critical_count}
                  </span>
                </div>
              </div>

              {/* Conversation History List */}
              <div className="space-y-3">
                <div className="flex items-center justify-between border-b border-neutral-200 pb-2">
                  <h3 className="font-bold text-neutral-900 flex items-center gap-1.5">
                    <MessageSquareText className="w-4 h-4 text-neutral-500" />
                    Conversation History & Ticket Archive
                  </h3>
                  <span className="text-[11px] text-neutral-400 font-mono">
                    {customerHistory?.conversations?.length || 0} Tickets
                  </span>
                </div>

                {loadingHistory ? (
                  <div className="py-12 text-center text-neutral-400 font-mono">
                    Fetching tenant ticket archive...
                  </div>
                ) : (
                  <div className="divide-y divide-neutral-100 border border-neutral-200 rounded-lg overflow-hidden bg-white">
                    {(customerHistory?.conversations || []).map((conv) => (
                      <div key={conv.conversation_id} className="p-3.5 hover:bg-neutral-50/80 transition flex items-center justify-between gap-3">
                        <div className="space-y-1 min-w-0 flex-1">
                          <div className="flex items-center gap-2">
                            <span className="font-mono font-semibold text-neutral-900">
                              {conv.conversation_id}
                            </span>
                            <span className="px-1.5 py-0.5 rounded text-[9px] font-semibold bg-neutral-100 text-neutral-700">
                              {conv.category}
                            </span>
                            {conv.security?.threat_detected && (
                              <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-rose-50 text-rose-700 border border-rose-200">
                                {conv.security.threat_type}
                              </span>
                            )}
                          </div>
                          <p className="text-neutral-600 truncate text-[11px]">
                            {conv.customer_issue || conv.raw_text_masked || 'No issue description recorded'}
                          </p>
                          <div className="flex items-center gap-3 text-[10px] text-neutral-400">
                            <span>Status: {conv.resolution_status}</span>
                            <span>• Priority: {conv.priority}</span>
                            <span>• {new Date(conv.created_at).toLocaleDateString()}</span>
                          </div>
                        </div>

                        <Link
                          to={`/conversations/${conv.conversation_id}`}
                          className="p-1.5 rounded-lg bg-neutral-100 hover:bg-neutral-900 hover:text-white transition shrink-0"
                          title="Open Ticket"
                        >
                          <ArrowRight className="w-3.5 h-3.5" />
                        </Link>
                      </div>
                    ))}

                    {(!customerHistory?.conversations || customerHistory.conversations.length === 0) && (
                      <div className="p-8 text-center text-neutral-400 text-xs">
                        No conversations found for this customer account.
                      </div>
                    )}
                  </div>
                )}
              </div>

            </div>

            {/* Drawer Footer */}
            <div className="p-4 border-t border-neutral-200 bg-neutral-50 flex items-center justify-between">
              <Link
                to={`/admin/conversations?q=${encodeURIComponent(selectedCustomer.email)}`}
                className="text-xs font-semibold text-neutral-900 hover:underline inline-flex items-center gap-1"
              >
                Inspect All in Conversation Inbox
                <ExternalLink className="w-3.5 h-3.5" />
              </Link>
              <button
                onClick={closeDossier}
                className="px-4 py-2 text-xs font-semibold bg-neutral-900 text-white rounded-lg hover:bg-neutral-800 transition"
              >
                Close
              </button>
            </div>

          </div>
        </div>
      )}
    </div>
  );
}
