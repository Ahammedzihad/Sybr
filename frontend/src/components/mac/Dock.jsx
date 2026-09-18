import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  LayoutDashboard, 
  MessageSquareText, 
  Zap, 
  UploadCloud, 
  Activity,
  Wifi,
  WifiOff
} from 'lucide-react';
import { isOfflineMode, setOfflineMode, fetchDashboard } from '../../api';

export default function Dock() {
  const location = useLocation();
  const [offline, setOffline] = useState(isOfflineMode());
  const [threatCount, setThreatCount] = useState(0);

  useEffect(() => {
    async function loadStats() {
      try {
        const data = await fetchDashboard();
        if (data?.kpis?.threats_detected) {
          setThreatCount(data.kpis.threats_detected);
        }
      } catch (err) {
        // quiet fallback
      }
    }
    loadStats();
    const interval = setInterval(loadStats, 20000);
    return () => clearInterval(interval);
  }, [offline]);

  const toggleOffline = () => {
    const next = !offline;
    setOffline(next);
    setOfflineMode(next);
  };

  const dockApps = [
    {
      name: 'Dashboard',
      path: '/',
      icon: LayoutDashboard,
      color: 'from-[#007aff] to-[#0051a8]',
      iconColor: 'text-white',
    },
    {
      name: 'Conversations',
      path: '/conversations',
      icon: MessageSquareText,
      color: 'from-[#34c759] to-[#248a3d]',
      iconColor: 'text-white',
      badge: threatCount > 0 ? threatCount : null,
    },
    {
      name: 'Live Analyzer',
      path: '/analyze',
      icon: Zap,
      color: 'from-[#ff9500] to-[#d66c00]',
      iconColor: 'text-white',
    },
    {
      name: 'Batch Ingestion',
      path: '/upload',
      icon: UploadCloud,
      color: 'from-[#32ade6] to-[#007aff]',
      iconColor: 'text-white',
    },
    {
      name: 'System Telemetry',
      path: '/health',
      icon: Activity,
      color: 'from-[#af52de] to-[#7928ca]',
      iconColor: 'text-white',
    },
  ];

  return (
    <div className="fixed bottom-3 left-1/2 -translate-x-1/2 z-40 select-none pointer-events-auto">
      {/* Translucent Frosted Glass Dock Container */}
      <div className="bg-white/55 backdrop-blur-2xl border border-white/50 shadow-dock rounded-3xl px-3 py-2 flex items-end gap-2.5 sm:gap-3 transition-all duration-200">
        
        {dockApps.map((app) => {
          const Icon = app.icon;
          const isActive = location.pathname === app.path || (app.path !== '/' && location.pathname.startsWith(app.path));

          return (
            <div key={app.name} className="group relative flex flex-col items-center">
              {/* Apple Floating Hover Tooltip */}
              <div className="absolute -top-9 px-2.5 py-1 rounded-lg bg-black/80 backdrop-blur-md text-white text-[11px] font-medium tracking-tight shadow-md opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-50">
                {app.name}
              </div>

              {/* App Icon Tile */}
              <Link
                to={app.path}
                className="relative w-11 h-11 sm:w-12 sm:h-12 rounded-2xl bg-gradient-to-b flex items-center justify-center shadow-[0_4px_12px_rgba(0,0,0,0.12)] group-hover:-translate-y-2 group-hover:scale-110 transition-all duration-200 active:scale-95"
                style={{
                  backgroundImage: app.name === 'Dashboard' 
                    ? 'linear-gradient(180deg, #007aff, #0051a8)'
                    : app.name === 'Conversations'
                    ? 'linear-gradient(180deg, #34c759, #248a3d)'
                    : app.name === 'Live Analyzer'
                    ? 'linear-gradient(180deg, #ff9500, #d66c00)'
                    : app.name === 'Batch Ingestion'
                    ? 'linear-gradient(180deg, #32ade6, #007aff)'
                    : 'linear-gradient(180deg, #af52de, #7928ca)',
                }}
              >
                <Icon className={`w-6 h-6 ${app.iconColor}`} />

                {/* Threat Notification Badge */}
                {app.badge && (
                  <span className="absolute -top-1.5 -right-1.5 min-w-[20px] h-5 px-1 rounded-full bg-[#ff3b30] border-2 border-white text-white text-[10px] font-mono font-bold flex items-center justify-center shadow-md animate-pulse">
                    {app.badge}
                  </span>
                )}
              </Link>

              {/* Active Indicator Dot */}
              <div className="h-1.5 flex items-center justify-center mt-1">
                {isActive && (
                  <span className="w-1.5 h-1.5 rounded-full bg-[#1d1d1f] shadow-sm animate-fade-in" />
                )}
              </div>
            </div>
          );
        })}

        {/* Vertical Separator */}
        <div className="w-[1px] h-9 bg-black/10 mx-0.5 self-center" />

        {/* Quick Mode Switcher in Dock */}
        <div className="group relative flex flex-col items-center">
          <div className="absolute -top-9 px-2.5 py-1 rounded-lg bg-black/80 backdrop-blur-md text-white text-[11px] font-medium tracking-tight shadow-md opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-50">
            {offline ? 'Switch to Live Online' : 'Switch to Offline Cache'}
          </div>

          <button
            onClick={toggleOffline}
            aria-label="Toggle Online/Offline Mode"
            className={`w-11 h-11 sm:w-12 sm:h-12 rounded-2xl flex items-center justify-center shadow-sm group-hover:-translate-y-2 group-hover:scale-110 transition-all duration-200 active:scale-95 border ${
              offline
                ? 'bg-[#ff9500]/15 text-[#8a4e00] border-[#ff9500]/35'
                : 'bg-[#34c759]/15 text-[#1b6d31] border-[#34c759]/35'
            }`}
          >
            {offline ? <WifiOff className="w-5 h-5" /> : <Wifi className="w-5 h-5" />}
          </button>
          
          <div className="h-1.5" />
        </div>

      </div>
    </div>
  );
}
