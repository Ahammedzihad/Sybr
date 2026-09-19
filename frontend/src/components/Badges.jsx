import React from 'react';
import { ShieldAlert, ShieldCheck, CheckCircle2, AlertCircle, Clock } from 'lucide-react';

/**
 * Apple HIG Semantic Badges & Chips
 * Calibrated for strict WCAG AA contrast (≥ 4.5:1 for small text)
 */
export function PriorityBadge({ level, reason, showReason = false }) {
  const styles = {
    Low: 'bg-emerald-50 text-emerald-700 border-emerald-200/80',
    Medium: 'bg-amber-50 text-amber-800 border-amber-200/80',
    High: 'bg-orange-50 text-orange-800 border-orange-200/80 font-semibold',
    Critical: 'bg-rose-50 text-rose-800 border-rose-200/80 font-semibold',
  };
  const dotStyles = {
    Low: 'bg-emerald-500',
    Medium: 'bg-amber-500',
    High: 'bg-orange-500',
    Critical: 'bg-rose-500',
  };

  const style = styles[level] || styles.Low;
  const dot = dotStyles[level] || dotStyles.Low;

  return (
    <div className="inline-flex flex-col items-start">
      <span
        title={reason}
        className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-[11px] font-medium border ${style} transition-colors`}
      >
        <span className={`w-1.5 h-1.5 rounded-full ${dot}`}></span>
        {level}
      </span>
      {showReason && reason && (
        <span className="text-[11px] text-neutral-500 mt-1 max-w-xs leading-tight">{reason}</span>
      )}
    </div>
  );
}

export function RiskBadge({ level, reasons = [], showReasons = false }) {
  const styles = {
    Low: 'bg-emerald-50 text-emerald-700 border-emerald-200/80',
    Medium: 'bg-amber-50 text-amber-800 border-amber-200/80',
    High: 'bg-orange-50 text-orange-800 border-orange-200/80 font-semibold',
    Critical: 'bg-rose-50 text-rose-800 border-rose-200/80 font-semibold shadow-xs',
  };
  const style = styles[level] || styles.Low;

  return (
    <div className="inline-flex flex-col items-start">
      <span
        title={reasons.join('; ')}
        className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-[11px] font-medium border ${style}`}
      >
        {level === 'Critical' || level === 'High' ? (
          <ShieldAlert className="w-3.5 h-3.5 shrink-0 text-rose-600" />
        ) : (
          <ShieldCheck className="w-3.5 h-3.5 shrink-0 text-emerald-600" />
        )}
        {level} Risk
      </span>
      {showReasons && reasons && reasons.length > 0 && (
        <ul className="mt-1.5 space-y-1">
          {reasons.slice(0, 3).map((r, idx) => (
            <li key={idx} className="text-[11px] text-neutral-500 flex items-start gap-1.5 leading-tight">
              <span className="text-rose-500 text-xs leading-none">•</span> {r}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export function SentimentBadge({ sentiment }) {
  const styles = {
    Positive: 'bg-emerald-50 text-emerald-700 border-emerald-200/80 font-medium',
    Neutral: 'bg-neutral-100 text-neutral-700 border-neutral-200/80 font-medium',
    Negative: 'bg-rose-50 text-rose-800 border-rose-200/80 font-medium',
  };
  const style = styles[sentiment] || styles.Neutral;

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-md text-[11px] border ${style}`}>
      {sentiment}
    </span>
  );
}

export function EmotionBadge({ emotion, intensity = 1 }) {
  const styles = {
    Anger: 'bg-rose-50 text-rose-800 border-rose-200/80',
    Frustration: 'bg-amber-50 text-amber-800 border-amber-200/80',
    Satisfaction: 'bg-emerald-50 text-emerald-700 border-emerald-200/80',
    Confusion: 'bg-purple-50 text-purple-800 border-purple-200/80',
    Urgency: 'bg-amber-50 text-amber-800 border-amber-200/80',
    Fear: 'bg-indigo-50 text-indigo-800 border-indigo-200/80',
    Neutral: 'bg-neutral-100 text-neutral-700 border-neutral-200/80',
  };
  const style = styles[emotion] || styles.Neutral;

  return (
    <span
      title={`Intensity: ${intensity}/5`}
      className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-[11px] font-medium border ${style}`}
    >
      <span>{emotion}</span>
      <span className="text-[10px] opacity-75 font-mono font-medium">({intensity}/5)</span>
    </span>
  );
}

export function ResolutionBadge({ status, reason }) {
  if (status === 'Resolved') {
    return (
      <span title={reason} className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-medium bg-emerald-50 text-emerald-700 border border-emerald-200/80">
        <CheckCircle2 className="w-3 h-3 text-emerald-600" /> Resolved
      </span>
    );
  } else if (status === 'Unresolved') {
    return (
      <span title={reason} className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-medium bg-rose-50 text-rose-800 border border-rose-200/80 font-semibold">
        <AlertCircle className="w-3 h-3 text-rose-600" /> Unresolved
      </span>
    );
  }
  return (
    <span title={reason} className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-medium bg-amber-50 text-amber-800 border border-amber-200/80">
      <Clock className="w-3 h-3 text-amber-600" /> Pending
    </span>
  );
}

export function CategoryBadge({ category }) {
  return (
    <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[11px] font-medium bg-neutral-100 text-neutral-700 border border-neutral-200/80">
      {category || 'General Support'}
    </span>
  );
}

