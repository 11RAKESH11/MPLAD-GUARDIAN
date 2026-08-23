import React from 'react';
import { RiskLevel } from '../../types';
import { getRiskBadgeClass } from '../../lib/utils';

interface RiskBadgeProps {
  level: RiskLevel;
  score?: number;
  size?: 'sm' | 'md' | 'lg';
  showScore?: boolean;
}

export const RiskBadge: React.FC<RiskBadgeProps> = ({
  level,
  score,
  size = 'md',
  showScore = true,
}) => {
  const sizeClasses = {
    sm: 'text-[10px] px-2 py-0.5',
    md: 'text-xs px-2.5 py-0.5',
    lg: 'text-sm px-3 py-1',
  }[size];

  const colorClass = getRiskBadgeClass(level);
  const label = level === 'LOW' ? 'Low Signal' : level === 'MEDIUM' ? 'Review Required' : level === 'HIGH' ? 'High Signal' : 'Critical Signal';

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded border font-sans tracking-tight ${colorClass} ${sizeClasses}`}
    >
      <span className="font-semibold">{label}</span>
      {showScore && score !== undefined && (
        <span className="font-mono text-[11px] opacity-85">
          ({Math.round(score)})
        </span>
      )}
    </span>
  );
};
