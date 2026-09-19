import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { ShieldCheck, Lock, ArrowRight, AlertCircle, CheckCircle2 } from 'lucide-react';
import { updatePassword } from '../api';
import Button from '../components/ui/Button';

export default function ResetPassword() {
  const navigate = useNavigate();
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (password.length < 6) {
      setError('Password must be at least 6 characters.');
      return;
    }
    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    setLoading(true);
    try {
      await updatePassword(password);
      setSuccess('Your password has been updated. Redirecting to login...');
      setTimeout(() => {
        navigate('/login', { replace: true });
      }, 2000);
    } catch (err) {
      setError(err.message || 'Failed to update password. Reset link may be expired.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen w-full bg-[#fbfbfd] flex items-center justify-center p-4 selection:bg-neutral-900 selection:text-white font-sans antialiased relative overflow-hidden">
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[400px] bg-gradient-to-b from-[#0071e3]/10 to-transparent blur-3xl pointer-events-none" />

      <div className="w-full max-w-md relative z-10 space-y-6">
        <div className="text-center space-y-2">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-neutral-900 text-white shadow-lg shadow-neutral-900/10 mb-2">
            <ShieldCheck className="w-6 h-6 text-white" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-neutral-900">
            Set a new password
          </h1>
          <p className="text-xs text-neutral-500 max-w-xs mx-auto">
            Choose a strong password to protect your account.
          </p>
        </div>

        <div className="bg-white/80 backdrop-blur-xl border border-neutral-200/80 rounded-2xl p-6 sm:p-8 shadow-sm space-y-5 text-left">
          {error && (
            <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0 text-rose-500" />
              <span>{error}</span>
            </div>
          )}

          {success && (
            <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-700 text-xs flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-500" />
              <span>{success}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-neutral-700 block">
                New Password
              </label>
              <div className="relative">
                <Lock className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-neutral-400 pointer-events-none" />
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full pl-9 pr-3 py-2 text-xs bg-neutral-50 border border-neutral-200 rounded-xl focus:bg-white focus:border-neutral-900 focus:ring-1 focus:ring-neutral-900 outline-none transition font-mono"
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-neutral-700 block">
                Confirm New Password
              </label>
              <div className="relative">
                <Lock className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-neutral-400 pointer-events-none" />
                <input
                  type="password"
                  required
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full pl-9 pr-3 py-2 text-xs bg-neutral-50 border border-neutral-200 rounded-xl focus:bg-white focus:border-neutral-900 focus:ring-1 focus:ring-neutral-900 outline-none transition font-mono"
                />
              </div>
            </div>

            <Button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 text-xs font-semibold bg-neutral-900 hover:bg-neutral-800 text-white rounded-xl shadow-md transition flex items-center justify-center gap-2"
            >
              {loading ? (
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <>
                  <span>Save New Password</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </>
              )}
            </Button>

            <div className="pt-2 text-center">
              <Link to="/login" className="text-xs text-neutral-500 hover:text-neutral-800">
                Cancel and return to Sign In
              </Link>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
