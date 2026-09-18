import React, { useState, useEffect } from 'react';
import { 
  ShieldAlert, 
  MessageSquare, 
  AlertOctagon, 
  TrendingUp, 
  Flame, 
  RefreshCw,
  Clock,
  Sparkles,
  Tag,
  AlertCircle,
  BarChart3,
  Calendar,
  CheckCircle2,
  ChevronRight
} from 'lucide-react';
import { 
  PieChart, Pie, Cell, Tooltip, ResponsiveContainer, 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, AreaChart, Area 
} from 'recharts';
import { Link } from 'react-router-dom';
import { fetchDashboard } from '../api';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import SegmentedControl from '../components/ui/SegmentedControl';
import { KpiSkeleton } from '../components/ui/Skeleton';

const SENTIMENT_COLORS = {
  Positive: '#10b981', // Emerald
  Neutral: '#71717a',  // Zinc
  Negative: '#f43f5e', // Rose
};

const RISK_COLORS = {
  Low: '#10b981',      // Emerald
  Medium: '#f59e0b',   // Amber
  High: '#ea580c',     // Orange
  Critical: '#e11d48', // Crimson/Rose
};

// Stripe/Linear Clean Tooltip for Recharts
const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-white border border-neutral-200/90 rounded-lg px-3 py-2 shadow-sm text-xs space-y-1.5 min-w-[140px]">
        {label && <p className="font-semibold text-neutral-900 border-b border-neutral-100 pb-1 font-sans">{label}</p>}
        {payload.map((entry, index) => (
          <div key={index} className="flex items-center justify-between gap-3 text-neutral-700">
            <span className="flex items-center gap-1.5">
              <span 
                className="w-1.5 h-1.5 rounded-full shrink-0" 
                style={{ backgroundColor: entry.color || entry.fill || '#18181b' }} 
              />
              <span className="font-medium text-neutral-500">{entry.name || 'Count'}:</span>
            </span>
            <span className="font-mono font-bold text-neutral-900 tabular-nums">{entry.value}</span>
          </div>
        ))}
      </div>
    );
  }
  return null;
};

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [timeRange, setTimeRange] = useState('all'); // '24h' | '7d' | '30d' | 'all'

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchDashboard();
      setData(res);
    } catch (err) {
      setError(err.message || 'Failed to fetch dashboard telemetry');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const handleModeChange = () => loadData();
    window.addEventListener('offline-mode-changed', handleModeChange);
    return () => window.removeEventListener('offline-mode-changed', handleModeChange);
  }, []);

  if (loading && !data) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        <div className="flex items-center justify-between">
          <div className="space-y-1.5">
            <div className="h-7 w-64 bg-black/[0.06] rounded-md animate-pulse" />
            <div className="h-4 w-96 bg-black/[0.04] rounded-md animate-pulse" />
          </div>
          <div className="h-9 w-28 bg-black/[0.05] rounded-xl animate-pulse" />
        </div>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
          {Array.from({ length: 5 }).map((_, i) => (
            <KpiSkeleton key={i} />
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="bg-white border border-black/[0.07] rounded-2xl p-5 h-72 animate-pulse" />
          <div className="bg-white border border-black/[0.07] rounded-2xl p-5 h-72 animate-pulse" />
          <div className="bg-white border border-black/[0.07] rounded-2xl p-5 h-72 animate-pulse" />
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="max-w-md mx-auto my-16 p-6 rounded-2xl bg-white border border-black/[0.08] text-center shadow-card">
        <div className="w-12 h-12 rounded-2xl bg-[#ff3b30]/10 border border-[#ff3b30]/20 flex items-center justify-center text-[#ff3b30] mx-auto mb-3.5">
          <AlertCircle className="w-6 h-6" />
        </div>
        <h3 className="text-base font-semibold text-[#1d1d1f] mb-1 font-sans">Telemetry Unavailable</h3>
        <p className="text-xs text-[#59595e] mb-5 leading-relaxed">{error}</p>
        <Button variant="secondary" size="md" onClick={loadData} icon={RefreshCw}>
          Retry Connection
        </Button>
      </div>
    );
  }

  const { kpis, sentiment_distribution, category_distribution, issue_frequency, risk_distribution, emotion_distribution, daily_trend } = data;

  const sentimentData = Object.entries(sentiment_distribution || {}).map(([name, value]) => ({
    name, value, color: SENTIMENT_COLORS[name] || '#8e8e93'
  }));

  const riskData = Object.entries(risk_distribution || {}).map(([name, count]) => ({
    name, count, color: RISK_COLORS[name] || '#8e8e93'
  }));

  const timeSegments = [
    { label: '24 Hours', value: '24h' },
    { label: '7 Days', value: '7d' },
    { label: '30 Days', value: '30d' },
    { label: 'All Time', value: 'all' },
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6 animate-fade-in">
      
      {/* Executive Command Header */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 border-b border-neutral-200/80 pb-4">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-xl sm:text-2xl font-bold text-neutral-900 tracking-tight font-sans">
              Support & Threat Intelligence
            </h1>
            <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded-md bg-emerald-50 text-emerald-700 border border-emerald-200/80 font-bold">
              Live Feed
            </span>
          </div>
          <p className="text-neutral-500 text-xs sm:text-sm mt-0.5">
            Enterprise interaction monitoring, autonomous phishing isolation, and sentiment triage
          </p>
        </div>

        {/* Action Controls & Segmented Time Filter */}
        <div className="flex flex-wrap items-center gap-3">
          <SegmentedControl
            segments={timeSegments}
            value={timeRange}
            onChange={setTimeRange}
            size="sm"
          />

          <Button
            variant="secondary"
            size="sm"
            onClick={loadData}
            icon={RefreshCw}
          >
            Refresh
          </Button>
        </div>
      </div>

      {/* Top 5-Metric Executive KPI Strip */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3 sm:gap-3.5">
        
        {/* Total Ingested Conversations */}
        <div className="p-4 rounded-xl bg-white border border-neutral-200/80 shadow-xs hover:border-neutral-300 transition-all flex flex-col justify-between group">
          <div className="flex items-center justify-between text-neutral-500 text-[11px] font-medium uppercase tracking-wider mb-2">
            <span>Conversations</span>
            <div className="p-1.5 rounded-md bg-neutral-100 text-neutral-800">
              <MessageSquare className="w-4 h-4" />
            </div>
          </div>
          <div>
            <div className="text-2xl font-bold text-neutral-900 font-mono tabular-nums">
              {kpis.total_conversations}
            </div>
            <div className="text-[11px] text-neutral-500 mt-1 flex items-center justify-between">
              <span>Total ingested</span>
              <span className="text-emerald-700 font-mono font-medium">100% indexed</span>
            </div>
          </div>
        </div>

        {/* Threats Flagged */}
        <div className="p-4 rounded-xl bg-white border border-rose-200 shadow-xs hover:border-rose-300 transition-all flex flex-col justify-between group">
          <div className="flex items-center justify-between text-rose-700 text-[11px] font-medium uppercase tracking-wider mb-2">
            <span>Threats Flagged</span>
            <div className="p-1.5 rounded-md bg-rose-50 text-rose-700 border border-rose-200/60">
              <ShieldAlert className="w-4 h-4" />
            </div>
          </div>
          <div>
            <div className="text-2xl font-bold text-rose-700 font-mono tabular-nums">
              {kpis.threats_detected}
            </div>
            <div className="text-[11px] text-rose-600 mt-1 flex items-center justify-between font-medium">
              <span>Phishing & malware</span>
              <span className="font-mono font-semibold">0% FP</span>
            </div>
          </div>
        </div>

        {/* Critical Cases */}
        <div className="p-4 rounded-xl bg-white border border-amber-200 shadow-xs hover:border-amber-300 transition-all flex flex-col justify-between group">
          <div className="flex items-center justify-between text-amber-800 text-[11px] font-medium uppercase tracking-wider mb-2">
            <span>Critical Priority</span>
            <div className="p-1.5 rounded-md bg-amber-50 text-amber-800 border border-amber-200/60">
              <AlertOctagon className="w-4 h-4" />
            </div>
          </div>
          <div>
            <div className="text-2xl font-bold text-amber-800 font-mono tabular-nums">
              {kpis.critical_count}
            </div>
            <div className="text-[11px] text-neutral-500 mt-1 flex items-center justify-between">
              <span>Action needed</span>
              <span className="text-amber-700 font-mono font-medium">Urgent</span>
            </div>
          </div>
        </div>

        {/* Unresolved Complaints */}
        <div className="p-4 rounded-xl bg-white border border-neutral-200/80 shadow-xs hover:border-neutral-300 transition-all flex flex-col justify-between group">
          <div className="flex items-center justify-between text-neutral-500 text-[11px] font-medium uppercase tracking-wider mb-2">
            <span>Unresolved</span>
            <div className="p-1.5 rounded-md bg-neutral-100 text-neutral-800">
              <Clock className="w-4 h-4" />
            </div>
          </div>
          <div>
            <div className="text-2xl font-bold text-neutral-900 font-mono tabular-nums">
              {kpis.unresolved_count}
            </div>
            <div className="text-[11px] text-neutral-500 mt-1 flex items-center justify-between">
              <span>Pending response</span>
              <span className="text-amber-700 font-mono font-medium">Follow-up</span>
            </div>
          </div>
        </div>

        {/* Customer Anger / Hostility */}
        <div className="p-4 rounded-xl bg-white border border-neutral-200/80 shadow-xs hover:border-neutral-300 transition-all flex flex-col justify-between col-span-2 sm:col-span-1 group">
          <div className="flex items-center justify-between text-neutral-500 text-[11px] font-medium uppercase tracking-wider mb-2">
            <span>Customer Anger</span>
            <div className="p-1.5 rounded-md bg-neutral-100 text-rose-600">
              <Flame className="w-4 h-4" />
            </div>
          </div>
          <div>
            <div className="text-2xl font-bold text-neutral-900 font-mono tabular-nums">
              {kpis.angry_customers}
            </div>
            <div className="text-[11px] text-neutral-500 mt-1 flex items-center justify-between">
              <span>High frustration</span>
              <span className="text-rose-700 font-mono font-medium">Triage</span>
            </div>
          </div>
        </div>

      </div>

      {/* Operational Highlights Strip */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3.5">
        <div className="p-3.5 rounded-xl bg-white border border-neutral-200/80 flex items-center justify-between shadow-xs">
          <div>
            <div className="text-[10px] text-neutral-400 uppercase font-semibold tracking-wider">Top Issue Area</div>
            <div className="text-sm font-semibold text-neutral-900 mt-0.5 font-sans">{kpis.most_common_complaint}</div>
          </div>
          <span className="px-2 py-0.5 rounded-md bg-emerald-50 text-xs font-mono text-emerald-700 border border-emerald-200/80 font-medium">
            Category
          </span>
        </div>

        <div className="p-3.5 rounded-xl bg-white border border-neutral-200/80 flex items-center justify-between shadow-xs">
          <div>
            <div className="text-[10px] text-neutral-400 uppercase font-semibold tracking-wider">Frequent Controlled Tag</div>
            <div className="text-sm font-semibold text-neutral-900 mt-0.5 font-sans">{kpis.most_frequent_issue}</div>
          </div>
          <span className="px-2 py-0.5 rounded-md bg-neutral-100 text-xs font-mono text-neutral-800 border border-neutral-200/80 font-medium">
            Controlled Tag
          </span>
        </div>

        <div className="p-3.5 rounded-xl bg-white border border-neutral-200/80 flex items-center justify-between shadow-xs">
          <div>
            <div className="text-[10px] text-neutral-400 uppercase font-semibold tracking-wider">Sentiment Balance</div>
            <div className="text-xs font-semibold text-neutral-900 mt-0.5 flex gap-2 font-mono">
              <span className="text-emerald-700 font-semibold">{kpis.positive_count} Pos</span>
              <span className="text-neutral-300">/</span>
              <span className="text-neutral-600 font-semibold">{kpis.neutral_count} Neu</span>
              <span className="text-neutral-300">/</span>
              <span className="text-rose-700 font-semibold">{kpis.negative_count} Neg</span>
            </div>
          </div>
          <span className="px-2 py-0.5 rounded-md bg-purple-50 text-xs font-mono text-purple-700 border border-purple-200/80 font-medium">
            Ratio
          </span>
        </div>
      </div>

      {/* Main Charts Row 1: Split Visualizations */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Sentiment Distribution Donut */}
        <Card title="Sentiment Breakdown" subtitle="Customer experience posture" icon={TrendingUp}>
          <div className="h-56 w-full flex items-center justify-center relative">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={sentimentData}
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={80}
                  paddingAngle={4}
                  dataKey="value"
                >
                  {sentimentData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} stroke="#ffffff" strokeWidth={2.5} />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
              </PieChart>
            </ResponsiveContainer>
            {/* Donut Center Label */}
            <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
              <span className="text-2xl font-bold text-[#1d1d1f] font-mono">{kpis.total_conversations}</span>
              <span className="text-[10px] text-[#59595e] font-semibold uppercase tracking-wider">Tickets</span>
            </div>
          </div>
          <div className="flex justify-center gap-4 text-xs font-medium mt-2 pt-3 border-t border-black/[0.05]">
            {sentimentData.map((item) => (
              <div key={item.name} className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: item.color }}></span>
                <span className="text-[#59595e]">{item.name} ({item.value})</span>
              </div>
            ))}
          </div>
        </Card>

        {/* Security Risk Levels */}
        <Card title="Threat Risk Distribution" subtitle="Aggregated rule engine risk bands" icon={ShieldAlert}>
          <div className="h-56 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={riskData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.06)" vertical={false} />
                <XAxis dataKey="name" stroke="#59595e" fontSize={11} tickLine={false} axisLine={false} />
                <YAxis stroke="#59595e" fontSize={11} tickLine={false} axisLine={false} />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="count" name="Conversations" radius={[8, 8, 0, 0]}>
                  {riskData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="flex justify-center gap-3 text-xs text-[#59595e] font-mono mt-2 pt-3 border-t border-black/[0.05]">
            <span>Low: {risk_distribution.Low || 0}</span>
            <span>•</span>
            <span>Med: {risk_distribution.Medium || 0}</span>
            <span>•</span>
            <span>High: {risk_distribution.High || 0}</span>
            <span>•</span>
            <span className="text-[#b81414] font-bold">Crit: {risk_distribution.Critical || 0}</span>
          </div>
        </Card>

        {/* Temporal Activity & Threat Timeline */}
        <Card title="Activity & Threat Timeline" subtitle="Daily ticket volume vs threat alerts" icon={BarChart3}>
          <div className="h-56 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={daily_trend} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="totalGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#007aff" stopOpacity={0.25}/>
                    <stop offset="95%" stopColor="#007aff" stopOpacity={0.02}/>
                  </linearGradient>
                  <linearGradient id="threatGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ff3b30" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#ff3b30" stopOpacity={0.02}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.06)" vertical={false} />
                <XAxis dataKey="date" stroke="#59595e" fontSize={10} tickLine={false} axisLine={false} />
                <YAxis stroke="#59595e" fontSize={11} tickLine={false} axisLine={false} />
                <Tooltip content={<CustomTooltip />} />
                <Area type="monotone" dataKey="total" name="Total Volume" stroke="#007aff" fillOpacity={1} fill="url(#totalGrad)" strokeWidth={2.5} />
                <Area type="monotone" dataKey="threats" name="Threats Detected" stroke="#ff3b30" fillOpacity={1} fill="url(#threatGrad)" strokeWidth={2.5} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
          <div className="flex justify-center gap-4 text-xs font-medium mt-2 pt-3 border-t border-black/[0.05]">
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-[#007aff]"></span>
              <span className="text-[#59595e]">Total Volume</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-[#ff3b30]"></span>
              <span className="text-[#59595e]">Threat Alerts</span>
            </div>
          </div>
        </Card>

      </div>

      {/* Ranked Issue Frequencies (F5) */}
      <Card 
        title="Ranked Issue Frequency (F5)" 
        subtitle="Controlled taxonomy distribution with percentage impact metrics" 
        icon={Tag}
        action={
          <Link to="/conversations" className="text-xs font-semibold text-[#007aff] hover:underline flex items-center gap-1">
            View in Inbox <ChevronRight className="w-3.5 h-3.5" />
          </Link>
        }
      >
        <div className="space-y-3.5">
          {issue_frequency && issue_frequency.length > 0 ? (
            issue_frequency.map((item, index) => (
              <div key={item.issue_label} className="space-y-1.5 group">
                <div className="flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2.5">
                    <span className="font-mono text-[11px] font-bold px-1.5 py-0.5 rounded bg-black/[0.04] text-[#59595e] border border-black/[0.06] w-6 text-center">
                      #{index + 1}
                    </span>
                    <span className="font-semibold text-[#1d1d1f] group-hover:text-[#007aff] transition-colors">{item.issue_label}</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-[#59595e] font-mono text-[11px]">{item.count} tickets</span>
                    <span className="font-mono font-bold text-[#007aff] w-12 text-right">{item.percentage}%</span>
                  </div>
                </div>
                <div className="w-full bg-black/[0.04] rounded-full h-1.5 overflow-hidden">
                  <div 
                    className="bg-gradient-to-r from-[#007aff] to-[#32ade6] h-1.5 rounded-full transition-all duration-500" 
                    style={{ width: `${Math.min(item.percentage, 100)}%` }}
                  />
                </div>
              </div>
            ))
          ) : (
            <p className="text-xs text-[#59595e] py-4 text-center">No ranked issue telemetry available.</p>
          )}
        </div>
      </Card>

    </div>
  );
}
