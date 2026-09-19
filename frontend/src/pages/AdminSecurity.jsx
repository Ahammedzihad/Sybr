import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  ShieldAlert, 
  ShieldCheck, 
  Globe, 
  Mail, 
  Paperclip, 
  RefreshCw, 
  ArrowRight,
  AlertTriangle,
  Flame,
  ExternalLink
} from 'lucide-react';
import { fetchAdminSecurityAnalytics } from '../api';

export default function AdminSecurity() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const loadData = async () => {
    try {
      const res = await fetchAdminSecurityAnalytics();
      setData(res);
    } catch (err) {
      console.error('Failed to load security analytics:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6 animate-fade-in text-left">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-neutral-200/80 pb-5">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-semibold tracking-wide uppercase bg-rose-50 text-rose-700 border border-rose-200">
              SecOps Threat Center
            </span>
            <span className="text-xs text-neutral-400">Cyber Intelligence & Attack Surface Analysis</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-neutral-900">
            Threat Intelligence & Phishing Interceptions
          </h1>
          <p className="text-xs text-neutral-500">
            Real-time telemetry on social engineering vectors, lookalike domain spoofing, and credential harvesting attempts.
          </p>
        </div>

        <button
          onClick={() => { setRefreshing(true); loadData(); }}
          disabled={refreshing}
          className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl border border-neutral-200 text-neutral-700 hover:bg-neutral-50 text-xs font-semibold transition active:scale-95"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Threat Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white p-5 rounded-2xl border border-neutral-200/80 shadow-xs space-y-2">
          <div className="flex items-center justify-between text-neutral-500 text-xs">
            <span className="font-medium">Total Intercepted Threats</span>
            <ShieldAlert className="w-4 h-4 text-rose-600" />
          </div>
          <div className="text-3xl font-bold text-rose-600">
            {loading ? '-' : data?.total_threats ?? 0}
          </div>
          <p className="text-[11px] text-neutral-400">Verified malicious customer communications</p>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-neutral-200/80 shadow-xs space-y-2">
          <div className="flex items-center justify-between text-neutral-500 text-xs">
            <span className="font-medium">Critical Threat Severity</span>
            <AlertTriangle className="w-4 h-4 text-red-600" />
          </div>
          <div className="text-3xl font-bold text-red-600">
            {loading ? '-' : data?.critical_count ?? 0}
          </div>
          <p className="text-[11px] text-neutral-400">Credential or OTP extraction payloads</p>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-neutral-200/80 shadow-xs space-y-2">
          <div className="flex items-center justify-between text-neutral-500 text-xs">
            <span className="font-medium">High Risk Anomalies</span>
            <Flame className="w-4 h-4 text-amber-500" />
          </div>
          <div className="text-3xl font-bold text-amber-600">
            {loading ? '-' : data?.high_count ?? 0}
          </div>
          <p className="text-[11px] text-neutral-400">Suspicious domains & brand impersonation</p>
        </div>
      </div>

      {/* Threat Types & Techniques Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        
        {/* Threat Types Breakdown */}
        <div className="bg-white p-5 rounded-2xl border border-neutral-200/80 shadow-xs space-y-4">
          <div className="flex items-center justify-between border-b border-neutral-100 pb-3">
            <h2 className="text-xs font-bold text-neutral-900 uppercase tracking-wide">Threat Classifications</h2>
            <span className="text-[11px] text-neutral-400">By Vector Type</span>
          </div>

          <div className="space-y-3 text-xs">
            {loading ? (
              <div className="p-8 text-center text-neutral-400">Loading threat vectors...</div>
            ) : !data?.threat_types || Object.keys(data.threat_types).length === 0 ? (
              <div className="p-8 text-center text-neutral-400">No malicious threats detected in dataset.</div>
            ) : (
              Object.entries(data.threat_types).map(([type, count]) => (
                <div key={type} className="flex items-center justify-between p-3 rounded-xl bg-neutral-50 border border-neutral-200/60">
                  <span className="font-semibold text-neutral-800">{type}</span>
                  <div className="flex items-center gap-3">
                    <span className="font-mono font-bold text-neutral-900">{count} incident{count > 1 ? 's' : ''}</span>
                    <Link
                      to={`/admin/conversations?q=${encodeURIComponent(type)}`}
                      className="text-[11px] text-[#0071e3] hover:underline"
                    >
                      Filter
                    </Link>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Attack Techniques */}
        <div className="bg-white p-5 rounded-2xl border border-neutral-200/80 shadow-xs space-y-4">
          <div className="flex items-center justify-between border-b border-neutral-100 pb-3">
            <h2 className="text-xs font-bold text-neutral-900 uppercase tracking-wide">Detected Social Engineering Techniques</h2>
            <span className="text-[11px] text-neutral-400">Behavioral Signals</span>
          </div>

          <div className="space-y-3 text-xs">
            {loading ? (
              <div className="p-8 text-center text-neutral-400">Loading techniques...</div>
            ) : !data?.techniques || Object.keys(data.techniques).length === 0 ? (
              <div className="p-8 text-center text-neutral-400">No technique signatures registered.</div>
            ) : (
              Object.entries(data.techniques).map(([tech, count]) => (
                <div key={tech} className="flex items-center justify-between p-3 rounded-xl bg-neutral-50 border border-neutral-200/60">
                  <span className="font-medium text-neutral-800">{tech}</span>
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-100 text-rose-700">
                    {count} detected
                  </span>
                </div>
              ))
            )}
          </div>
        </div>

      </div>

      {/* Top Lookalike Domains & Top Senders */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        
        {/* Lookalike Domains */}
        <div className="bg-white p-5 rounded-2xl border border-neutral-200/80 shadow-xs space-y-4">
          <div className="flex items-center justify-between border-b border-neutral-100 pb-3">
            <div className="flex items-center gap-2">
              <Globe className="w-4 h-4 text-blue-600" />
              <h2 className="text-xs font-bold text-neutral-900 uppercase tracking-wide">Identified Suspicious Domains</h2>
            </div>
            <span className="text-[11px] text-neutral-400">Brand Spoofing</span>
          </div>

          <div className="space-y-2 text-xs">
            {loading ? (
              <div className="p-8 text-center text-neutral-400">Analyzing domain logs...</div>
            ) : !data?.top_domains?.length ? (
              <div className="p-8 text-center text-neutral-400">No suspicious domains extracted.</div>
            ) : (
              data.top_domains.map((item, idx) => (
                <div key={idx} className="flex items-center justify-between p-2.5 rounded-xl bg-neutral-50 border border-neutral-200/60 font-mono text-[11px]">
                  <span className="text-rose-700 font-semibold truncate max-w-xs">{item.domain}</span>
                  <span className="text-neutral-500 font-sans">{item.count} appearance{item.count > 1 ? 's' : ''}</span>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Suspicious Sender Domains */}
        <div className="bg-white p-5 rounded-2xl border border-neutral-200/80 shadow-xs space-y-4">
          <div className="flex items-center justify-between border-b border-neutral-100 pb-3">
            <div className="flex items-center gap-2">
              <Mail className="w-4 h-4 text-indigo-600" />
              <h2 className="text-xs font-bold text-neutral-900 uppercase tracking-wide">Analyzed Sender Origins</h2>
            </div>
            <span className="text-[11px] text-neutral-400">Domain Origins</span>
          </div>

          <div className="space-y-2 text-xs">
            {loading ? (
              <div className="p-8 text-center text-neutral-400">Analyzing sender logs...</div>
            ) : !data?.top_senders?.length ? (
              <div className="p-8 text-center text-neutral-400">No external sender headers recorded.</div>
            ) : (
              data.top_senders.map((item, idx) => (
                <div key={idx} className="flex items-center justify-between p-2.5 rounded-xl bg-neutral-50 border border-neutral-200/60 font-mono text-[11px]">
                  <span className="text-neutral-800 truncate max-w-xs">{item.domain}</span>
                  <span className="text-neutral-500 font-sans">{item.count} message{item.count > 1 ? 's' : ''}</span>
                </div>
              ))
            )}
          </div>
        </div>

      </div>

    </div>
  );
}
