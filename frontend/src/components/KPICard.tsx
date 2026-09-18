import React, { ReactNode } from 'react';

interface KPICardProps {
  title: string;
  value: number | string;
  subtitle?: string;
  icon: ReactNode;
  variant?: 'default' | 'danger' | 'success' | 'warning' | 'info';
}

export const KPICard: React.FC<KPICardProps> = ({
  title,
  value,
  subtitle,
  icon,
  variant = 'default',
}) => {
  const borderStyles = {
    default: 'border-slate-800 hover:border-slate-700',
    danger: 'border-rose-900/40 hover:border-rose-700/60 bg-rose-950/10',
    warning: 'border-amber-900/40 hover:border-amber-700/60 bg-amber-950/10',
    success: 'border-emerald-900/40 hover:border-emerald-700/60 bg-emerald-950/10',
    info: 'border-sky-900/40 hover:border-sky-700/60 bg-sky-950/10',
  }[variant];

  return (
    <div
      className={`relative overflow-hidden rounded-xl border p-5 bg-slate-900/60 backdrop-blur-md shadow-lg transition-all duration-200 ${borderStyles}`}
    >
      <div className="flex items-center justify-between">
        <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">
          {title}
        </p>
        <div className="rounded-lg bg-slate-800/80 p-2.5 text-slate-300 border border-slate-700/50">
          {icon}
        </div>
      </div>
      <div className="mt-3">
        <h3 className="text-3xl font-extrabold tracking-tight text-white">{value}</h3>
        {subtitle && (
          <p className="mt-1 text-xs text-slate-400 font-medium">{subtitle}</p>
        )}
      </div>
    </div>
  );
};
