import React, { useState } from 'react';
import { ChevronDown, ChevronUp, Link as LinkIcon, ShieldAlert, Clock } from 'lucide-react';
import { ConversationRecord } from '../types/analysis';
import { RiskBadge } from './RiskBadge';

interface ConversationCardProps {
  conversation: ConversationRecord;
}

export const ConversationCard: React.FC<ConversationCardProps> = ({ conversation }) => {
  const [expanded, setExpanded] = useState<boolean>(false);
  const { analysis } = conversation;

  const formatDate = (isoString: string) => {
    try {
      const date = new Date(isoString);
      return date.toLocaleString();
    } catch {
      return isoString;
    }
  };

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 shadow transition hover:border-slate-700">
      {/* Header Row */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <RiskBadge riskLevel={analysis.risk_level} size="sm" />
            <span className="rounded bg-slate-800 px-2 py-0.5 text-xs font-medium text-slate-300 border border-slate-700">
              {analysis.category}
            </span>
            <span className="text-xs text-slate-400 flex items-center gap-1">
              <Clock className="h-3 w-3" />
              {formatDate(conversation.created_at)}
            </span>
          </div>
          <h4 className="mt-2 text-base font-bold text-white truncate">
            {conversation.subject || '(No Subject)'}
          </h4>
          <p className="text-xs text-slate-400 truncate">
            <span className="text-slate-500">From:</span> {conversation.sender}
          </p>
        </div>

        <div className="flex items-center gap-2 self-end sm:self-center">
          <span className="text-xs font-medium px-2.5 py-1 rounded-full bg-slate-800/80 text-slate-300 border border-slate-700">
            {analysis.resolution_status}
          </span>
          <button
            onClick={() => setExpanded(!expanded)}
            className="flex items-center gap-1 rounded-lg border border-slate-700 px-2.5 py-1 text-xs font-medium text-slate-300 hover:bg-slate-800 transition"
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
      <p className="mt-3 text-xs sm:text-sm text-slate-300 line-clamp-2">
        {analysis.summary}
      </p>

      {/* Expandable Details */}
      {expanded && (
        <div className="mt-4 pt-4 border-t border-slate-800/80 space-y-4 text-xs">
          {/* Message Content */}
          <div>
            <h5 className="font-semibold text-slate-300 uppercase tracking-wider text-[11px] mb-1">
              Message Content
            </h5>
            <div className="rounded-lg bg-slate-950 p-3 text-slate-300 font-mono text-xs whitespace-pre-wrap border border-slate-800 max-h-40 overflow-y-auto">
              {conversation.message}
            </div>
          </div>

          {/* URLs & Security Indicators */}
          {(conversation.urls.length > 0 || (conversation.security_indicators && conversation.security_indicators.length > 0)) && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {conversation.urls.length > 0 && (
                <div>
                  <h5 className="font-semibold text-slate-300 uppercase tracking-wider text-[11px] mb-1 flex items-center gap-1">
                    <LinkIcon className="h-3 w-3 text-sky-400" /> Extracted URLs
                  </h5>
                  <ul className="space-y-1">
                    {conversation.urls.map((u, i) => (
                      <li key={i} className="text-sky-400 font-mono break-all bg-slate-950/60 p-1.5 rounded border border-slate-800/50">
                        {u}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {conversation.security_indicators && conversation.security_indicators.length > 0 && (
                <div>
                  <h5 className="font-semibold text-slate-300 uppercase tracking-wider text-[11px] mb-1 flex items-center gap-1">
                    <ShieldAlert className="h-3 w-3 text-amber-400" /> Rule Indicators
                  </h5>
                  <div className="flex flex-wrap gap-1">
                    {conversation.security_indicators.map((ind, i) => (
                      <span key={i} className="rounded bg-rose-950/60 border border-rose-800/60 px-2 py-0.5 text-rose-300 font-mono text-[10px]">
                        {ind}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Complete 11-field Locked Schema Analysis Table */}
          <div>
            <h5 className="font-semibold text-slate-300 uppercase tracking-wider text-[11px] mb-2">
              Full Threat Intelligence Breakdown
            </h5>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2 bg-slate-950/80 p-3 rounded-lg border border-slate-800">
              <div>
                <span className="text-slate-500 block text-[10px] uppercase">Threat Type</span>
                <span className="font-medium text-slate-200">{analysis.threat_type}</span>
              </div>
              <div>
                <span className="text-slate-500 block text-[10px] uppercase">Priority</span>
                <span className="font-medium text-slate-200">{analysis.priority}</span>
              </div>
              <div>
                <span className="text-slate-500 block text-[10px] uppercase">Sentiment</span>
                <span className="font-medium text-slate-200">{analysis.sentiment}</span>
              </div>
              <div>
                <span className="text-slate-500 block text-[10px] uppercase">Emotion</span>
                <span className="font-medium text-slate-200">{analysis.emotion}</span>
              </div>
              <div>
                <span className="text-slate-500 block text-[10px] uppercase">Social Engineering</span>
                <span className={analysis.social_engineering ? "text-rose-400 font-semibold" : "text-emerald-400"}>
                  {analysis.social_engineering ? "Detected" : "None"}
                </span>
              </div>
              <div>
                <span className="text-slate-500 block text-[10px] uppercase">Suspicious URL</span>
                <span className={analysis.suspicious_url ? "text-rose-400 font-semibold" : "text-emerald-400"}>
                  {analysis.suspicious_url ? "Flagged" : "None"}
                </span>
              </div>
              <div className="col-span-2 sm:col-span-3 md:col-span-2">
                <span className="text-slate-500 block text-[10px] uppercase">Recommended Action</span>
                <span className="text-slate-300 font-medium">{analysis.recommended_action}</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
