import React, { useState } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { 
  PanelLeft, 
  ChevronLeft, 
  ChevronRight, 
  Lock, 
  Search, 
  Maximize2, 
  Minimize2,
  X,
  Minus,
  Plus
} from 'lucide-react';

export default function WindowFrame({ children, isSidebarOpen, onToggleSidebar }) {
  const navigate = useNavigate();
  const location = useLocation();
  const [trafficHover, setTrafficHover] = useState(false);
  const [isMaximized, setIsMaximized] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  const handleSearch = (e) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/conversations?q=${encodeURIComponent(searchQuery.trim())}`);
      setSearchQuery('');
    }
  };

  const toggleMaximize = () => {
    setIsMaximized(!isMaximized);
  };

  const getWindowTitle = () => {
    const p = location.pathname;
    if (p === '/') return 'Dashboard — Support & Threat Intelligence';
    if (p.startsWith('/conversations/')) return 'Conversation Dossier Inspector';
    if (p === '/conversations') return 'All Conversations — Ingested Inbox';
    if (p === '/analyze') return 'Live Interactive Threat & Support Analyzer';
    if (p === '/upload') return 'Batch Ingestion & File Upload';
    if (p === '/health') return 'System Health & Security Benchmark';
    return 'Sybr Workstation';
  };

  return (
    <div className={`
      w-full mx-auto flex flex-col transition-all duration-300 ease-out select-none
      ${isMaximized 
        ? 'h-[calc(100vh-32px)] max-w-full rounded-none' 
        : 'h-[calc(100vh-92px)] max-w-[1480px] rounded-3xl shadow-window border border-white/60 my-auto'
      }
      bg-[#fbfbfd]/90 backdrop-blur-3xl overflow-hidden
    `}>
      
      {/* Translucent Frosted Glass Window Titlebar */}
      <header className="h-12 bg-white/70 backdrop-blur-2xl border-b border-black/[0.07] px-4 flex items-center justify-between gap-3 shrink-0 select-none">
        
        {/* Left: Traffic Lights & History Navigation */}
        <div className="flex items-center gap-3.5 min-w-0">
          {/* macOS Traffic Lights with Hover Symbols */}
          <div 
            onMouseEnter={() => setTrafficHover(true)}
            onMouseLeave={() => setTrafficHover(false)}
            className="flex items-center gap-2"
          >
            {/* Close Button */}
            <button
              onClick={() => navigate('/')}
              title="Close / Reset to Home"
              className="w-3 h-3 rounded-full bg-[#ff5f56] border border-[#e0443e]/40 shadow-sm flex items-center justify-center text-[#4a0000] text-[8px] font-bold"
            >
              {trafficHover && '×'}
            </button>
            {/* Minimize Button */}
            <button
              onClick={toggleMaximize}
              title="Minimize / Restore"
              className="w-3 h-3 rounded-full bg-[#ffbd2e] border border-[#dea123]/40 shadow-sm flex items-center justify-center text-[#593d00] text-[8px] font-bold"
            >
              {trafficHover && '−'}
            </button>
            {/* Maximize Button */}
            <button
              onClick={toggleMaximize}
              title={isMaximized ? "Restore Window" : "Maximize Window"}
              className="w-3 h-3 rounded-full bg-[#27c93f] border border-[#1aab29]/40 shadow-sm flex items-center justify-center text-[#004a0e] text-[8px] font-bold"
            >
              {trafficHover && '+'}
            </button>
          </div>

          {/* Sidebar Toggle & Back/Forward Navigation */}
          <div className="flex items-center gap-1 pl-2 border-l border-black/[0.08]">
            <button
              onClick={onToggleSidebar}
              title="Toggle Sidebar"
              className="p-1.5 rounded-lg text-[#59595e] hover:text-[#1d1d1f] hover:bg-black/[0.05] transition"
            >
              <PanelLeft className="w-4 h-4" />
            </button>
            <button
              onClick={() => window.history.back()}
              title="Back"
              className="p-1.5 rounded-lg text-[#59595e] hover:text-[#1d1d1f] hover:bg-black/[0.05] transition"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button
              onClick={() => window.history.forward()}
              title="Forward"
              className="p-1.5 rounded-lg text-[#59595e] hover:text-[#1d1d1f] hover:bg-black/[0.05] transition"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Center: Window Title with Secure Lock Badge */}
        <div className="flex items-center gap-1.5 text-xs text-[#1d1d1f] font-medium truncate max-w-sm sm:max-w-md">
          <Lock className="w-3 h-3 text-[#34c759] shrink-0" />
          <span className="truncate font-semibold">{getWindowTitle()}</span>
        </div>

        {/* Right: Window Search Field */}
        <div className="flex items-center gap-2">
          <form onSubmit={handleSearch} className="relative hidden sm:flex items-center">
            <Search className="w-3.5 h-3.5 absolute left-2.5 text-[#59595e] pointer-events-none" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search (⌘K)"
              className="w-36 md:w-48 bg-black/[0.04] hover:bg-black/[0.06] focus:bg-white text-xs text-[#1d1d1f] placeholder:text-[#8e8e93] rounded-lg pl-7 pr-3 py-1 border border-black/[0.06] focus:border-[#007aff] focus:ring-1 focus:ring-[#007aff]/30 transition outline-none"
            />
          </form>

          <button
            onClick={toggleMaximize}
            title={isMaximized ? "Restore Window" : "Full Screen Window"}
            className="p-1.5 rounded-lg text-[#59595e] hover:text-[#1d1d1f] hover:bg-black/[0.05] transition"
          >
            {isMaximized ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
          </button>
        </div>

      </header>

      {/* Main Window Body */}
      <div className="flex-1 flex overflow-hidden relative">
        {children}
      </div>

    </div>
  );
}
