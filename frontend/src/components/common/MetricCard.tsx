import React from 'react';
import { LucideIcon } from 'lucide-react';
import { SourceBadge } from './SourceBadge';

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: LucideIcon;
  sourceBadge?: string;
  onClick?: () => void;
  sparklineData?: number[];
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  sourceBadge,
  onClick,
  sparklineData,
}) => {
  return (
    <div
      onClick={onClick}
      className={`gov-card p-5 flex flex-col justify-between space-y-3 ${
        onClick ? 'cursor-pointer gov-card-hover' : ''
      }`}
    >
      {/* Top: Category Title + Line Icon */}
      <div className="flex items-center justify-between gap-2">
        <span className="text-[11px] font-sans font-bold uppercase tracking-wider text-[#667085]">
          {title}
        </span>
        {Icon && (
          <div className="p-1.5 rounded bg-[#F0F4F8] text-[#102A43]">
            <Icon className="w-4 h-4" />
          </div>
        )}
      </div>

      {/* Main Number */}
      <div className="space-y-1">
        <div className="text-2xl sm:text-3xl font-bold font-display text-[#172033] tracking-tight">
          {value}
        </div>
        {subtitle && (
          <p className="text-xs text-[#667085] leading-snug">
            {subtitle}
          </p>
        )}
      </div>

      {/* Footer Lineage & Sparkline */}
      <div className="pt-2 border-t border-[#E5E7EB] flex items-center justify-between">
        {sourceBadge ? (
          <SourceBadge type={sourceBadge} />
        ) : (
          <span className="text-[10px] font-mono text-[#98A2B3]">Verified Lineage</span>
        )}
        
        {sparklineData && sparklineData.length > 0 && (
          <div className="flex items-end gap-1 h-3.5">
            {sparklineData.map((val, idx) => (
              <span
                key={idx}
                className="w-1 bg-[#102A43]/40 rounded-xs"
                style={{ height: `${Math.max(20, Math.min(100, val))}%` }}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
