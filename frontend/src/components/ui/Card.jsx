import React from 'react';

/**
 * Apple HIG Standard Material Card
 * Grounded in Apple's materials.md (Content layer standard materials)
 */
export default function Card({
  children,
  title,
  subtitle,
  action,
  icon: Icon,
  hoverable = false,
  className = '',
  headerClassName = '',
  bodyClassName = '',
  ...props
}) {
  return (
    <div
      className={`bg-white border border-neutral-200/80 rounded-xl shadow-xs transition-all duration-150 ${
        hoverable ? 'hover:border-neutral-300 hover:shadow-sm' : ''
      } ${className}`}
      {...props}
    >
      {(title || subtitle || action || Icon) && (
        <div className={`px-5 py-3.5 border-b border-neutral-100 flex items-center justify-between gap-3 ${headerClassName}`}>
          <div className="flex items-center gap-2.5 min-w-0">
            {Icon && (
              <div className="p-1.5 rounded-lg bg-neutral-100 border border-neutral-200/60 text-neutral-800 shrink-0">
                <Icon className="w-4 h-4" />
              </div>
            )}
            <div className="min-w-0">
              {title && (
                <h3 className="text-sm font-semibold text-neutral-900 tracking-tight truncate font-sans">
                  {title}
                </h3>
              )}
              {subtitle && (
                <p className="text-xs text-neutral-500 truncate mt-0.5 font-sans">
                  {subtitle}
                </p>
              )}
            </div>
          </div>
          {action && <div className="shrink-0">{action}</div>}
        </div>
      )}
      <div className={`p-5 ${bodyClassName}`}>{children}</div>
    </div>
  );
}
