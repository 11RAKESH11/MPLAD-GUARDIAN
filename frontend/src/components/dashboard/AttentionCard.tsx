import React from 'react';
import { AlertCircle, ArrowRight, ShieldAlert, FileText, CheckCircle2 } from 'lucide-react';
import { AttentionItem } from '../../types';

interface AttentionCardProps {
  item: AttentionItem;
  onInvestigate: (workCode: string, alertId?: string) => void;
}

export const AttentionCard: React.FC<AttentionCardProps> = ({ item, onInvestigate }) => {
  const formatCurrency = (val: number | null | undefined) => {
    if (val === null || val === undefined || isNaN(Number(val)) || Number(val) === 0) return '₹0';
    const num = Number(val);
    if (num >= 10000000) return `₹${(num / 10000000).toFixed(2)} Cr`;
    if (num >= 100000) return `₹${(num / 100000).toFixed(1)} L`;
    return `₹${num.toLocaleString('en-IN')}`;
  };

  const getSeverityStyle = (severity: string) => {
    switch (severity?.toUpperCase()) {
      case 'CRITICAL':
        return {
          badge: 'bg-red-100 text-red-800 border-red-200',
          border: 'border-l-4 border-l-red-600',
          dot: 'bg-red-600'
        };
      case 'HIGH':
        return {
          badge: 'bg-amber-100 text-amber-900 border-amber-200',
          border: 'border-l-4 border-l-amber-500',
          dot: 'bg-amber-500'
        };
      case 'MEDIUM':
        return {
          badge: 'bg-blue-100 text-blue-800 border-blue-200',
          border: 'border-l-4 border-l-blue-500',
          dot: 'bg-blue-500'
        };
      default:
        return {
          badge: 'bg-gray-100 text-gray-800 border-gray-200',
          border: 'border-l-4 border-l-gray-400',
          dot: 'bg-gray-400'
        };
    }
  };

  const style = getSeverityStyle(item.severity);

  return (
    <div className={`gov-card p-5 flex flex-col justify-between space-y-4 bg-white ${style.border} hover:shadow-md transition-shadow`}>
      {/* Header: Signal Type + Severity Pill */}
      <div>
        <div className="flex items-center justify-between gap-2 mb-2">
          <div className="flex items-center gap-2">
            <span className={`w-2 h-2 rounded-full ${style.dot}`} />
            <span className="text-xs font-bold uppercase tracking-wider text-[#102A43]">
              {item.signal_type}
            </span>
          </div>
          <span className={`text-[11px] font-semibold px-2 py-0.5 rounded border uppercase ${style.badge}`}>
            {item.severity} PRIORITY
          </span>
        </div>

        {/* Location & Title */}
        <h4 className="text-sm font-bold text-[#172033] line-clamp-2 leading-snug">
          {item.title}
        </h4>
        <div className="text-xs text-[#667085] mt-1 flex items-center gap-2">
          <span className="font-semibold text-[#334E68]">{item.district}</span>
          <span>•</span>
          <span>{item.state}</span>
          {item.category && (
            <>
              <span>•</span>
              <span className="truncate max-w-[120px]">{item.category}</span>
            </>
          )}
        </div>
      </div>

      {/* Exposure & Evidence Strength */}
      <div className="p-2.5 rounded bg-[#F8FAFC] border border-[#E2E8F0] space-y-1.5 text-xs">
        <div className="flex items-center justify-between">
          <span className="text-[#64748B]">Financial Allocation:</span>
          <span className="font-mono font-bold text-[#102A43]">{formatCurrency(item.sanctioned_amount)}</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-[#64748B]">Evidence Strength:</span>
          <span className="font-semibold text-[#0F766E]">{item.confidence}% Model Confidence</span>
        </div>
        <p className="text-[11px] text-[#475569] leading-relaxed pt-1 border-t border-[#E2E8F0]">
          {item.why_prioritized}
        </p>
      </div>

      {/* Action Footer */}
      <div className="pt-2 flex items-center justify-between border-t border-[#F1F5F9]">
        <div className="text-[10px] font-mono text-[#94A3B8]">
          ID: {item.alert_id}
        </div>
        <button
          onClick={() => onInvestigate(item.work_code, item.alert_id)}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-bold bg-[#102A43] text-white hover:bg-[#1E3A8A] transition-colors focus:ring-2 focus:ring-[#102A43] focus:outline-none"
        >
          <span>Investigate</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
};
