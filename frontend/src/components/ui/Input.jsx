import React from 'react';
import { X } from 'lucide-react';

export default function Input({
  label,
  error,
  icon: Icon,
  onClear,
  value,
  className = '',
  containerClassName = '',
  ...props
}) {
  return (
    <div className={`flex flex-col gap-1.5 ${containerClassName}`}>
      {label && (
        <label className="text-xs font-medium text-neutral-600 tracking-tight">
          {label}
        </label>
      )}
      <div className="relative flex items-center">
        {Icon && (
          <div className="absolute left-3 text-neutral-400 pointer-events-none flex items-center">
            <Icon className="w-4 h-4" />
          </div>
        )}
        <input
          value={value}
          className={`w-full min-h-[34px] bg-white text-neutral-900 placeholder:text-neutral-400 text-xs rounded-lg border border-neutral-200 hover:border-neutral-300 focus:border-neutral-900 focus:ring-1 focus:ring-neutral-900 transition-all duration-150 py-1.5 shadow-xs outline-none ${
            Icon ? 'pl-9' : 'pl-3'
          } ${onClear && value ? 'pr-8' : 'pr-3'} ${error ? 'border-rose-400 focus:border-rose-500 focus:ring-rose-500' : ''} ${className}`}
          {...props}
        />
        {onClear && value ? (
          <button
            type="button"
            onClick={onClear}
            className="absolute right-2.5 p-1 rounded-md text-neutral-400 hover:text-neutral-700 hover:bg-neutral-100 transition"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        ) : null}
      </div>
      {error && (
        <span className="text-xs text-rose-600 font-medium">{error}</span>
      )}
    </div>
  );
}
