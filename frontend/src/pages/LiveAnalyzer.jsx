import React, { useState } from 'react';
import { 
  Zap, 
  Send, 
  ShieldAlert, 
  ShieldCheck, 
  FileText, 
  AlertTriangle, 
  RefreshCw,
  Sparkles,
  Info,
  Globe,
  Mail,
  Paperclip
} from 'lucide-react';
import { analyzeLive } from '../api';
import { PriorityBadge, RiskBadge, SentimentBadge, EmotionBadge, ResolutionBadge } from '../components/Badges';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import Select from '../components/ui/Select';
import Input from '../components/ui/Input';

const DEMO_PRESETS = [
  {
    title: "1. Phishing (OTP + Lookalike)",
    text: "URGENT SECURITY ALERT! Your account has been compromised. Visit http://paypa1-security.example/login immediately and enter your password and 6-digit OTP code to prevent account suspension.",
    channel: "email",
    attachments: "",
  },
  {
    title: "2. Legitimate Complaint",
    text: "Hello, my card was charged twice ($45 each) for order #99210. Please look into this and process an immediate refund for the duplicate transaction.",
    channel: "chat",
    attachments: "",
  },
  {
    title: "3. Remote Access Scam",
    text: "This is IT Support. We detected a Trojan virus spreading on your workstation. Install AnyDesk immediately and provide your 9-digit remote access code. Do not disclose this to your supervisor.",
    channel: "chat",
    attachments: "",
  },
  {
    title: "4. Fake Invoice Attachment",
    text: "Dear accounts team, please find attached the updated supplier invoice for March 2026. Please process remittance today.",
    channel: "email",
    attachments: "invoice_march2026.pdf.exe",
  },
];

export default function LiveAnalyzer() {
  const [text, setText] = useState(DEMO_PRESETS[0].text);
  const [channel, setChannel] = useState('email');
  const [attachments, setAttachments] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handlePreset = (p) => {
    setText(p.text);
    setChannel(p.channel);
    setAttachments(p.attachments);
  };

  const handleAnalyze = async (e) => {
    e.preventDefault();
    if (!text.trim()) return;

    setLoading(true);
    setError(null);
    try {
      const attList = attachments ? attachments.split(',').map(a => a.trim()).filter(Boolean) : [];
      const res = await analyzeLive({
        text,
        channel,
        attachments: attList,
      });
      setResult(res);
    } catch (err) {
      setError(err.message || 'Analysis failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6 animate-fade-in">
      
      {/* Header */}
      <div className="border-b border-neutral-200/80 pb-4">
        <h1 className="text-xl sm:text-2xl font-bold text-neutral-900 tracking-tight flex items-center gap-2.5 font-sans">
          <Zap className="w-5 h-5 text-neutral-900" />
          Live Interactive Threat & Support Analyzer
        </h1>
        <p className="text-neutral-500 text-xs sm:text-sm mt-0.5">
          Paste any message or select an attack simulation to run synchronous dual-layer intelligence
        </p>
      </div>

      {/* Preset Pills Bar */}
      <div className="space-y-2">
        <div className="text-[10px] font-semibold text-neutral-400 uppercase tracking-wider">
          Quick Demo Presets
        </div>
        <div className="flex flex-wrap gap-2">
          {DEMO_PRESETS.map((p, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => handlePreset(p)}
              className="px-3 py-1.5 rounded-lg text-xs font-medium bg-white border border-neutral-200/80 hover:border-neutral-300 hover:bg-neutral-50 text-neutral-800 transition shadow-xs text-left"
            >
              {p.title}
            </button>
          ))}
        </div>
      </div>

      {/* Main Input Form */}
      <Card title="Live Interaction Inspector" subtitle="Test customer messages against the security rule engine and Gemini AI">
        <form onSubmit={handleAnalyze} className="space-y-4">
          <div className="space-y-1.5">
            <div className="flex items-center justify-between text-xs text-neutral-500">
              <label className="font-medium text-neutral-700">Customer Support Message / Email Body</label>
              <span className="font-mono text-neutral-400">{text.length} characters</span>
            </div>
            <textarea
              rows={5}
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Paste raw support email, WhatsApp message, or ticket thread here..."
              className="w-full rounded-lg bg-white border border-neutral-200 p-3 text-xs text-neutral-900 placeholder:text-neutral-400 focus:border-neutral-900 focus:ring-1 focus:ring-neutral-900 transition-all font-sans leading-relaxed outline-none shadow-xs"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
            <Select
              label="Source Channel"
              value={channel}
              onChange={(e) => setChannel(e.target.value)}
            >
              <option value="email">Email</option>
              <option value="chat">Chat (Web / App)</option>
              <option value="ticket">Helpdesk Ticket</option>
              <option value="sms">SMS / WhatsApp</option>
              <option value="social">Social Media</option>
            </Select>

            <Input
              label="Attachment Filenames (Optional, comma-separated)"
              placeholder="e.g. invoice.pdf, update.exe"
              value={attachments}
              onChange={(e) => setAttachments(e.target.value)}
            />
          </div>

          <div className="flex items-center justify-between pt-2">
            <p className="text-[11px] text-neutral-500">
              PII is masked locally before any AI processing takes place.
            </p>
            <Button
              type="submit"
              variant="primary"
              size="sm"
              loading={loading}
              icon={Send}
            >
              Run Dual Analysis
            </Button>
          </div>
        </form>
      </Card>

      {/* Error Message */}
      {error && (
        <div className="p-4 rounded-2xl bg-[#ff3b30]/10 border border-[#ff3b30]/20 text-[#b81414] text-xs font-medium">
          {error}
        </div>
      )}

      {/* Analysis Results Display */}
      {result && (
        <div className="space-y-6 animate-fade-in">
          
          {/* Operational Banner */}
          <div className={`p-4 rounded-2xl border flex items-start gap-3.5 shadow-sm ${
            result.security?.threat_detected
              ? 'bg-[#ff3b30]/10 border-[#ff3b30]/25 text-[#b81414]'
              : 'bg-[#34c759]/10 border-[#34c759]/25 text-[#1b6d31]'
          }`}>
            {result.security?.threat_detected ? (
              <ShieldAlert className="w-5 h-5 text-[#b81414] shrink-0 mt-0.5" />
            ) : (
              <ShieldCheck className="w-5 h-5 text-[#1b6d31] shrink-0 mt-0.5" />
            )}
            <div className="flex-1">
              <div className="text-[11px] font-bold uppercase tracking-wider text-[#59595e] mb-0.5">
                Recommended Operational & Security Action
              </div>
              <div className="text-sm font-semibold text-[#1d1d1f]">
                {result.security?.recommended_action || "Standard customer support routing."}
              </div>
            </div>
          </div>

          {/* Results Side-by-Side */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            
            {/* Customer Support Findings */}
            <Card title="Customer Support Intelligence" subtitle="Classification & structured resolution">
              <div className="space-y-4">
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5">
                  <div className="p-2.5 rounded-xl bg-black/[0.02] border border-black/[0.05]">
                    <div className="text-[10px] text-[#59595e] mb-1 font-medium">Category</div>
                    <span className="text-xs font-semibold text-[#6e21a8]">{result.category}</span>
                  </div>
                  <div className="p-2.5 rounded-xl bg-black/[0.02] border border-black/[0.05]">
                    <div className="text-[10px] text-[#59595e] mb-1 font-medium">Issue Tag</div>
                    <span className="text-xs font-semibold text-[#007aff]">{result.issue_label}</span>
                  </div>
                  <div className="p-2.5 rounded-xl bg-black/[0.02] border border-black/[0.05]">
                    <div className="text-[10px] text-[#59595e] mb-1 font-medium">Priority</div>
                    <PriorityBadge level={result.priority} />
                  </div>
                  <div className="p-2.5 rounded-xl bg-black/[0.02] border border-black/[0.05]">
                    <div className="text-[10px] text-[#59595e] mb-1 font-medium">Sentiment</div>
                    <SentimentBadge sentiment={result.sentiment} />
                  </div>
                  <div className="p-2.5 rounded-xl bg-black/[0.02] border border-black/[0.05]">
                    <div className="text-[10px] text-[#59595e] mb-1 font-medium">Emotion</div>
                    <EmotionBadge emotion={result.emotion} intensity={result.emotion_intensity} />
                  </div>
                  <div className="p-2.5 rounded-xl bg-black/[0.02] border border-black/[0.05]">
                    <div className="text-[10px] text-[#59595e] mb-1 font-medium">Status</div>
                    <ResolutionBadge status={result.resolution_status} />
                  </div>
                </div>

                {/* 5-Point Summary */}
                <div className="p-3.5 rounded-xl bg-black/[0.02] border border-black/[0.06] space-y-2 text-xs">
                  <div className="font-bold text-[#1d1d1f]">5-Point Structured Summary</div>
                  <div className="space-y-1 text-[#3c3c43]">
                    <div><span className="font-semibold text-[#59595e]">Issue:</span> {result.summary?.issue}</div>
                    <div><span className="font-semibold text-[#59595e]">Request:</span> {result.summary?.customer_request}</div>
                    <div><span className="font-semibold text-[#59595e]">Actions:</span> {result.summary?.actions_taken}</div>
                    <div><span className="font-semibold text-[#59595e]">Status:</span> {result.summary?.current_status}</div>
                    <div><span className="font-semibold text-[#59595e]">Priority:</span> {result.summary?.priority}</div>
                  </div>
                </div>
              </div>
            </Card>

            {/* Cyber Threat Findings */}
            <Card title="Cyber Threat Intelligence" subtitle="Rule scoring & social engineering cues">
              <div className="space-y-4">
                {/* Score Gauge */}
                <div className="p-3.5 rounded-xl bg-black/[0.02] border border-black/[0.06] space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-[#1d1d1f]">Risk Score</span>
                    <span className="font-mono text-sm font-bold text-[#1d1d1f] tabular-nums">
                      {result.security?.rule_score} / 100
                    </span>
                  </div>
                  <div className="w-full bg-black/[0.06] rounded-full h-2 overflow-hidden">
                    <div
                      className={`h-2 rounded-full transition-all duration-500 ${
                        result.security?.risk_level === 'Critical'
                          ? 'bg-[#ff3b30]'
                          : result.security?.risk_level === 'High'
                          ? 'bg-[#ff9500]'
                          : result.security?.risk_level === 'Medium'
                          ? 'bg-[#ff9500]'
                          : 'bg-[#34c759]'
                      }`}
                      style={{ width: `${Math.min(result.security?.rule_score, 100)}%` }}
                    />
                  </div>
                </div>

                {/* Techniques */}
                <div>
                  <div className="text-[11px] font-bold text-[#59595e] uppercase tracking-wider mb-1.5">
                    Techniques & Threat Type
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    <span className="px-2.5 py-0.5 rounded-lg bg-black/[0.04] text-xs font-semibold text-[#1d1d1f] border border-black/[0.06]">
                      Type: {result.security?.threat_type || 'None'}
                    </span>
                    {result.security?.techniques && result.security?.techniques.length > 0 ? (
                      result.security.techniques.map((t, i) => (
                        <span key={i} className="px-2.5 py-0.5 rounded-lg bg-[#ff3b30]/12 text-xs font-bold text-[#b81414] border border-[#ff3b30]/25">
                          {t}
                        </span>
                      ))
                    ) : (
                      <span className="text-xs text-[#59595e]">No malicious techniques identified</span>
                    )}
                  </div>
                </div>

                {/* Reasons */}
                {result.security?.risk_reasons && result.security?.risk_reasons.length > 0 && (
                  <div className="p-3.5 rounded-xl bg-black/[0.02] border border-black/[0.06] space-y-1.5">
                    <div className="text-xs font-bold text-[#1d1d1f]">Explainable Reasons</div>
                    <ul className="space-y-1 text-xs text-[#3c3c43]">
                      {result.security.risk_reasons.map((r, i) => (
                        <li key={i} className="flex items-start gap-1.5">
                          <span className="text-[#b81414] leading-none">•</span>
                          <span>{r}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </Card>

          </div>

          {/* Raw JSON */}
          <Card title="Canonical Section 5 Output" subtitle="Production locked JSON contract">
            <pre className="p-4 rounded-xl bg-[#f5f5f7] border border-black/[0.08] text-[#1d1d1f] font-mono text-xs overflow-x-auto max-h-64 leading-relaxed">
              {JSON.stringify(result, null, 2)}
            </pre>
          </Card>

        </div>
      )}

    </div>
  );
}
