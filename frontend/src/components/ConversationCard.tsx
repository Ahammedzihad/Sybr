import React, { useState } from 'react';
import {
  ChevronDown,
  ChevronUp,
  Link as LinkIcon,
  ShieldAlert,
  ShieldCheck,
  Clock,
  Tag,
  Mail,
  Eye,
  EyeOff,
  User,
} from 'lucide-react';
import { ConversationRecord, formatSummaryText, normalizeConversation } from '../types/analysis';
import { RiskBadge } from './RiskBadge';

interface ConversationCardProps {
  conversation: ConversationRecord;
}

export const ConversationCard: React.FC<ConversationCardProps> = ({ conversation: rawConv }) => {
  const [expanded, setExpanded] = useState<boolean>(false);
  const [showMasked, setShowMasked] = useState<boolean>(true);

  const conv = normalizeConversation(rawConv);
  const analysis = conv.analysis!;

  const formatDate = (isoString?: string) => {
    if (!isoString) return 'Recent';
    try {
      const date = new Date(isoString);
      return date.toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return isoString;
    }
  };

  const displayText = showMasked
    ? (conv.masked_text || conv.raw_text || conv.message || '')
    : (conv.raw_text || conv.clean_text || conv.message || '');

  const summaryText = formatSummaryText(conv.summary || analysis.summary);

  const isStructuredSummary = typeof conv.summary === 'object' && conv.summary !== null;
  const structuredSummary = isStructuredSummary ? (conv.summary as Record<string, any>) : null;

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 shadow-lg transition duration-150 hover:border-slate-700">
      {/* Header Row */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-1.5">
            <span className="font-mono text-xs font-bold text-sky-400 bg-sky-950/80 px-2 py-0.5 rounded border border-sky-800/60">
              {conv.conversation_id}
            </span>
            <RiskBadge riskLevel={conv.risk_level || analysis.risk_level} size="sm" />
            <span className="rounded bg-slate-800 px-2 py-0.5 text-xs font-medium text-slate-300 border border-slate-700">
              {conv.category || analysis.category}
            </span>
            <span className="text-xs text-slate-400 flex items-center gap-1">
              <Clock className="h-3 w-3" />
              {formatDate(conv.created_at)}
            </span>
          </div>

          <h4 className="text-base font-bold text-white truncate">
            {conv.subject || '(No Subject Line)'}
          </h4>
          <p className="text-xs text-slate-400 truncate flex items-center gap-1 mt-0.5">
            <User className="h-3 w-3 text-slate-500" />
            <span className="text-slate-500">From:</span> {conv.sender || 'Customer'}
          </p>
        </div>

        <div className="flex items-center gap-2 self-end sm:self-center shrink-0">
          <span
            className={`text-xs font-medium px-2.5 py-1 rounded-full border ${
              conv.resolution_status?.toLowerCase() === 'resolved'
                ? 'bg-emerald-950/60 text-emerald-300 border-emerald-800/60'
                : conv.resolution_status?.toLowerCase() === 'unresolved'
                ? 'bg-rose-950/60 text-rose-300 border-rose-800/60'
                : 'bg-slate-800/80 text-slate-300 border-slate-700'
            }`}
          >
            {conv.resolution_status || 'Pending'}
          </span>
          <button
            type="button"
            onClick={() => setExpanded(!expanded)}
            className="flex items-center gap-1 rounded-lg border border-slate-700 bg-slate-800/80 px-3 py-1 text-xs font-medium text-slate-300 hover:bg-slate-700 hover:text-white transition"
          >
            {expanded ? (
              <>
                Less <ChevronUp className="h-3.5 w-3.5" />
              </>
            ) : (
              <>
                Details <ChevronDown className="h-3.5 w-3.5" />
              </>
            )}
          </button>
        </div>
      </div>

      {/* Summary Preview */}
      <div className="mt-3 text-xs sm:text-sm text-slate-300 line-clamp-2 bg-slate-950/40 p-2.5 rounded-lg border border-slate-800/60">
        <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider block mb-0.5">
          Summary:
        </span>
        {summaryText}
      </div>

      {/* Expandable Details Drawer */}
      {expanded && (
        <div className="mt-4 pt-4 border-t border-slate-800/80 space-y-4 text-xs">
          {/* Structured Summary Breakdown if available */}
          {structuredSummary && (
            <div className="rounded-lg bg-slate-950/80 p-3.5 border border-slate-800 space-y-1.5">
              <span className="font-semibold text-sky-400 uppercase tracking-wider text-[10px] block">
                Structured Analysis Summary
              </span>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                {structuredSummary.issue && (
                  <div>
                    <span className="text-slate-500 font-semibold block">Core Issue:</span>
                    <span className="text-slate-200">{structuredSummary.issue}</span>
                  </div>
                )}
                {structuredSummary.customer_request && (
                  <div>
                    <span className="text-slate-500 font-semibold block">Customer Request:</span>
                    <span className="text-slate-200">{structuredSummary.customer_request}</span>
                  </div>
                )}
                {structuredSummary.actions_taken && (
                  <div>
                    <span className="text-slate-500 font-semibold block">Actions Taken:</span>
                    <span className="text-slate-200">{structuredSummary.actions_taken}</span>
                  </div>
                )}
                {structuredSummary.current_status && (
                  <div>
                    <span className="text-slate-500 font-semibold block">Status:</span>
                    <span className="text-slate-200">{structuredSummary.current_status}</span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Message Content with PII Mask Toggle */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <h5 className="font-semibold text-slate-300 uppercase tracking-wider text-[11px]">
                Conversation Content
              </h5>
              {conv.masked_text && conv.masked_text !== conv.raw_text && (
                <button
                  type="button"
                  onClick={() => setShowMasked(!showMasked)}
                  className="flex items-center gap-1 text-[11px] text-sky-400 hover:text-sky-300 transition"
                >
                  {showMasked ? (
                    <>
                      <EyeOff className="h-3 w-3" /> PII Masked (Click for Raw)
                    </>
                  ) : (
                    <>
                      <Eye className="h-3 w-3" /> Raw Text (Click to Mask)
                    </>
                  )}
                </button>
              )}
            </div>
            <div className="rounded-lg bg-slate-950 p-3 text-slate-300 font-mono text-xs whitespace-pre-wrap border border-slate-800 max-h-48 overflow-y-auto leading-relaxed">
              {displayText || '(No text content)'}
            </div>
          </div>

          {/* Keywords & Indicator Tags */}
          {conv.keywords && conv.keywords.length > 0 && (
            <div>
              <h5 className="font-semibold text-slate-300 uppercase tracking-wider text-[11px] mb-1.5 flex items-center gap-1">
                <Tag className="h-3 w-3 text-sky-400" /> Extracted Keywords
              </h5>
              <div className="flex flex-wrap gap-1.5">
                {conv.keywords.map((kw, i) => (
                  <span
                    key={i}
                    className="rounded bg-slate-800 border border-slate-700 px-2 py-0.5 text-slate-300 font-mono text-[10px]"
                  >
                    #{kw}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Security Signals Grid (URLs, Email Spoofing, Threat Vectors) */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {/* URL Heuristics */}
            <div className="rounded-lg bg-slate-950/70 p-3 border border-slate-800/80">
              <h5 className="font-semibold text-slate-300 uppercase tracking-wider text-[11px] mb-1 flex items-center gap-1">
                <LinkIcon className="h-3 w-3 text-sky-400" /> URL Security Signals
              </h5>
              {conv.suspicious_url ? (
                <div className="space-y-1">
                  <div className="flex items-center gap-1.5 text-rose-400 font-semibold text-xs">
                    <ShieldAlert className="h-3.5 w-3.5 shrink-0" />
                    <span>Suspicious URL Flagged ({conv.url_risk || 'High'})</span>
                  </div>
                  {conv.url_reason && (
                    <p className="text-slate-400 text-[11px]">{conv.url_reason}</p>
                  )}
                  {conv.urls && conv.urls.length > 0 && (
                    <ul className="mt-1 space-y-1">
                      {conv.urls.map((u, i) => (
                        <li
                          key={i}
                          className="font-mono text-[10px] text-rose-300 bg-rose-950/40 p-1.5 rounded border border-rose-900/50 break-all"
                        >
                          {u}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              ) : (
                <div className="flex items-center gap-1.5 text-emerald-400 text-xs mt-1">
                  <ShieldCheck className="h-3.5 w-3.5" />
                  <span>No malicious URLs detected</span>
                </div>
              )}
            </div>

            {/* Email Heuristics */}
            <div className="rounded-lg bg-slate-950/70 p-3 border border-slate-800/80">
              <h5 className="font-semibold text-slate-300 uppercase tracking-wider text-[11px] mb-1 flex items-center gap-1">
                <Mail className="h-3 w-3 text-amber-400" /> Email Origin Analysis
              </h5>
              {conv.suspicious_email ? (
                <div className="space-y-1">
                  <div className="flex items-center gap-1.5 text-rose-400 font-semibold text-xs">
                    <ShieldAlert className="h-3.5 w-3.5 shrink-0" />
                    <span>Suspicious Email Flagged ({conv.email_risk || 'High'})</span>
                  </div>
                  {conv.email_reason && (
                    <p className="text-slate-400 text-[11px]">{conv.email_reason}</p>
                  )}
                </div>
              ) : (
                <div className="flex items-center gap-1.5 text-emerald-400 text-xs mt-1">
                  <ShieldCheck className="h-3.5 w-3.5" />
                  <span>Legitimate domain format verified</span>
                </div>
              )}
            </div>
          </div>

          {/* Threat Intelligence Breakdown */}
          <div className="rounded-lg bg-slate-950/90 p-3.5 border border-slate-800">
            <h5 className="font-semibold text-slate-300 uppercase tracking-wider text-[11px] mb-2.5">
              Gemini AI Threat Reasoning
            </h5>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 text-xs">
              <div>
                <span className="text-slate-500 block text-[10px] uppercase font-semibold">
                  Threat Type
                </span>
                <span className="font-bold text-white">{conv.threat_type || analysis.threat_type}</span>
              </div>
              <div>
                <span className="text-slate-500 block text-[10px] uppercase font-semibold">
                  Priority
                </span>
                <span className="font-bold text-white">{conv.priority || analysis.priority}</span>
              </div>
              <div>
                <span className="text-slate-500 block text-[10px] uppercase font-semibold">
                  Sentiment
                </span>
                <span className="font-bold text-white">{conv.sentiment || analysis.sentiment}</span>
              </div>
              <div>
                <span className="text-slate-500 block text-[10px] uppercase font-semibold">
                  Target Emotion
                </span>
                <span className="font-bold text-white">{conv.emotion || analysis.emotion || 'Neutral'}</span>
              </div>
            </div>

            {/* Social Engineering Techniques */}
            {conv.technique && conv.technique.length > 0 && (
              <div className="mt-2.5 pt-2 border-t border-slate-800/80 flex items-center gap-2 flex-wrap">
                <span className="text-rose-400 font-semibold text-[11px]">Coercion Tactics:</span>
                {conv.technique.map((tech, i) => (
                  <span
                    key={i}
                    className="rounded bg-rose-950/80 border border-rose-800/80 px-2 py-0.5 text-rose-300 font-mono text-[10px]"
                  >
                    {tech}
                  </span>
                ))}
              </div>
            )}

            {/* Recommended Action */}
            <div className="mt-3 pt-2.5 border-t border-slate-800/80">
              <span className="text-sky-400 font-semibold uppercase tracking-wider text-[10px] block mb-1">
                Recommended Action:
              </span>
              <p className="text-xs text-sky-200 font-medium bg-sky-950/40 p-2 rounded border border-sky-900/50">
                {conv.recommended_action || analysis.recommended_action}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
