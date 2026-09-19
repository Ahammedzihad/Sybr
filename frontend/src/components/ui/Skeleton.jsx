import React from 'react';

export function Skeleton({ className = '', ...props }) {
  return (
    <div
      className={`bg-black/[0.06] rounded-md animate-pulse ${className}`}
      {...props}
    />
  );
}

export function KpiSkeleton() {
  return (
    <div className="bg-white border border-black/[0.07] rounded-2xl p-4 shadow-card space-y-3">
      <div className="flex items-center justify-between">
        <Skeleton className="h-3 w-24" />
        <Skeleton className="h-4 w-4 rounded-full" />
      </div>
      <Skeleton className="h-8 w-16" />
      <Skeleton className="h-2.5 w-32" />
    </div>
  );
}

export function TableRowSkeleton({ cols = 6 }) {
  return (
    <tr className="border-b border-black/[0.04]">
      {Array.from({ length: cols }).map((_, i) => (
        <td key={i} className="py-3.5 px-4">
          <Skeleton className={`h-4 ${i === 0 ? 'w-20' : i === 2 ? 'w-3/4' : 'w-16'}`} />
        </td>
      ))}
    </tr>
  );
}
