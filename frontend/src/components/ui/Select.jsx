import React from 'react';
import { ChevronDown } from 'lucide-react';

export default function Select({
  label,
  error,
  options = [],
  children,
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
        <select
          className={`w-full min-h-[34px] appearance-none bg-white text-neutral-900 text-xs rounded-lg border border-neutral-200 hover:border-neutral-300 focus:border-neutral-900 focus:ring-1 focus:ring-neutral-900 transition-all duration-150 py-1.5 pl-3 pr-8 cursor-pointer shadow-xs outline-none ${
            error ? 'border-rose-400 focus:border-rose-500' : ''
          } ${className}`}
          {...props}
        >
          {options.length > 0
            ? options.map((opt) => (
                <option key={opt.value} value={opt.value} className="bg-white text-neutral-900">
                  {opt.label}
                </option>
              ))
            : children}
        </select>
        <div className="absolute right-2.5 text-neutral-400 pointer-events-none flex items-center">
          <ChevronDown className="w-3.5 h-3.5" />
        </div>
      </div>
      {error && (
        <span className="text-xs text-rose-600 font-medium">{error}</span>
      )}
    </div>
  );
}
