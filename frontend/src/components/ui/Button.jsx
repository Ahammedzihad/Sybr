import React from 'react';
import { Loader2 } from 'lucide-react';

/**
 * Apple HIG Button
 * Grounded in Apple's buttons.md and accessibility.md
 * Respects touch target sizes and clear interactive states
 */
export default function Button({
  children,
  variant = 'primary',
  size = 'md',
  loading = false,
  disabled = false,
  icon: Icon,
  className = '',
  ...props
}) {
  const baseStyles = "inline-flex items-center justify-center font-medium transition-all duration-150 select-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-neutral-900 focus-visible:ring-offset-2 active:scale-[0.98] disabled:opacity-40 disabled:pointer-events-none disabled:scale-100";

  const sizeStyles = {
    sm: "px-2.5 py-1 text-xs min-h-[30px] rounded-lg gap-1.5",
    md: "px-3.5 py-1.5 text-xs min-h-[34px] rounded-lg gap-2",
    lg: "px-4 py-2 text-sm min-h-[38px] rounded-lg gap-2",
  };

  const variantStyles = {
    primary: "bg-neutral-900 hover:bg-neutral-800 text-white font-medium shadow-xs border border-neutral-900 active:bg-neutral-950",
    secondary: "bg-white hover:bg-neutral-50 text-neutral-800 border border-neutral-200/80 shadow-xs hover:border-neutral-300",
    outline: "bg-transparent hover:bg-neutral-100 text-neutral-800 border border-neutral-200",
    ghost: "bg-transparent hover:bg-neutral-100 text-neutral-600 hover:text-neutral-900",
    danger: "bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 font-medium",
  };

  const finalClass = `${baseStyles} ${sizeStyles[size] || sizeStyles.md} ${variantStyles[variant] || variantStyles.primary} ${className}`;

  return (
    <button
      disabled={disabled || loading}
      className={finalClass}
      {...props}
    >
      {loading ? (
        <Loader2 className="w-4 h-4 animate-spin text-current" />
      ) : Icon ? (
        <Icon className="w-4 h-4 text-current shrink-0" />
      ) : null}
      {children}
    </button>
  );
}
