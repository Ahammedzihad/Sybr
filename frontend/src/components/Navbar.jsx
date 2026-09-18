import React, { useState } from 'react';
import { useLocation, useNavigate, Link } from 'react-router-dom';
import { 
  PanelLeft, 
  Search, 
  Wifi, 
  WifiOff, 
  Zap,
  X
} from 'lucide-react';
import { isOfflineMode, setOfflineMode } from '../api';

export default function Navbar({ onToggleSidebar }) {
  const location = useLocation();
  const navigate = useNavigate();
  const [offline, setOffline] = useState(isOfflineMode());
  const [navSearch, setNavSearch] = useState('');

  const toggleOffline = () => {
    const next = !offline;
    setOffline(next);
    setOfflineMode(next);
  };

  const handleNavSearch = (e) => {
    e.preventDefault();
    if (navSearch.trim()) {
      navigate(`/conversations?q=${encodeURIComponent(navSearch.trim())}`);
      setNavSearch('');
    }
  };

  const getBreadcrumbTitle = () => {
    const p = location.pathname;
    if (p === '/') return 'Dashboard';
    if (p.startsWith('/conversations/')) return 'Conversation Inspector';
    if (p === '/conversations') return 'Conversations';
    if (p === '/analyze') return 'Live Analyzer';
    if (p === '/upload') return 'Batch Ingestion';
    if (p === '/health') return 'System Telemetry';
    return 'Workstation';
  };

  return (
    <header className="sticky top-0 z-30 bg-white border-b border-neutral-200/80 px-4 sm:px-6 h-13 flex items-center justify-between gap-3 select-none">
      
      {/* Left: Sidebar Toggle & Linear Breadcrumbs */}
      <div className="flex items-center gap-2.5 min-w-0">
        <button
          onClick={onToggleSidebar}
          aria-label="Toggle Sidebar"
          title="Toggle Sidebar"
          className="p-1.5 rounded-md text-neutral-500 hover:text-neutral-900 hover:bg-neutral-100 transition shrink-0"
        >
          <PanelLeft className="w-4 h-4" />
        </button>

        <div className="flex items-center gap-2 text-xs min-w-0">
          <Link to="/" className="text-neutral-500 hover:text-neutral-900 transition font-medium hidden sm:inline">
            Sybr
          </Link>
          <span className="text-neutral-300 hidden sm:inline">/</span>
          <span className="text-neutral-900 font-semibold truncate">
            {getBreadcrumbTitle()}
          </span>
        </div>
      </div>

      {/* Center: Stripe Command Search (⌘K) */}
      <div className="flex-1 max-w-xs sm:max-w-sm md:max-w-md mx-2">
        <form onSubmit={handleNavSearch} className="relative flex items-center">
          <Search className="w-3.5 h-3.5 absolute left-3 text-neutral-400 pointer-events-none" />
          <input
            type="text"
            value={navSearch}
            onChange={(e) => setNavSearch(e.target.value)}
            placeholder="Search tickets, customers, indicators..."
            aria-label="Search"
            className="w-full bg-neutral-50 hover:bg-neutral-100/80 focus:bg-white text-xs text-neutral-900 placeholder:text-neutral-400 rounded-md pl-8.5 pr-14 py-1.5 min-h-[32px] border border-neutral-200 focus:border-neutral-900 focus:ring-1 focus:ring-neutral-900 transition-all outline-none shadow-xs"
          />
          {navSearch ? (
            <button
              type="button"
              onClick={() => setNavSearch('')}
              aria-label="Clear Search"
              className="absolute right-2.5 p-0.5 rounded text-neutral-400 hover:text-neutral-700"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          ) : (
            <kbd className="absolute right-2.5 hidden sm:inline-flex items-center px-1.5 py-0.5 text-[10px] font-mono text-neutral-400 bg-white border border-neutral-200 rounded shadow-xs pointer-events-none">
              ⌘K
            </kbd>
          )}
        </form>
      </div>

      {/* Right: Network Mode Switch & Primary Action */}
      <div className="flex items-center gap-2 shrink-0">
        <button
          onClick={toggleOffline}
          title={offline ? "Switch to Live Online Mode" : "Switch to Offline Demo Cache"}
          className={`min-h-[30px] flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium border transition-all active:scale-[0.98] ${
            offline
              ? 'bg-amber-50 text-amber-800 border-amber-200 hover:bg-amber-100/70'
              : 'bg-emerald-50 text-emerald-800 border-emerald-200 hover:bg-emerald-100/70'
          }`}
        >
          {offline ? <WifiOff className="w-3 h-3 text-amber-700" /> : <Wifi className="w-3 h-3 text-emerald-700" />}
          <span className="hidden sm:inline">{offline ? 'Offline Cache' : 'Live Online'}</span>
        </button>

        <Link
          to="/analyze"
          title="Run Threat Analyzer"
          className="min-h-[30px] hidden md:flex items-center gap-1.5 px-3 py-1 rounded-md bg-neutral-900 hover:bg-neutral-800 text-white text-xs font-medium shadow-xs border border-neutral-900 transition active:scale-[0.98]"
        >
          <Zap className="w-3.5 h-3.5" />
          <span>New Analysis</span>
        </Link>
      </div>

    </header>
  );
}
