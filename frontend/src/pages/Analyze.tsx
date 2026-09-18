import React, { useState } from 'react';
import {
  ShieldCheck,
  ShieldAlert,
  Sparkles,
  Link as LinkIcon,
  AlertOctagon,
} from 'lucide-react';
import { api } from '../api/client';
import { AnalysisRequest, AnalysisResult } from '../types/analysis';
import { RiskBadge } from '../components/RiskBadge';

const SAMPLE_PRESETS = [
  {
    label: 'Credential Phishing (IP URL)',
    sender: 'security-alert@micros0ft-support.xyz',
    subject: 'Urgent: Your Microsoft 365 Account will be terminated',
    message:
      'We detected unauthorized login attempts from a remote IP. Your account will be locked within 24 hours unless you verify your identity now.',
    urls: ['http://192.168.1.100/verify-login'],
  },
  {
    label: 'Brand Spoofing (Free-mail)',
    sender: 'PayPal Support <service392@gmail.com>',
    subject: 'Account Suspension Warning: Immediate Action Required',
    message:
      'Dear Customer, we have restricted your PayPal account due to suspicious transactions. Click the link to update your billing information.',
    urls: ['https://bit.ly/secure-paypal-update'],
  },
  {
    label: 'Clean Business Meeting',
    sender: 'sarah.connor@cyberdyne-systems.com',
    subject: 'Q3 Product Roadmap Review & Sync',
    message:
      'Hi team, please find the updated roadmap slides for our discussion this Thursday at 2:00 PM EST. Let me know if you need any agenda items added.',
    urls: ['https://cyberdyne-systems.com/docs/q3-roadmap'],
  },
];

interface AnalyzeProps {
  onAnalysisComplete?: () => void;
}

export const Analyze: React.FC<AnalyzeProps> = ({ onAnalysisComplete }) => {
  const [sender, setSender] = useState<string>('');
  const [subject, setSubject] = useState<string>('');
  const [message, setMessage] = useState<string>('');
  const [urlsInput, setUrlsInput] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AnalysisResult | null>(null);

  const handleApplyPreset = (preset: (typeof SAMPLE_PRESETS)[0]) => {
    setSender(preset.sender);
    setSubject(preset.subject);
    setMessage(preset.message);
    setUrlsInput(preset.urls.join('\n'));
    setResult(null);
    setError(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!sender.trim() || !message.trim()) {
      setError('Please provide at least a sender and message content.');
      return;
    }

    setLoading(true);
    setError(null);

    const urls = urlsInput
      .split(/[\n,]+/)
      .map((u) => u.trim())
      .filter((u) => u.length > 0);

    const payload: AnalysisRequest = {
      sender: sender.trim(),
      subject: subject.trim(),
      message: message.trim(),
      urls,
    };

    try {
      const data = await api.analyze(payload);
      setResult(data);
      if (onAnalysisComplete) {
        onAnalysisComplete();
      }
    } catch (err: any) {
      setError(err.message || 'Failed to analyze communication. Ensure backend is running.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      <div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
          Analyze Email or Message
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Inspect suspicious communications through rule-based domain/URL heuristics and Gemini threat analysis
        </p>
      </div>

      {/* Preset Buttons */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
        <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 block mb-2">
          Load Quick Test Sample:
        </span>
        <div className="flex flex-wrap gap-2">
          {SAMPLE_PRESETS.map((p, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => handleApplyPreset(p)}
              className="rounded-lg border border-slate-700 bg-slate-800/80 px-3 py-1.5 text-xs font-medium text-slate-300 hover:bg-slate-700 hover:text-white transition"
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {/* Submission Form */}
      <form onSubmit={handleSubmit} className="rounded-xl border border-slate-800 bg-slate-900/60 p-6 shadow-xl space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1">
              Sender Address <span className="text-rose-400">*</span>
            </label>
            <input
              type="text"
              required
              value={sender}
              onChange={(e) => setSender(e.target.value)}
              placeholder="e.g. security-update@paypal-verify.com or John <john@gmail.com>"
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3.5 py-2 text-sm text-white placeholder-slate-500 focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500 font-mono"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1">
              Subject Line
            </label>
            <input
              type="text"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              placeholder="e.g. Action Required: Account Suspension Notice"
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3.5 py-2 text-sm text-white placeholder-slate-500 focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500"
            />
          </div>
        </div>

        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1">
            Message Body <span className="text-rose-400">*</span>
          </label>
          <textarea
            required
            rows={5}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Paste full email/message content here..."
            className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3.5 py-2.5 text-sm text-white placeholder-slate-500 focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500 font-mono"
          />
        </div>

        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1 flex items-center gap-1.5">
            <LinkIcon className="h-3.5 w-3.5 text-sky-400" />
            Extracted URLs (optional, one per line)
          </label>
          <textarea
            rows={2}
            value={urlsInput}
            onChange={(e) => setUrlsInput(e.target.value)}
            placeholder="http://192.168.1.100/login&#10;https://bit.ly/update-now"
            className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3.5 py-2 text-xs text-white placeholder-slate-500 focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500 font-mono"
          />
        </div>

        {error && (
          <div className="rounded-lg bg-rose-950/60 border border-rose-800 p-3 text-sm text-rose-300 flex items-center gap-2">
            <AlertOctagon className="h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <div className="pt-2 flex justify-end">
          <button
            type="submit"
            disabled={loading}
            className="inline-flex items-center gap-2 rounded-lg bg-sky-600 px-6 py-2.5 text-sm font-semibold text-white shadow-lg hover:bg-sky-500 transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <>
                <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                Analyzing Security Signals...
              </>
            ) : (
              <>
                <Sparkles className="h-4 w-4" /> Analyze
              </>
            )}
          </button>
        </div>
      </form>

      {/* Analysis Result Display */}
      {result && (
        <div className="rounded-xl border border-slate-800 bg-slate-900/80 p-6 shadow-2xl space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-xl bg-slate-800 flex items-center justify-center border border-slate-700">
                {result.risk_level === 'Critical' || result.risk_level === 'High' ? (
                  <ShieldAlert className="h-6 w-6 text-rose-400" />
                ) : (
                  <ShieldCheck className="h-6 w-6 text-emerald-400" />
                )}
              </div>
              <div>
                <h3 className="text-lg font-bold text-white">Analysis Results</h3>
                <p className="text-xs text-slate-400">Validated against Locked Analysis Schema</p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <RiskBadge riskLevel={result.risk_level} size="lg" />
              <span className="rounded-lg bg-slate-800 px-3 py-1 text-xs font-semibold text-slate-200 border border-slate-700">
                {result.resolution_status}
              </span>
            </div>
          </div>

          {/* Summary Banner */}
          <div className="rounded-lg bg-slate-950 p-4 border border-slate-800">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 block mb-1">
              Executive Summary
            </span>
            <p className="text-sm text-slate-200 leading-relaxed">{result.summary}</p>
          </div>

          {/* Grid of Locked Schema Properties */}
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
            <div className="rounded-lg bg-slate-950/60 p-3 border border-slate-800/80">
              <span className="text-[10px] uppercase font-semibold text-slate-500 block">Category</span>
              <span className="text-sm font-bold text-white">{result.category}</span>
            </div>

            <div className="rounded-lg bg-slate-950/60 p-3 border border-slate-800/80">
              <span className="text-[10px] uppercase font-semibold text-slate-500 block">Threat Type</span>
              <span className="text-sm font-bold text-white">{result.threat_type}</span>
            </div>

            <div className="rounded-lg bg-slate-950/60 p-3 border border-slate-800/80">
              <span className="text-[10px] uppercase font-semibold text-slate-500 block">Priority</span>
              <span className="text-sm font-bold text-white">{result.priority}</span>
            </div>

            <div className="rounded-lg bg-slate-950/60 p-3 border border-slate-800/80">
              <span className="text-[10px] uppercase font-semibold text-slate-500 block">Sentiment</span>
              <span className="text-sm font-bold text-white">{result.sentiment}</span>
            </div>

            <div className="rounded-lg bg-slate-950/60 p-3 border border-slate-800/80">
              <span className="text-[10px] uppercase font-semibold text-slate-500 block">Target Emotion</span>
              <span className="text-sm font-bold text-white">{result.emotion}</span>
            </div>

            <div className="rounded-lg bg-slate-950/60 p-3 border border-slate-800/80">
              <span className="text-[10px] uppercase font-semibold text-slate-500 block">Social Engineering</span>
              <span className={`text-sm font-bold ${result.social_engineering ? 'text-rose-400' : 'text-emerald-400'}`}>
                {result.social_engineering ? 'TRUE' : 'FALSE'}
              </span>
            </div>

            <div className="rounded-lg bg-slate-950/60 p-3 border border-slate-800/80">
              <span className="text-[10px] uppercase font-semibold text-slate-500 block">Suspicious URL</span>
              <span className={`text-sm font-bold ${result.suspicious_url ? 'text-rose-400' : 'text-emerald-400'}`}>
                {result.suspicious_url ? 'TRUE' : 'FALSE'}
              </span>
            </div>

            <div className="rounded-lg bg-slate-950/60 p-3 border border-slate-800/80">
              <span className="text-[10px] uppercase font-semibold text-slate-500 block">Risk Level</span>
              <span className="text-sm font-bold text-white">{result.risk_level}</span>
            </div>
          </div>

          {/* Recommended Action Box */}
          <div className="rounded-lg bg-sky-950/30 border border-sky-900/60 p-4">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-sky-400 block mb-1">
              Recommended Security Action
            </span>
            <p className="text-sm text-sky-200 font-medium">{result.recommended_action}</p>
          </div>
        </div>
      )}
    </div>
  );
};
