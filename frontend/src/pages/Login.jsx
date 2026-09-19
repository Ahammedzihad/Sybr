import React, { useState } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { ShieldCheck, Lock, Mail, ArrowRight, AlertCircle, Sparkles, CheckCircle2, ShieldAlert } from 'lucide-react';
import { login, setAuthSession, getCurrentUser } from '../api';
import Button from '../components/ui/Button';

export default function Login() {
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  // Destination after login (if redirected from a protected deep link)
  const from = location.state?.from?.pathname || '/';

  const routeAfterLogin = (user) => {
    const role = user?.role || 'customer';
    if (from && from !== '/login') {
      if (from.startsWith('/admin') && role !== 'admin') {
        navigate('/', { replace: true });
        return;
      }
      navigate(from, { replace: true });
      return;
    }
    if (role === 'admin') {
      navigate('/admin', { replace: true });
    } else {
      navigate('/', { replace: true });
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setNotice('');

    if (!email.trim() || !password.trim()) {
      setError('Please provide both your email and password.');
      return;
    }

    if (!email.includes('@')) {
      setError('Please enter a valid email address.');
      return;
    }

    setLoading(true);
    try {
      const res = await login(email.trim(), password);
      routeAfterLogin(res.user);
    } catch (err) {
      setError(err.message || 'Invalid email or password. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleQuickCustomerDemo = async () => {
    setError('');
    setEmail('customer@sybr.local');
    setPassword('CustomerDemo2026!');
    setLoading(true);
    try {
      const res = await login('customer@sybr.local', 'CustomerDemo2026!');
      routeAfterLogin(res.user);
    } catch (err) {
      setAuthSession('demo-token', { id: 'demo-user-001', email: 'customer@sybr.local', role: 'customer' }, true);
      navigate('/', { replace: true });
    } finally {
      setLoading(false);
    }
  };

  const handleQuickAdminDemo = async () => {
    setError('');
    setEmail('admin@sybr.local');
    setPassword('AdminSuper2026!');
    setLoading(true);
    try {
      const res = await login('admin@sybr.local', 'AdminSuper2026!');
      routeAfterLogin(res.user);
    } catch (err) {
      setAuthSession('admin-demo-token', { id: 'admin-user-001', email: 'admin@sybr.local', role: 'admin' }, true);
      navigate('/admin', { replace: true });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen w-full bg-[#fbfbfd] flex items-center justify-center p-4 selection:bg-neutral-900 selection:text-white font-sans antialiased relative overflow-hidden">
      {/* Apple Subtle Frosted Radial Lighting */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[400px] bg-gradient-to-b from-[#0071e3]/10 to-transparent blur-3xl pointer-events-none" />

      <div className="w-full max-w-md relative z-10 space-y-6">
        
        {/* Brand Lockup */}
        <div className="text-center space-y-2">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-neutral-900 text-white shadow-lg shadow-neutral-900/10 mb-2">
            <ShieldCheck className="w-6 h-6 text-white" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-neutral-900">
            Sign in to Sybr
          </h1>
          <p className="text-xs text-neutral-500 max-w-xs mx-auto">
            AI Support Intelligence & Dual-Layer Threat Detection Platform
          </p>
        </div>

        {/* Evaluation Banner */}
        <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/25 flex items-start gap-2.5 text-left">
          <Sparkles className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
          <div className="flex-1 text-xs">
            <div className="font-semibold text-amber-900">
              Supabase Auth & Enterprise RBAC Enabled
            </div>
            <div className="text-amber-800/80 mt-0.5 text-[11px] leading-relaxed">
              Sign in with your Supabase account or choose a 1-click Quick Demo profile below to explore the Customer or Admin portals.
            </div>
          </div>
        </div>

        {/* Login Card */}
        <div className="bg-white/80 backdrop-blur-xl border border-neutral-200/80 rounded-2xl p-6 sm:p-8 shadow-sm space-y-5 text-left">
          
          {error && (
            <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0 text-rose-500" />
              <span>{error}</span>
            </div>
          )}

          {notice && (
            <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-700 text-xs flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-500" />
              <span>{notice}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-neutral-700 block">
                Email address
              </label>
              <div className="relative">
                <Mail className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-neutral-400 pointer-events-none" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="analyst@organization.com"
                  className="w-full pl-9 pr-3 py-2 text-xs bg-neutral-50 border border-neutral-200 rounded-xl focus:bg-white focus:border-neutral-900 focus:ring-1 focus:ring-neutral-900 outline-none transition"
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <label className="text-xs font-semibold text-neutral-700">
                  Password
                </label>
                <Link
                  to="/forgot-password"
                  className="text-[11px] text-[#0071e3] hover:underline font-medium"
                >
                  Forgot password?
                </Link>
              </div>
              <div className="relative">
                <Lock className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-neutral-400 pointer-events-none" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="w-full pl-9 pr-12 py-2 text-xs bg-neutral-50 border border-neutral-200 rounded-xl focus:bg-white focus:border-neutral-900 focus:ring-1 focus:ring-neutral-900 outline-none transition font-mono"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-[10px] text-neutral-400 hover:text-neutral-700 font-sans"
                >
                  {showPassword ? 'Hide' : 'Show'}
                </button>
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
                  <span>Sign In</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </>
              )}
            </Button>
          </form>

          <div className="pt-2 border-t border-neutral-100 flex items-center justify-between text-xs">
            <span className="text-neutral-500">Don't have an account?</span>
            <Link to="/signup" className="text-[#0071e3] font-medium hover:underline">
              Create Customer Account
            </Link>
          </div>

          <div className="relative flex items-center justify-center my-2">
            <div className="border-t border-neutral-200 w-full" />
            <span className="bg-white px-3 text-[10px] uppercase font-semibold text-neutral-400 absolute">
              Quick 1-Click Evaluation
            </span>
          </div>

          {/* Quick Demo Mode 1-Click Buttons */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1">
            <button
              type="button"
              onClick={handleQuickCustomerDemo}
              disabled={loading}
              className="flex items-center justify-center gap-2 py-2 px-3 rounded-xl border border-neutral-200 bg-neutral-50 hover:bg-neutral-100 text-neutral-800 text-xs font-medium transition active:scale-[0.99]"
            >
              <Sparkles className="w-3.5 h-3.5 text-emerald-600" />
              <span>Customer Demo</span>
            </button>

            <button
              type="button"
              onClick={handleQuickAdminDemo}
              disabled={loading}
              className="flex items-center justify-center gap-2 py-2 px-3 rounded-xl border border-neutral-200 bg-neutral-50 hover:bg-neutral-100 text-neutral-800 text-xs font-medium transition active:scale-[0.99]"
            >
              <ShieldAlert className="w-3.5 h-3.5 text-violet-600" />
              <span>Admin Demo</span>
            </button>
          </div>

        </div>

      </div>
    </div>
  );
}
