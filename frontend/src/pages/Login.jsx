import React, { useState } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { ShieldCheck, Lock, Mail, ArrowRight, AlertCircle, CheckCircle2, X } from 'lucide-react';
import { login } from '../api';
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
      setError('Please enter both your email address and password.');
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
      setError(err.message || 'Invalid email or password.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen w-full bg-[#fbfbfd] flex items-center justify-center p-4 selection:bg-neutral-900 selection:text-white font-sans antialiased relative overflow-hidden">
      {/* Apple Subtle Frosted Radial Lighting */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[400px] bg-gradient-to-b from-[#0071e3]/10 to-transparent blur-3xl pointer-events-none" />

      <div className="w-full max-w-md relative z-10 space-y-6">
        
        {/* 1. Sybr Branding & Logo, 2. Title, 3. Short Subtitle */}
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
            {/* 4. Email address input */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-neutral-700 block">
                Email address
              </label>
              <div className="relative">
                <Mail className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-neutral-400 pointer-events-none" />
                <input
                  type="email"
                  required
                  autoComplete="username"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@company.com"
                  className="w-full pl-9 pr-8 py-2 text-xs bg-neutral-50 border border-neutral-200 rounded-xl focus:bg-white focus:border-neutral-900 focus:ring-1 focus:ring-neutral-900 outline-none transition"
                />
                {email && (
                  <button
                    type="button"
                    onClick={() => setEmail('')}
                    title="Clear email"
                    className="absolute right-2.5 top-1/2 -translate-y-1/2 text-neutral-400 hover:text-neutral-700 p-0.5 rounded-full hover:bg-neutral-200/60 transition"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>
            </div>

            {/* 5. Password input, 6. Show/Hide password, 7. Forgot password */}
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
                  autoComplete="current-password"
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

            {/* 8. Sign In button */}
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

          {/* 9. Create Customer Account / Sign Up link */}
          <div className="pt-2 border-t border-neutral-100 flex items-center justify-between text-xs">
            <span className="text-neutral-500">Don't have an account?</span>
            <Link to="/signup" className="text-[#0071e3] font-medium hover:underline">
              Create Customer Account
            </Link>
          </div>

        </div>

      </div>
    </div>
  );
}
