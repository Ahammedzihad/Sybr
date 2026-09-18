import React, { useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';
import Conversations from './pages/Conversations';
import ConversationDetail from './pages/ConversationDetail';
import LiveAnalyzer from './pages/LiveAnalyzer';
import Upload from './pages/Upload';
import SystemHealth from './pages/SystemHealth';

export default function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <BrowserRouter>
      {/* Linear / Stripe Full-Bleed Application Shell */}
      <div className="h-screen w-screen bg-[#fafafa] text-neutral-900 flex overflow-hidden font-sans selection:bg-neutral-900 selection:text-white antialiased">
        
        {/* Collapsible Left Navigation Sidebar */}
        <Sidebar 
          isOpen={sidebarOpen} 
          onClose={() => setSidebarOpen(false)} 
        />

        {/* Main Application Workspace */}
        <div className="flex-1 flex flex-col min-w-0 h-screen overflow-hidden bg-[#fafafa]">
          
          {/* Stripe-Grade Top Command Bar */}
          <Navbar onToggleSidebar={() => setSidebarOpen((prev) => !prev)} />

          {/* Scrollable Document & Data Canvas */}
          <main className="flex-1 overflow-y-auto overflow-x-hidden bg-[#fafafa]">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/conversations" element={<Conversations />} />
              <Route path="/conversations/:id" element={<ConversationDetail />} />
              <Route path="/analyze" element={<LiveAnalyzer />} />
              <Route path="/upload" element={<Upload />} />
              <Route path="/health" element={<SystemHealth />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </main>

        </div>

      </div>
    </BrowserRouter>
  );
}
