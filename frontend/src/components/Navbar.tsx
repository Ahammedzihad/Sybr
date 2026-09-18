import React from 'react';
import { Shield, RefreshCw } from 'lucide-react';
import { HealthStatus } from '../types/analysis';

interface NavbarProps {
  activeTab: 'dashboard' | 'analyze' | 'conversations';
  setActiveTab: (tab: 'dashboard' | 'analyze' | 'conversations') => void;
  health: HealthStatus | null;
  onRefreshHealth: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  health,
  onRefreshHealth,
}) => {
  const isOnline = Boolean(health && health.status === 'ok');

  return (
    <header className="sticky top-0 z-40 w-full border-b border-slate-800/80 bg-slate-950/90 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-sky-600 to-indigo-500 flex items-center justify-center shadow-lg shadow-sky-500/20">
            <Shield className="h-5 w-5 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold tracking-tight text-white text-base sm:text-lg">
                AI Security Analytics
              </span>
              <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-sky-950 text-sky-400 border border-sky-800">
                v1.0
              </span>
            </div>
            <p className="text-xs text-slate-400 hidden sm:block">
              Rule-Based Heuristics + Gemini Threat Intelligence
            </p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="flex items-center gap-1 rounded-lg bg-slate-900/90 p-1 border border-slate-800">
          <button
            onClick={() => setActiveTab('dashboard')}
            className={`px-3 py-1.5 rounded-md text-xs sm:text-sm font-medium transition-colors ${
              activeTab === 'dashboard'
                ? 'bg-sky-600 text-white shadow'
                : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
            }`}
          >
            Dashboard
          </button>
          <button
            onClick={() => setActiveTab('analyze')}
            className={`px-3 py-1.5 rounded-md text-xs sm:text-sm font-medium transition-colors ${
              activeTab === 'analyze'
                ? 'bg-sky-600 text-white shadow'
                : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
            }`}
          >
            Analyze Message
          </button>
          <button
            onClick={() => setActiveTab('conversations')}
            className={`px-3 py-1.5 rounded-md text-xs sm:text-sm font-medium transition-colors ${
              activeTab === 'conversations'
                ? 'bg-sky-600 text-white shadow'
                : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
            }`}
          >
            Conversations
          </button>
        </nav>

        {/* Backend Health Status */}
        <div className="flex items-center gap-2">
          <div
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-xs font-medium ${
              isOnline
                ? 'bg-emerald-950/60 border-emerald-800/50 text-emerald-400'
                : 'bg-rose-950/60 border-rose-800/50 text-rose-400'
            }`}
          >
            <span
              className={`h-2 w-2 rounded-full ${
                isOnline ? 'bg-emerald-400 animate-pulse' : 'bg-rose-400'
              }`}
            />
            <span className="hidden md:inline">API:</span>
            <span>{isOnline ? 'Online' : 'Offline'}</span>
            {health?.mock_mode === 'true' && (
              <span className="ml-1 text-[10px] text-amber-300 font-mono px-1 rounded bg-amber-950/80 border border-amber-800/50">
                MOCK
              </span>
            )}
          </div>

          <button
            onClick={onRefreshHealth}
            title="Refresh status"
            aria-label="Refresh status"
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <RefreshCw className="h-4 w-4" />
          </button>
        </div>
      </div>
    </header>
  );
};
