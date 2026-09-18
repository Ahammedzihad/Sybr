import React, { useState } from 'react';
import {
  ShieldCheck,
  ShieldAlert,
  Sparkles,
  Link as LinkIcon,
  AlertOctagon,
  Mail,
  Lock,
  Eye,
  EyeOff,
} from 'lucide-react';
import { api } from '../api/client';
import { AnalysisRequest, AnalysisResult, formatSummaryText } from '../types/analysis';
import { RiskBadge } from '../components/RiskBadge';

const SAMPLE_PRESETS = [
  {
    label: 'Real: Duplicate Charge Refund (₹1,499)',
    sender: 'priya.sharma@gmail.com',
    subject: 'Charged ₹1,499 twice for premium subscription',
    message:
      'Hello support, I was charged ₹1,499 twice for my monthly premium plan on September 15th. Please issue a refund immediately. Sent from my iPhone',
    urls: [],
  },
  {
    label: 'Real: Account Lockout Inquiry',
    sender: 'john.doe@company.org',
    subject: 'Help! Dashboard account locked due to invalid attempts',
    message:
      'Help! I cannot access my dashboard. When I enter my email it says “Account locked due to multiple invalid attempts”. Previous ticket #8941 closed without fix.',
    urls: [],
  },
  {
    label: 'Real: French Package Delay',
    sender: 'pierre.dubois@free.fr',
    subject: 'Colis bloqué au centre de tri',
    message:
      "Bonjour, mon colis n'est pas encore arrivé. Le numéro de suivi indique qu'il est bloqué au centre de tri. Merci de vérifier.",
    urls: [],
  },
  {
    label: 'Threat: IP-Literal Credential Phishing',
    sender: 'security-alert@micros0ft-support.xyz',
    subject: 'Urgent: Your Microsoft 365 Account will be terminated',
    message:
      'We detected unauthorized login attempts from a remote IP. Your account will be locked within 24 hours unless you verify your identity now at our secure portal.',
    urls: ['http://192.168.1.100/verify-login'],
  },
  {
    label: 'Threat: PayPal Lookalike & Free-mail Spoof',
    sender: 'PayPal Billing <service-billing392@gmail.com>',
    subject: 'Account Suspension Warning: Immediate Action Required',
    message:
      'Dear Customer, we have restricted your PayPal account due to suspicious transactions. Click the link to update your billing information immediately.',
    urls: ['https://bit.ly/secure-paypal-update'],
  },
  {
    label: 'Threat: CEO Wire Transfer Coercion',
    sender: 'CEO Executive <exec-board-office@gmail.com>',
    subject: 'Confidential: Urgent wire payment required for acquisition',
    message:
      'Are you at your desk? I am currently in a board meeting and need an urgent wire transfer of $45,000 sent to vendor account before 3 PM. Reply immediately with confirmation.',
    urls: [],
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
  const [showMaskedToggle, setShowMaskedToggle] = useState<boolean>(false);

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
    if (!message.trim()) {
      setError('Please provide message content to analyze.');
      return;
    }

    setLoading(true);
    setError(null);

    const urls = urlsInput
      .split(/[\n,]+/)
      .map((u) => u.trim())
      .filter((u) => u.length > 0);

    const payload: AnalysisRequest = {
      sender: sender.trim() || 'Customer',
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
      setError(err.message || 'Failed to analyze communication. Ensure backend is running on port 8000.');
    } finally {
      setLoading(false);
    }
  };

  const summaryDisplay = result ? formatSummaryText(result.summary) : '';

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      {/* Page Title */}
      <div className="border-b border-slate-800/80 pb-5">
        <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
          Analyze Email or Support Message
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Inspect customer inquiries and suspicious messages through rule-based heuristics and Gemini threat analysis
        </p>
      </div>

      {/* Preset Test Scenarios */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
        <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 block mb-2.5">
          Load Quick Test Scenario (Real Tickets & Synthetic Threats):
        </span>
        <div className="flex flex-wrap gap-2">
          {SAMPLE_PRESETS.map((p, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => handleApplyPreset(p)}
              className={`rounded-lg border px-3 py-1.5 text-xs font-medium transition ${
                p.label.startsWith('Threat')
                  ? 'border-rose-900/60 bg-rose-950/40 text-rose-300 hover:bg-rose-900/60 hover:text-white'
                  : 'border-slate-700 bg-slate-800/80 text-slate-300 hover:bg-slate-700 hover:text-white'
              }`}
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
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5 flex items-center gap-1.5">
              <Mail className="h-3.5 w-3.5 text-slate-400" /> Sender Email or Display Name
            </label>
            <input
              type="text"
              value={sender}
              onChange={(e) => setSender(e.target.value)}
              placeholder="e.g. PayPal Support <service392@gmail.com> or customer@gmail.com"
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3.5 py-2 text-sm text-white placeholder-slate-500 focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500 font-mono"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5">
              Subject Line
            </label>
            <input
              type="text"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              placeholder="e.g. Account Suspension Notice or Refund Request"
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3.5 py-2 text-sm text-white placeholder-slate-500 focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500"
            />
          </div>
        </div>

        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5">
            Message Body <span className="text-rose-400">*</span>
          </label>
          <textarea
            required
            rows={5}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Paste customer support inquiry or suspicious email content..."
            className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3.5 py-2.5 text-sm text-white placeholder-slate-500 focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500 font-mono"
          />
        </div>

        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5 flex items-center gap-1.5">
            <LinkIcon className="h-3.5 w-3.5 text-sky-400" /> Extracted URLs (optional, one per line)
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
                Processing Security & AI Pipeline...
              </>
            ) : (
              <>
                <Sparkles className="h-4 w-4" /> Run Intelligence Analysis
              </>
            )}
          </button>
        </div>
      </form>

      {/* Analysis Result Display */}
      {result && (
        <div className="rounded-xl border border-slate-800 bg-slate-900/80 p-6 shadow-2xl space-y-6">
          {/* Header Verdict */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-xl bg-slate-800 flex items-center justify-center border border-slate-700">
                {result.risk_level === 'Critical' || result.risk_level === 'High' ? (
                  <ShieldAlert className="h-6 w-6 text-rose-400 animate-pulse" />
                ) : (
                  <ShieldCheck className="h-6 w-6 text-emerald-400" />
                )}
              </div>
              <div>
                <h3 className="text-lg font-bold text-white">Pipeline Verdict</h3>
                <p className="text-xs text-slate-400">Validated against Locked Schema Contract</p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <RiskBadge riskLevel={result.risk_level} size="lg" />
              <span className="rounded-lg bg-slate-800 px-3 py-1.5 text-xs font-semibold text-slate-200 border border-slate-700">
                {result.resolution_status}
              </span>
            </div>
          </div>

          {/* Executive Summary */}
          <div className="rounded-lg bg-slate-950 p-4 border border-slate-800">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 block mb-1">
              Executive Summary
            </span>
            <p className="text-sm text-slate-200 leading-relaxed font-sans">{summaryDisplay}</p>
          </div>

          {/* Core Properties Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
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
              <span className="text-sm font-bold text-white">{result.emotion || 'Neutral'}</span>
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
                {result.suspicious_url ? 'FLAGGED' : 'CLEAN'}
              </span>
            </div>

            <div className="rounded-lg bg-slate-950/60 p-3 border border-slate-800/80">
              <span className="text-[10px] uppercase font-semibold text-slate-500 block">Suspicious Email</span>
              <span className={`text-sm font-bold ${result.suspicious_email ? 'text-rose-400' : 'text-emerald-400'}`}>
                {result.suspicious_email ? 'FLAGGED' : 'CLEAN'}
              </span>
            </div>
          </div>

          {/* Rule Heuristics Breakdown */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* URL Heuristic Card */}
            <div className="rounded-lg bg-slate-950/70 p-4 border border-slate-800">
              <span className="text-[10px] uppercase font-semibold text-slate-500 block mb-1 flex items-center gap-1">
                <LinkIcon className="h-3 w-3 text-sky-400" /> URL Rule Analysis
              </span>
              <div className="flex items-center gap-2 mt-1">
                <span className={`font-semibold text-xs ${result.suspicious_url ? 'text-rose-400' : 'text-emerald-400'}`}>
                  {result.suspicious_url ? `Flagged (${result.url_risk || 'High'})` : 'No Malicious URL Detected'}
                </span>
              </div>
              {result.url_reason && (
                <p className="mt-1.5 text-xs text-slate-400 font-mono bg-slate-900/80 p-2 rounded border border-slate-800">
                  {result.url_reason}
                </p>
              )}
            </div>

            {/* Email Heuristic Card */}
            <div className="rounded-lg bg-slate-950/70 p-4 border border-slate-800">
              <span className="text-[10px] uppercase font-semibold text-slate-500 block mb-1 flex items-center gap-1">
                <Mail className="h-3 w-3 text-amber-400" /> Email Rule Analysis
              </span>
              <div className="flex items-center gap-2 mt-1">
                <span className={`font-semibold text-xs ${result.suspicious_email ? 'text-rose-400' : 'text-emerald-400'}`}>
                  {result.suspicious_email ? `Flagged (${result.email_risk || 'High'})` : 'Clean Sender Domain'}
                </span>
              </div>
              {result.email_reason && (
                <p className="mt-1.5 text-xs text-slate-400 font-mono bg-slate-900/80 p-2 rounded border border-slate-800">
                  {result.email_reason}
                </p>
              )}
            </div>
          </div>

          {/* Coercion Tactics if any */}
          {result.technique && result.technique.length > 0 && (
            <div className="flex items-center gap-2 flex-wrap bg-rose-950/20 p-3 rounded-lg border border-rose-900/40">
              <span className="text-xs font-semibold text-rose-400">Detected Coercion Tactics:</span>
              {result.technique.map((tech, i) => (
                <span
                  key={i}
                  className="rounded bg-rose-950/80 border border-rose-800/80 px-2.5 py-0.5 text-rose-300 font-mono text-xs font-medium"
                >
                  {tech}
                </span>
              ))}
            </div>
          )}

          {/* Recommended Action */}
          <div className="rounded-lg bg-sky-950/30 border border-sky-900/60 p-4">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-sky-400 block mb-1">
              Recommended Security & SOC Action
            </span>
            <p className="text-sm text-sky-200 font-medium">{result.recommended_action}</p>
          </div>

          {/* PII Masking Transparency Section */}
          {(result.masked_text || result.clean_text) && (
            <div className="rounded-lg bg-slate-950 p-4 border border-slate-800">
              <div className="flex items-center justify-between mb-2">
                <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                  <Lock className="h-3.5 w-3.5 text-emerald-400" /> PII Masking & Preprocessing Trace
                </span>
                <button
                  type="button"
                  onClick={() => setShowMaskedToggle(!showMaskedToggle)}
                  className="text-xs text-sky-400 hover:text-sky-300 flex items-center gap-1 transition"
                >
                  {showMaskedToggle ? (
                    <>
                      <EyeOff className="h-3 w-3" /> Show Preprocessed
                    </>
                  ) : (
                    <>
                      <Eye className="h-3 w-3" /> Show Masked PII
                    </>
                  )}
                </button>
              </div>
              <div className="rounded bg-slate-900/90 p-3 font-mono text-xs text-slate-300 whitespace-pre-wrap border border-slate-800">
                {showMaskedToggle ? result.masked_text || 'PII Masking applied.' : result.clean_text || 'Text normalized.'}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
