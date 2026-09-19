import React, { useState, useEffect } from 'react';
import { 
  Wifi, 
  WifiOff, 
  ShieldCheck, 
  BatteryCharging, 
  Sliders, 
  Volume2, 
  Search,
  Command
} from 'lucide-react';
import { isOfflineMode, setOfflineMode, fetchHealth } from '../../api';

export default function MenuBar() {
  const [offline, setOffline] = useState(isOfflineMode());
  const [health, setHealth] = useState({ status: 'checking', ai_mode: '...' });
  const [timeStr, setTimeStr] = useState('');
  const [appleMenuOpen, setAppleMenuOpen] = useState(false);

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setTimeStr(
        now.toLocaleDateString('en-US', {
          weekday: 'short',
          month: 'short',
          day: 'numeric',
        }) +
          '  ' +
          now.toLocaleTimeString('en-US', {
            hour: 'numeric',
            minute: '2-digit',
          })
      );
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    async function check() {
      try {
        const res = await fetchHealth();
        setHealth(res);
      } catch (err) {
        setHealth({ status: 'offline', ai_mode: 'fallback' });
      }
    }
    check();
    const interval = setInterval(check, 15000);
    return () => clearInterval(interval);
  }, [offline]);

  const toggleOffline = () => {
    const next = !offline;
    setOffline(next);
    setOfflineMode(next);
  };

  return (
    <div className="h-7.5 w-full bg-white/65 backdrop-blur-2xl border-b border-black/[0.07] px-4 flex items-center justify-between text-xs select-none z-50 text-[#1d1d1f] font-sans font-medium">
      
      {/* Left Menu Items */}
      <div className="flex items-center gap-4 relative">
        {/* Apple Logo Dropdown */}
        <button
          onClick={() => setAppleMenuOpen(!appleMenuOpen)}
          className="font-bold text-sm text-[#1d1d1f] hover:opacity-75 transition"
          aria-label="Apple Menu"
        >
          
        </button>

        {appleMenuOpen && (
          <div className="absolute top-7 left-0 w-52 bg-white/85 backdrop-blur-2xl border border-black/[0.08] shadow-2xl rounded-xl py-1 text-xs text-[#1d1d1f] z-50 animate-fade-in font-normal">
            <div className="px-3 py-1.5 font-semibold text-[11px] text-[#59595e] border-b border-black/[0.06]">
              Sybr Workstation 2.0
            </div>
            <button 
              onClick={() => setAppleMenuOpen(false)} 
              className="w-full text-left px-3 py-1.5 hover:bg-[#007aff] hover:text-white transition rounded-md"
            >
              About This Workstation
            </button>
            <button 
              onClick={() => { toggleOffline(); setAppleMenuOpen(false); }} 
              className="w-full text-left px-3 py-1.5 hover:bg-[#007aff] hover:text-white transition rounded-md"
            >
              {offline ? 'Switch to Live Online Mode' : 'Switch to Offline Cache'}
            </button>
            <div className="my-1 border-t border-black/[0.06]" />
            <button 
              onClick={() => { window.location.reload(); }} 
              className="w-full text-left px-3 py-1.5 hover:bg-[#007aff] hover:text-white transition rounded-md"
            >
              Restart Session
            </button>
          </div>
        )}

        {/* Application Brand */}
        <span className="font-bold text-xs tracking-tight">Sybr Pro</span>

        {/* Top Menus */}
        <div className="hidden sm:flex items-center gap-3.5 text-[#3c3c43] text-xs">
          <span className="hover:text-[#1d1d1f] cursor-pointer transition">File</span>
          <span className="hover:text-[#1d1d1f] cursor-pointer transition">Edit</span>
          <span className="hover:text-[#1d1d1f] cursor-pointer transition">View</span>
          <span className="hover:text-[#1d1d1f] cursor-pointer transition">Intelligence</span>
          <span className="hover:text-[#1d1d1f] cursor-pointer transition">Window</span>
          <span className="hover:text-[#1d1d1f] cursor-pointer transition">Help</span>
        </div>
      </div>

      {/* Right System Telemetry */}
      <div className="flex items-center gap-3 text-xs">
        {/* Engine Telemetry Capsule */}
        <div className="hidden md:flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-black/[0.04] border border-black/[0.06] text-[11px]">
          <span className={`w-2 h-2 rounded-full ${health.status === 'ok' ? 'bg-[#34c759]' : 'bg-[#ff9500]'}`} />
          <span className="font-medium text-[#1d1d1f]">
            {offline ? 'Mock Cache' : (health.ai_mode === 'gemini' ? 'Gemini 2.5 Flash' : 'Rule Engine')}
          </span>
        </div>

        {/* Online / Offline Switch */}
        <button
          onClick={toggleOffline}
          title={offline ? "Click to switch to Live Backend" : "Click to switch to Offline Mock Cache"}
          className={`flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold border transition active:scale-95 ${
            offline
              ? 'bg-[#ff9500]/12 text-[#8a4e00] border-[#ff9500]/30'
              : 'bg-[#34c759]/12 text-[#1b6d31] border-[#34c759]/30'
          }`}
        >
          {offline ? <WifiOff className="w-3 h-3" /> : <Wifi className="w-3 h-3" />}
          <span className="hidden sm:inline">{offline ? 'Offline' : 'Online'}</span>
        </button>

        {/* Battery / Power Indicator */}
        <div className="hidden lg:flex items-center gap-1 text-[#59595e]">
          <BatteryCharging className="w-3.5 h-3.5 text-[#34c759]" />
          <span className="text-[11px] font-mono font-medium">100%</span>
        </div>

        {/* Clock */}
        <span className="font-mono text-xs font-semibold text-[#1d1d1f] pl-1">
          {timeStr}
        </span>
      </div>

    </div>
  );
}
