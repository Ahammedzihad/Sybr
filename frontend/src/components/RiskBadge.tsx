import React from 'react';

interface RiskBadgeProps {
  riskLevel: string;
  size?: 'sm' | 'md' | 'lg';
}

export const RiskBadge: React.FC<RiskBadgeProps> = ({ riskLevel, size = 'md' }) => {
  const normalized = (riskLevel || 'Unknown').toUpperCase();

  let colorClasses = 'bg-slate-800 text-slate-300 border-slate-700';

  if (normalized === 'CRITICAL') {
    colorClasses = 'bg-rose-950/80 text-rose-300 border-rose-700/60 ring-1 ring-rose-500/30';
  } else if (normalized === 'HIGH') {
    colorClasses = 'bg-amber-950/80 text-amber-300 border-amber-700/60 ring-1 ring-amber-500/30';
  } else if (normalized === 'MEDIUM') {
    colorClasses = 'bg-yellow-950/80 text-yellow-300 border-yellow-700/60';
  } else if (normalized === 'LOW') {
    colorClasses = 'bg-sky-950/80 text-sky-300 border-sky-700/60';
  } else if (normalized === 'SAFE' || normalized === 'CLEAN') {
    colorClasses = 'bg-emerald-950/80 text-emerald-300 border-emerald-700/60 ring-1 ring-emerald-500/30';
  }

  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5 font-medium',
    md: 'text-xs px-2.5 py-1 font-semibold tracking-wide',
    lg: 'text-sm px-3.5 py-1.5 font-bold tracking-wider',
  }[size];

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border shadow-sm ${sizeClasses} ${colorClasses}`}
    >
      <span
        className={`w-1.5 h-1.5 rounded-full ${
          normalized === 'CRITICAL'
            ? 'bg-rose-400 animate-pulse'
            : normalized === 'HIGH'
            ? 'bg-amber-400'
            : normalized === 'SAFE' || normalized === 'CLEAN'
            ? 'bg-emerald-400'
            : 'bg-current'
        }`}
      />
      {riskLevel}
    </span>
  );
};
