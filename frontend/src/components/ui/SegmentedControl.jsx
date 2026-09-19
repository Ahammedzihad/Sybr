import React from 'react';

/**
 * Apple HIG Segmented Control
 * Grounded in Apple's segmented-controls.md
 * Features a recessed container with sliding physical pill highlight
 */
export default function SegmentedControl({
  segments = [],
  value,
  onChange,
  size = 'md',
  className = '',
}) {
  const sizeStyles = {
    sm: 'p-0.5 text-xs rounded-lg',
    md: 'p-1 text-xs sm:text-sm rounded-xl',
  };

  const segmentItemPadding = {
    sm: 'px-2.5 py-1',
    md: 'px-3.5 py-1.5',
  };

  return (
    <div
      role="radiogroup"
      className={`inline-flex items-center bg-neutral-100 border border-neutral-200/80 select-none ${sizeStyles[size] || sizeStyles.md} ${className}`}
    >
      {segments.map((seg) => {
        const segValue = typeof seg === 'object' ? seg.value : seg;
        const segLabel = typeof seg === 'object' ? seg.label : seg;
        const segIcon = typeof seg === 'object' && seg.icon ? seg.icon : null;
        const isSelected = value === segValue;
        const Icon = segIcon;

        return (
          <button
            key={segValue}
            type="button"
            role="radio"
            aria-checked={isSelected}
            onClick={() => onChange(segValue)}
            className={`
              relative flex items-center justify-center gap-1.5 font-medium transition-all duration-150 rounded-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-neutral-900
              ${segmentItemPadding[size] || segmentItemPadding.md}
              ${
                isSelected
                  ? 'bg-white text-neutral-900 font-semibold shadow-xs border border-neutral-200/60'
                  : 'text-neutral-500 hover:text-neutral-900 hover:bg-neutral-200/40'
              }
            `}
          >
            {Icon && <Icon className={`w-3.5 h-3.5 ${isSelected ? 'text-neutral-900' : 'text-neutral-400'}`} />}
            <span>{segLabel}</span>
          </button>
        );
      })}
    </div>
  );
}
