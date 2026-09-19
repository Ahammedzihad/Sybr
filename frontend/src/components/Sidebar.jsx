import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  ShieldCheck, 
  LayoutDashboard, 
  MessageSquareText, 
  Zap, 
  UploadCloud, 
  Activity, 
  Wifi, 
  WifiOff,
  ChevronRight,
  ChevronsUpDown,
  X,
  Bot,
  LogOut,
  User,
  Users,
  ShieldAlert,
  Sliders,
  BarChart3,
  Flame
} from 'lucide-react';
import { isOfflineMode, setOfflineMode, fetchHealth, getCurrentUser, logout, isAdmin, getUserRole } from '../api';

export default function Sidebar({ isOpen, onClose }) {
  const location = useLocation();
  const [offline, setOffline] = useState(isOfflineMode());
  const [backendHealth, setBackendHealth] = useState({ status: 'checking', ai_mode: '...' });
  const [user, setUser] = useState(getCurrentUser());
  const admin = isAdmin();
  const role = getUserRole();

  useEffect(() => {
    const handleAuth = () => setUser(getCurrentUser());
    window.addEventListener('auth-state-changed', handleAuth);
    return () => window.removeEventListener('auth-state-changed', handleAuth);
  }, []);

  useEffect(() => {
    async function check() {
      try {
        const res = await fetchHealth();
        setBackendHealth(res);
      } catch (err) {
        setBackendHealth({ status: 'offline', ai_mode: 'fallback' });
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

  const handleLogout = async () => {
    await logout();
    window.location.href = '/login';
  };

  // Dedicated Nav Links per role
  const customerNavLinks = [
    { name: 'Dashboard', path: '/', icon: LayoutDashboard, shortcut: '⌘1' },
    { name: 'Live Analyzer', path: '/analyze', icon: Zap, shortcut: '⌘2' },
    { name: 'My Conversations', path: '/conversations', icon: MessageSquareText, shortcut: '⌘3' },
    { name: 'Copilot Studio', path: '/copilot', icon: Bot, shortcut: '⌘4' },
    { name: 'CSV Ingestion', path: '/upload', icon: UploadCloud, shortcut: '⌘5' },
    { name: 'My Account', path: '/account', icon: User, shortcut: '⌘6' },
  ];

  const adminNavLinks = [
    { name: 'Admin Overview', path: '/admin', icon: LayoutDashboard, shortcut: '⌘1' },
    { name: 'Review & Inbox', path: '/admin/conversations', icon: MessageSquareText, shortcut: '⌘2' },
    { name: 'SecOps Threat Center', path: '/admin/security', icon: Flame, shortcut: '⌘3' },
    { name: 'Category & AI Analytics', path: '/admin/analytics', icon: BarChart3, shortcut: '⌘4' },
    { name: 'Customer Directory', path: '/admin/customers', icon: Users, shortcut: '⌘5' },
    { name: 'User Management', path: '/admin/users', icon: User, shortcut: '⌘6' },
    { name: 'Security Audit Log', path: '/admin/audit-logs', icon: ShieldAlert, shortcut: '⌘7' },
    { name: 'System Telemetry', path: '/health', icon: Activity, shortcut: '⌘8' },
    { name: 'Threat Analyzer', path: '/analyze', icon: Zap, shortcut: '⌘9' },
    { name: 'Copilot Studio', path: '/copilot', icon: Bot, shortcut: '⌘0' },
  ];

  const navLinks = admin ? adminNavLinks : customerNavLinks;

  const quickTags = [
    { name: 'Critical Threats', color: 'bg-rose-500', path: admin ? '/admin/conversations?risk=Critical' : '/conversations?risk=Critical' },
    { name: 'High Priority', color: 'bg-amber-500', path: admin ? '/admin/conversations?priority=High' : '/conversations?priority=High' },
    { name: 'Pending Followup', color: 'bg-yellow-500', path: admin ? '/admin/conversations?status=Unresolved' : '/conversations?status=Unresolved' },
    { name: 'Resolved Tickets', color: 'bg-emerald-500', path: admin ? '/admin/conversations?status=Resolved' : '/conversations?status=Resolved' },
    { name: 'Security Alerts', color: 'bg-indigo-500', path: admin ? '/admin/conversations?category=Security%20Concern' : '/conversations?category=Security%20Concern' },
  ];

  return (
    <>
      {/* Mobile Drawer Backdrop */}
      {isOpen && (
        <div 
          onClick={onClose} 
          className="fixed inset-0 bg-neutral-900/30 backdrop-blur-xs z-40 lg:hidden transition-opacity"
          aria-hidden="true"
        />
      )}

      {/* Linear-Style Left Sidebar Shell */}
      <aside 
        aria-label="Application Navigation"
        className={`
          transition-all duration-200 ease-out select-none flex flex-col justify-between shrink-0
          bg-[#fafafa] border-r border-neutral-200/80
          fixed top-0 bottom-0 left-0 z-50 w-60 lg:static lg:h-full lg:z-auto
          ${isOpen 
            ? 'translate-x-0 shadow-xl lg:shadow-none' 
            : '-translate-x-full lg:translate-x-0'
          }
        `}
      >
        <div className="flex flex-col flex-1 overflow-y-auto">
          
          {/* Workspace Switcher Header */}
          <div className="p-3 border-b border-neutral-200/60 flex items-center justify-between">
            <Link to="/" onClick={onClose} className="flex items-center gap-2.5 min-w-0 group flex-1">
              <div className="w-7 h-7 rounded-md bg-neutral-900 flex items-center justify-center text-white shadow-xs group-hover:bg-neutral-800 transition-colors shrink-0">
                <ShieldCheck className="w-4 h-4 text-white" />
              </div>
              <div className="flex flex-col min-w-0">
                <span className="font-semibold text-xs text-neutral-900 truncate leading-tight">
                  Sybr Security
                </span>
                <span className="text-[10px] text-neutral-500 font-mono truncate leading-tight">
                  {admin ? 'admin-workstation' : 'customer-portal'}
                </span>
              </div>
            </Link>
            <div className="flex items-center gap-1">
              <button 
                onClick={onClose}
                aria-label="Close Sidebar"
                className="lg:hidden p-1 rounded-md text-neutral-500 hover:text-neutral-900 hover:bg-neutral-200/60"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Navigation Items */}
          <div className="p-3 space-y-4">
            <div>
              <div className="px-2 mb-1.5 flex items-center justify-between text-[10px] font-semibold text-neutral-400 uppercase tracking-wider">
                <span>{admin ? 'Admin Operations' : 'Customer Workspace'}</span>
                <span className={`px-1 rounded text-[8px] font-bold uppercase tracking-wider ${admin ? 'bg-indigo-100 text-indigo-800' : 'bg-neutral-200/80 text-neutral-700'}`}>
                  {role}
                </span>
              </div>
              <nav className="space-y-0.5">
                {navLinks.map((item) => {
                  const Icon = item.icon;
                  const isActive = location.pathname === item.path;
                  return (
                    <Link
                      key={item.path}
                      to={item.path}
                      onClick={onClose}
                      className={`flex items-center justify-between px-2.5 py-1.5 rounded-md text-xs font-medium transition-all group ${
                        isActive
                          ? 'bg-white text-neutral-900 font-semibold shadow-xs border border-neutral-200/80'
                          : 'text-neutral-600 hover:text-neutral-900 hover:bg-neutral-200/40'
                      }`}
                    >
                      <div className="flex items-center gap-2.5 min-w-0">
                        <Icon className={`w-4 h-4 shrink-0 ${isActive ? 'text-neutral-900' : 'text-neutral-500 group-hover:text-neutral-700'}`} />
                        <span className="truncate">{item.name}</span>
                      </div>
                      <span className="text-[10px] font-mono text-neutral-400 opacity-0 group-hover:opacity-100 transition-opacity hidden sm:inline">
                        {item.shortcut}
                      </span>
                    </Link>
                  );
                })}
              </nav>
            </div>

            {/* Saved Views / Quick Security Tags */}
            <div>
              <div className="px-2 mb-1.5 text-[10px] font-semibold text-neutral-400 uppercase tracking-wider">
                Saved Views
              </div>
              <div className="space-y-0.5">
                {quickTags.map((tag) => (
                  <Link
                    key={tag.name}
                    to={tag.path}
                    onClick={onClose}
                    className="flex items-center justify-between px-2.5 py-1.5 rounded-md text-xs font-medium text-neutral-600 hover:text-neutral-900 hover:bg-neutral-200/40 transition-colors group"
                  >
                    <div className="flex items-center gap-2 min-w-0">
                      <span className={`w-1.5 h-1.5 rounded-full ${tag.color} shrink-0`} />
                      <span className="truncate">{tag.name}</span>
                    </div>
                    <ChevronRight className="w-3 h-3 text-neutral-400 opacity-0 group-hover:opacity-100 transition-opacity" />
                  </Link>
                ))}
              </div>
            </div>
          </div>

        </div>

        {/* Footer: Telemetry Status & Mode Switch */}
        <div className="p-3 border-t border-neutral-200/60 bg-white space-y-2">
          {/* Status capsule */}
          <div className="flex items-center justify-between px-2.5 py-1.5 rounded-md bg-neutral-50 border border-neutral-200/70 text-xs">
            <div className="flex items-center gap-2 min-w-0">
              <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${backendHealth.status === 'ok' ? 'bg-emerald-500' : 'bg-amber-500'}`} />
              <span className="text-[11px] font-medium text-neutral-700 truncate">
                {offline ? 'Mock Cache' : (backendHealth.ai_mode === 'gemini' ? 'Gemini 2.5 Flash' : 'Rule Engine')}
              </span>
            </div>
            <span className="text-[10px] font-mono text-neutral-500 shrink-0 font-medium">
              {backendHealth.status === 'ok' ? 'Online' : 'Offline'}
            </span>
          </div>

          {/* Mode Switcher Button */}
          <button
            onClick={toggleOffline}
            title={offline ? "Switch to Live Online Mode" : "Switch to Offline Demo Cache"}
            className={`w-full min-h-[30px] flex items-center justify-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium border transition-all active:scale-[0.98] ${
              offline
                ? 'bg-amber-50 text-amber-800 border-amber-200 hover:bg-amber-100/70'
                : 'bg-emerald-50 text-emerald-800 border-emerald-200 hover:bg-emerald-100/70'
            }`}
          >
            {offline ? <WifiOff className="w-3.5 h-3.5 text-amber-700" /> : <Wifi className="w-3.5 h-3.5 text-emerald-700" />}
            <span>{offline ? 'Mode: Offline Cache' : 'Mode: Live Online'}</span>
          </button>

          {/* User Account / Logout */}
          {user && (
            <div className="pt-2 border-t border-neutral-200/60 flex items-center justify-between gap-2 text-xs">
              <Link to="/account" onClick={onClose} className="flex items-center gap-2 min-w-0 flex-1 hover:opacity-80 transition group">
                <div className={`w-6 h-6 rounded-full text-white flex items-center justify-center text-[10px] font-bold shrink-0 ${admin ? 'bg-indigo-600' : 'bg-neutral-900'}`}>
                  {user.email ? user.email[0].toUpperCase() : 'U'}
                </div>
                <div className="min-w-0 flex-1">
                  <div className="text-[11px] font-semibold text-neutral-800 truncate group-hover:text-neutral-900">
                    {user.email || 'Current User'}
                  </div>
                  <div className="text-[9px] text-neutral-400 font-mono leading-none capitalize">
                    {role} • {user.is_demo ? 'Demo' : 'Auth'}
                  </div>
                </div>
              </Link>
              <button
                onClick={handleLogout}
                title="Log out of session"
                aria-label="Log out"
                className="p-1 rounded text-neutral-400 hover:text-rose-600 hover:bg-rose-50 transition shrink-0"
              >
                <LogOut className="w-3.5 h-3.5" />
              </button>
            </div>
          )}
        </div>

      </aside>
    </>
  );
}
