import React from 'react';

export const CardSkeleton: React.FC<{ count?: number }> = ({ count = 4 }) => (
  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
    {Array.from({ length: count }).map((_, i) => (
      <div key={i} className="civic-card p-5 animate-pulse space-y-3">
        <div className="h-3 bg-[#E1E5E1] rounded w-1/3" />
        <div className="h-7 bg-[#E1E5E1] rounded w-2/3" />
        <div className="h-3 bg-[#E1E5E1] rounded w-1/2 mt-2" />
      </div>
    ))}
  </div>
);

export const TableSkeleton: React.FC<{ rows?: number }> = ({ rows = 8 }) => (
  <div className="civic-card overflow-hidden animate-pulse">
    <div className="p-4 bg-[#F1F3F0] border-b border-[#E1E5E1] flex gap-4">
      <div className="h-4 bg-[#E1E5E1] rounded w-1/4" />
      <div className="h-4 bg-[#E1E5E1] rounded w-1/4" />
      <div className="h-4 bg-[#E1E5E1] rounded w-1/4" />
      <div className="h-4 bg-[#E1E5E1] rounded w-1/4" />
    </div>
    <div className="divide-y divide-[#E1E5E1] p-4 space-y-3">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="h-5 bg-[#F1F3F0] rounded w-full" />
      ))}
    </div>
  </div>
);
