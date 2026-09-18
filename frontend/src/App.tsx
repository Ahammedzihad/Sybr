import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { Dashboard } from './pages/Dashboard';
import { Analyze } from './pages/Analyze';
import { Conversations } from './pages/Conversations';
import { api } from './api/client';
import { HealthStatus } from './types/analysis';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'analyze' | 'conversations'>('dashboard');
  const [health, setHealth] = useState<HealthStatus | null>(null);

  const checkHealth = async () => {
    try {
      const res = await api.getHealth();
      setHealth(res);
    } catch {
      setHealth({ status: 'offline', version: '1.0.0', mock_mode: 'unknown', database: 'disconnected' });
    }
  };

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        health={health}
        onRefreshHealth={checkHealth}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'dashboard' && (
          <Dashboard onNavigateToAnalyze={() => setActiveTab('analyze')} />
        )}
        {activeTab === 'analyze' && (
          <Analyze onAnalysisComplete={() => checkHealth()} />
        )}
        {activeTab === 'conversations' && (
          <Conversations onNavigateToAnalyze={() => setActiveTab('analyze')} />
        )}
      </main>

      <footer className="border-t border-slate-900 bg-slate-950/80 py-6 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>AI Security Analytics Platform — Hackathon Boilerplate</span>
          <div className="flex items-center gap-4 text-slate-400">
            <span>Person 1: Rules</span>
            <span>•</span>
            <span>Person 2: Gemini</span>
            <span>•</span>
            <span>Person 3: Backend & DB</span>
            <span>•</span>
            <span>Person 4: Frontend</span>
          </div>
        </div>
      </footer>
    </div>
  );
};
