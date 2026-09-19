import React, { useState, useEffect } from 'react';
import { 
  Users, 
  ShieldCheck, 
  ShieldAlert, 
  RefreshCw, 
  AlertCircle, 
  CheckCircle2, 
  Search,
  ArrowUpDown,
  UserCheck,
  UserX
} from 'lucide-react';
import { fetchAdminUsers, updateUserRole, getCurrentUser } from '../api';
import Button from '../components/ui/Button';

export default function AdminUsers() {
  const currentAdmin = getCurrentUser();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [search, setSearch] = useState('');
  const [actionLoading, setActionLoading] = useState(null);
  const [message, setMessage] = useState({ type: '', text: '' });

  const loadUsers = async () => {
    try {
      const res = await fetchAdminUsers();
      setUsers(res);
    } catch (err) {
      setMessage({ type: 'error', text: err.message || 'Failed to load user accounts.' });
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadUsers();
  }, []);

  const handleRoleChange = async (targetUser, newRole) => {
    setMessage({ type: '', text: '' });
    
    // Confirmation prompt
    const actionText = newRole === 'admin' ? 'promote this user to Administrator' : 'demote this user to Customer';
    if (!window.confirm(`Are you sure you want to ${actionText}?`)) {
      return;
    }

    setActionLoading(targetUser.id);
    try {
      await updateUserRole(targetUser.id, newRole);
      setMessage({
        type: 'success',
        text: `Successfully updated ${targetUser.email || targetUser.display_name} to ${newRole.toUpperCase()}.`,
      });
      await loadUsers();
    } catch (err) {
      setMessage({
        type: 'error',
        text: err.message || 'Failed to update user role.',
      });
    } finally {
      setActionLoading(null);
    }
  };

  const filteredUsers = users.filter((u) => {
    const q = search.toLowerCase();
    return (
      (u.display_name || '').toLowerCase().includes(q) ||
      (u.email || '').toLowerCase().includes(q) ||
      (u.id || '').toLowerCase().includes(q) ||
      (u.role || '').toLowerCase().includes(q)
    );
  });

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6 animate-fade-in text-left">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-neutral-200/80 pb-5">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-semibold tracking-wide uppercase bg-violet-50 text-violet-700 border border-violet-200">
              User & Role Governance
            </span>
            <span className="text-xs text-neutral-400">Section 12 & 23</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-neutral-900">
            User Account Management
          </h1>
          <p className="text-xs text-neutral-500">
            View provisioned accounts, enforce tenant isolation, and assign administrative responsibilities.
          </p>
        </div>

        <button
          onClick={() => { setRefreshing(true); loadUsers(); }}
          disabled={refreshing}
          className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl border border-neutral-200 text-neutral-700 hover:bg-neutral-50 text-xs font-semibold transition active:scale-95"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin' : ''}`} />
          <span>Refresh Users</span>
        </button>
      </div>

      {/* Status Banners */}
      {message.text && (
        <div className={`p-3.5 rounded-xl text-xs flex items-center gap-2.5 ${
          message.type === 'error'
            ? 'bg-rose-50 border border-rose-200 text-rose-700'
            : 'bg-emerald-50 border border-emerald-200 text-emerald-700'
        }`}>
          {message.type === 'error' ? (
            <AlertCircle className="w-4 h-4 shrink-0 text-rose-500" />
          ) : (
            <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-500" />
          )}
          <span className="font-medium">{message.text}</span>
        </div>
      )}

      {/* Filter and Search Bar */}
      <div className="flex items-center justify-between gap-4 bg-white p-4 rounded-2xl border border-neutral-200/80 shadow-sm">
        <div className="relative flex-1 max-w-sm">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-neutral-400 pointer-events-none" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by name, email, role, or ID..."
            className="w-full pl-9 pr-3 py-1.5 text-xs bg-neutral-50 border border-neutral-200 rounded-xl focus:bg-white focus:border-neutral-900 outline-none transition"
          />
        </div>

        <div className="text-xs text-neutral-500">
          Showing <span className="font-semibold text-neutral-800">{filteredUsers.length}</span> of {users.length} accounts
        </div>
      </div>

      {/* Users Table */}
      <div className="bg-white rounded-2xl border border-neutral-200/80 shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-xs text-neutral-400">Loading user profiles...</div>
        ) : filteredUsers.length === 0 ? (
          <div className="p-12 text-center text-xs text-neutral-400">No accounts match your query.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-neutral-100 bg-neutral-50/50 text-[11px] font-semibold text-neutral-500 uppercase tracking-wider">
                  <th className="py-3 px-4">User</th>
                  <th className="py-3 px-4">Email</th>
                  <th className="py-3 px-4">Role</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">User ID</th>
                  <th className="py-3 px-4 text-right">Role Governance</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-100">
                {filteredUsers.map((u) => {
                  const isCurrent = u.id === currentAdmin?.id;
                  const isAdminRole = u.role === 'admin';
                  const isBusy = actionLoading === u.id;

                  return (
                    <tr key={u.id} className="hover:bg-neutral-50/60 transition">
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-2.5">
                          <div className="w-7 h-7 rounded-lg bg-neutral-900 text-white text-[11px] font-bold flex items-center justify-center">
                            {(u.display_name || u.email || 'U')[0].toUpperCase()}
                          </div>
                          <div>
                            <div className="font-semibold text-neutral-900">
                              {u.display_name || u.email?.split('@')[0] || 'User'}
                              {isCurrent && (
                                <span className="ml-1.5 text-[10px] text-neutral-400 font-normal">(You)</span>
                              )}
                            </div>
                          </div>
                        </div>
                      </td>

                      <td className="py-3 px-4 text-neutral-600 font-medium">
                        {u.email}
                      </td>

                      <td className="py-3 px-4">
                        {isAdminRole ? (
                          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-violet-50 text-violet-700 border border-violet-200">
                            <ShieldAlert className="w-3 h-3 text-violet-600" />
                            <span>Administrator</span>
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                            <ShieldCheck className="w-3 h-3 text-emerald-600" />
                            <span>Customer</span>
                          </span>
                        )}
                      </td>

                      <td className="py-3 px-4">
                        <span className="inline-flex items-center gap-1 text-emerald-700 font-medium text-[11px]">
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                          <span className="capitalize">{u.status || 'Active'}</span>
                        </span>
                      </td>

                      <td className="py-3 px-4 font-mono text-[11px] text-neutral-400 select-all">
                        {u.id}
                      </td>

                      <td className="py-3 px-4 text-right">
                        {isAdminRole ? (
                          <button
                            type="button"
                            disabled={isBusy}
                            onClick={() => handleRoleChange(u, 'customer')}
                            className="inline-flex items-center gap-1 px-2.5 py-1 text-[11px] font-medium text-amber-700 bg-amber-50 hover:bg-amber-100/80 border border-amber-200 rounded-lg transition active:scale-95 disabled:opacity-50"
                            title="Demote to Customer role"
                          >
                            <UserX className="w-3 h-3" />
                            <span>{isBusy ? 'Saving...' : 'Demote to Customer'}</span>
                          </button>
                        ) : (
                          <button
                            type="button"
                            disabled={isBusy}
                            onClick={() => handleRoleChange(u, 'admin')}
                            className="inline-flex items-center gap-1 px-2.5 py-1 text-[11px] font-medium text-violet-700 bg-violet-50 hover:bg-violet-100/80 border border-violet-200 rounded-lg transition active:scale-95 disabled:opacity-50"
                            title="Promote to Administrator role"
                          >
                            <UserCheck className="w-3 h-3" />
                            <span>{isBusy ? 'Saving...' : 'Promote to Admin'}</span>
                          </button>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

    </div>
  );
}
