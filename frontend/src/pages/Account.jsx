import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  User, 
  Mail, 
  Shield, 
  Lock, 
  LogOut, 
  Key, 
  CheckCircle2, 
  AlertCircle,
  Clock,
  Laptop
} from 'lucide-react';
import { getCurrentUser, logout, updatePassword, getUserRole, isAdmin } from '../api';
import Button from '../components/ui/Button';

export default function Account() {
  const navigate = useNavigate();
  const user = getCurrentUser();
  const role = getUserRole();
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState({ type: '', text: '' });

  const handleLogout = async () => {
    await logout();
    navigate('/login', { replace: true });
  };

  const handleUpdatePassword = async (e) => {
    e.preventDefault();
    setMsg({ type: '', text: '' });

    if (newPassword.length < 6) {
      setMsg({ type: 'error', text: 'Password must be at least 6 characters long.' });
      return;
    }
    if (newPassword !== confirmPassword) {
      setMsg({ type: 'error', text: 'Passwords do not match.' });
      return;
    }

    setLoading(true);
    try {
      await updatePassword(newPassword);
      setMsg({ type: 'success', text: 'Password has been updated successfully.' });
      setNewPassword('');
      setConfirmPassword('');
    } catch (err) {
      setMsg({ type: 'error', text: err.message || 'Failed to update password.' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-8 space-y-8 animate-fade-in text-left">
      
      {/* Header */}
      <div className="border-b border-neutral-200/80 pb-5 space-y-1">
        <h1 className="text-2xl font-bold tracking-tight text-neutral-900">
          Account & Profile Settings
        </h1>
        <p className="text-xs text-neutral-500">
          Manage your Sybr credentials, tenant identity, and active session permissions.
        </p>
      </div>

      {/* Profile Overview Card */}
      <div className="bg-white rounded-2xl border border-neutral-200/80 shadow-sm p-6 space-y-6">
        <div className="flex items-center justify-between border-b border-neutral-100 pb-4">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-2xl bg-neutral-900 text-white flex items-center justify-center font-bold text-lg">
              {(user?.display_name || user?.email || 'U')[0].toUpperCase()}
            </div>
            <div>
              <h2 className="text-sm font-bold text-neutral-900">
                {user?.display_name || user?.email?.split('@')[0] || 'Authenticated User'}
              </h2>
              <span className="text-xs text-neutral-400">
                {user?.email || 'user@sybr.local'}
              </span>
            </div>
          </div>

          <div>
            {role === 'admin' ? (
              <span className="px-3 py-1 rounded-full text-xs font-semibold bg-violet-50 text-violet-700 border border-violet-200 flex items-center gap-1.5">
                <Shield className="w-3.5 h-3.5 text-violet-600" />
                <span>Administrator</span>
              </span>
            ) : (
              <span className="px-3 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200 flex items-center gap-1.5">
                <Shield className="w-3.5 h-3.5 text-emerald-600" />
                <span>Customer</span>
              </span>
            )}
          </div>
        </div>

        {/* Identity Details */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
          <div className="p-3.5 rounded-xl bg-neutral-50 border border-neutral-200/60 space-y-1">
            <span className="text-[11px] font-medium text-neutral-400 block">Unique User ID</span>
            <span className="font-mono text-neutral-700 select-all">{user?.id || 'demo-user-001'}</span>
          </div>

          <div className="p-3.5 rounded-xl bg-neutral-50 border border-neutral-200/60 space-y-1">
            <span className="text-[11px] font-medium text-neutral-400 block">Authorization Role</span>
            <div className="flex items-center justify-between">
              <span className="font-semibold text-neutral-800 capitalize">{role}</span>
              <span className="text-[10px] text-neutral-400 italic">Server-Enforced (Read-Only)</span>
            </div>
          </div>

          <div className="p-3.5 rounded-xl bg-neutral-50 border border-neutral-200/60 space-y-1">
            <span className="text-[11px] font-medium text-neutral-400 block">Account Status</span>
            <span className="inline-flex items-center gap-1 text-emerald-700 font-semibold">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
              <span>Active</span>
            </span>
          </div>

          <div className="p-3.5 rounded-xl bg-neutral-50 border border-neutral-200/60 space-y-1">
            <span className="text-[11px] font-medium text-neutral-400 block">Environment</span>
            <span className="font-medium text-neutral-700">
              {user?.is_demo ? 'Local Prototype / Demo Workspace' : 'Production Supabase Auth'}
            </span>
          </div>
        </div>
      </div>

      {/* Security & Password Card */}
      <div className="bg-white rounded-2xl border border-neutral-200/80 shadow-sm p-6 space-y-5">
        <div className="border-b border-neutral-100 pb-3 flex items-center gap-2">
          <Key className="w-4 h-4 text-neutral-700" />
          <h2 className="text-sm font-bold text-neutral-900">Password & Security</h2>
        </div>

        {msg.text && (
          <div className={`p-3 rounded-xl text-xs flex items-center gap-2 ${
            msg.type === 'error'
              ? 'bg-rose-50 border border-rose-200 text-rose-700'
              : 'bg-emerald-50 border border-emerald-200 text-emerald-700'
          }`}>
            {msg.type === 'error' ? (
              <AlertCircle className="w-4 h-4 text-rose-500 shrink-0" />
            ) : (
              <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
            )}
            <span>{msg.text}</span>
          </div>
        )}

        <form onSubmit={handleUpdatePassword} className="space-y-4 max-w-md">
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-neutral-700 block">
              New Password
            </label>
            <input
              type="password"
              required
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              placeholder="••••••••••••"
              className="w-full px-3 py-2 text-xs bg-neutral-50 border border-neutral-200 rounded-xl focus:bg-white focus:border-neutral-900 focus:ring-1 focus:ring-neutral-900 outline-none transition font-mono"
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-neutral-700 block">
              Confirm New Password
            </label>
            <input
              type="password"
              required
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="••••••••••••"
              className="w-full px-3 py-2 text-xs bg-neutral-50 border border-neutral-200 rounded-xl focus:bg-white focus:border-neutral-900 focus:ring-1 focus:ring-neutral-900 outline-none transition font-mono"
            />
          </div>

          <Button
            type="submit"
            disabled={loading}
            className="text-xs font-semibold bg-neutral-900 hover:bg-neutral-800 text-white rounded-xl px-4 py-2 transition"
          >
            {loading ? 'Updating...' : 'Update Password'}
          </Button>
        </form>
      </div>

      {/* Session Actions Card */}
      <div className="bg-white rounded-2xl border border-neutral-200/80 shadow-sm p-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h3 className="text-sm font-bold text-neutral-900">Sign out of Sybr</h3>
          <p className="text-xs text-neutral-500">
            Terminate your active session and clear any cached local security credentials.
          </p>
        </div>

        <button
          type="button"
          onClick={handleLogout}
          className="inline-flex items-center gap-2 px-4 py-2 text-xs font-semibold text-rose-600 bg-rose-50 hover:bg-rose-100/80 border border-rose-200 rounded-xl transition active:scale-95"
        >
          <LogOut className="w-3.5 h-3.5" />
          <span>Sign Out</span>
        </button>
      </div>

    </div>
  );
}
