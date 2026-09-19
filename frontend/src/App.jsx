import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation, Link } from 'react-router-dom';
import { ShieldAlert, ArrowLeft } from 'lucide-react';
import Sidebar from './components/Sidebar';
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';
import CustomerDashboard from './pages/CustomerDashboard';
import Conversations from './pages/Conversations';
import ConversationDetail from './pages/ConversationDetail';
import LiveAnalyzer from './pages/LiveAnalyzer';
import CopilotStudio from './pages/CopilotStudio';
import Upload from './pages/Upload';
import SystemHealth from './pages/SystemHealth';
import Login from './pages/Login';
import Signup from './pages/Signup';
import ForgotPassword from './pages/ForgotPassword';
import ResetPassword from './pages/ResetPassword';
import Account from './pages/Account';
import AdminDashboard from './pages/AdminDashboard';
import AdminUsers from './pages/AdminUsers';
import AdminConversations from './pages/AdminConversations';
import AdminAuditLog from './pages/AdminAuditLog';
import { isAuthenticated, isAdmin, getUserRole } from './api';

function ProtectedRoute({ children }) {
  const location = useLocation();
  if (!isAuthenticated()) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }
  return children;
}

function AdminRoute({ children }) {
  if (!isAdmin()) {
    return (
      <div className="p-8 max-w-2xl mx-auto my-12 bg-white rounded-xl border border-rose-200 shadow-sm text-center">
        <div className="w-12 h-12 rounded-full bg-rose-100 text-rose-600 flex items-center justify-center mx-auto mb-4">
          <ShieldAlert className="w-6 h-6" />
        </div>
        <h2 className="text-lg font-bold text-neutral-900 mb-2">403 — Administrative Access Required</h2>
        <p className="text-sm text-neutral-600 mb-6 leading-relaxed">
          Your current account role (<span className="font-mono font-semibold text-rose-600">{getUserRole()}</span>) does not have privileges to access this administrative portal. All unauthorized access attempts are logged in the audit registry.
        </p>
        <Link
          to="/"
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-neutral-900 text-white text-xs font-semibold hover:bg-neutral-800 transition shadow-sm"
        >
          <ArrowLeft className="w-4 h-4" />
          Return to Customer Dashboard
        </Link>
      </div>
    );
  }
  return children;
}

function MainLayout({ sidebarOpen, setSidebarOpen }) {
  const admin = isAdmin();

  return (
    <div className="h-screen w-screen bg-[#fafafa] text-neutral-900 flex overflow-hidden font-sans selection:bg-neutral-900 selection:text-white antialiased">
      {/* Collapsible Left Navigation Sidebar */}
      <Sidebar 
        isOpen={sidebarOpen} 
        onClose={() => setSidebarOpen(false)} 
      />

      {/* Main Application Workspace */}
      <div className="flex-1 flex flex-col min-w-0 h-screen overflow-hidden bg-[#fafafa]">
        {/* Top Command Bar */}
        <Navbar onToggleSidebar={() => setSidebarOpen((prev) => !prev)} />

        {/* Scrollable Document & Data Canvas */}
        <main className="flex-1 overflow-y-auto overflow-x-hidden bg-[#fafafa]">
          <Routes>
            {/* Dashboard: Admin lands on AdminDashboard or Customer on CustomerDashboard */}
            <Route path="/" element={admin ? <AdminDashboard /> : <CustomerDashboard />} />
            <Route path="/customer" element={<CustomerDashboard />} />
            
            {/* Standard Sybr Workstation Pages */}
            <Route path="/conversations" element={<Conversations />} />
            <Route path="/conversations/:id" element={<ConversationDetail />} />
            <Route path="/analyze" element={<LiveAnalyzer />} />
            <Route path="/copilot" element={<CopilotStudio />} />
            <Route path="/upload" element={<Upload />} />
            <Route path="/account" element={<Account />} />
            
            {/* Dedicated Admin Portal Routes */}
            <Route path="/admin" element={<AdminRoute><AdminDashboard /></AdminRoute>} />
            <Route path="/admin/users" element={<AdminRoute><AdminUsers /></AdminRoute>} />
            <Route path="/admin/conversations" element={<AdminRoute><AdminConversations /></AdminRoute>} />
            <Route path="/admin/audit-logs" element={<AdminRoute><AdminAuditLog /></AdminRoute>} />
            <Route path="/health" element={<AdminRoute><SystemHealth /></AdminRoute>} />
            
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}

export default function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [, setAuthVersion] = useState(0);

  useEffect(() => {
    const handleAuthChange = () => setAuthVersion((v) => v + 1);
    window.addEventListener('auth-state-changed', handleAuthChange);
    return () => window.removeEventListener('auth-state-changed', handleAuthChange);
  }, []);

  return (
    <BrowserRouter>
      <Routes>
        {/* Public Authentication Routes */}
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route path="/reset-password" element={<ResetPassword />} />

        {/* Protected Application Workspace */}
        <Route
          path="/*"
          element={
            <ProtectedRoute>
              <MainLayout 
                sidebarOpen={sidebarOpen} 
                setSidebarOpen={setSidebarOpen} 
              />
            </ProtectedRoute>
          }
        />
      </Routes>
    </BrowserRouter>
  );
}
