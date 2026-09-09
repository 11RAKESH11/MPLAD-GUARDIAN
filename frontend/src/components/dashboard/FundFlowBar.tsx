import React, { useState } from 'react';
import { ChevronRight, Info, CheckCircle2, DollarSign, Send, FileCheck } from 'lucide-react';
import { FundFlowStage } from '../../types';
import { formatNumber } from '../../lib/utils';

interface FundFlowBarProps {
  stages: FundFlowStage[];
  totalSanctioned: number;
  totalExpenditure: number;
  utilizationRatePct: number;
}

export const FundFlowBar: React.FC<FundFlowBarProps> = ({
  stages,
  totalSanctioned,
  totalExpenditure,
  utilizationRatePct,
}) => {
  const [selectedStage, setSelectedStage] = useState<FundFlowStage | null>(null);

  const formatCr = (val: number | string | null | undefined) => {
    if (val === null || val === undefined || isNaN(Number(val)) || Number(val) === 0) return '₹0 Cr';
    const num = Number(val);
    return `₹${(num / 10000000).toLocaleString('en-IN', { maximumFractionDigits: 1 })} Cr`;
  };

  const getStageIcon = (id: string) => {
    switch (id) {
      case 'recommended':
        return <Send className="w-4 h-4 text-[#3B82F6]" />;
      case 'sanctioned':
        return <FileCheck className="w-4 h-4 text-[#102A43]" />;
      case 'disbursed':
        return <DollarSign className="w-4 h-4 text-[#0284C7]" />;
      case 'expenditure':
        return <CheckCircle2 className="w-4 h-4 text-[#059669]" />;
      default:
        return <Info className="w-4 h-4 text-[#64748B]" />;
    }
  };

  const getStageBg = (id: string) => {
    switch (id) {
      case 'recommended':
        return 'border-t-4 border-t-[#3B82F6]';
      case 'sanctioned':
        return 'border-t-4 border-t-[#102A43]';
      case 'disbursed':
        return 'border-t-4 border-t-[#0284C7]';
      case 'expenditure':
        return 'border-t-4 border-t-[#059669]';
      default:
        return 'border-t-4 border-t-slate-400';
    }
  };

  return (
    <div className="gov-card p-6 bg-white space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div>
          <h3 className="text-base font-bold text-[#102A43] flex items-center gap-2">
            <span>MPLADS Fund Flow Pipeline</span>
            <span className="text-xs font-normal text-[#64748B]">(Recommended → Sanctioned → Disbursed → Expenditure)</span>
          </h3>
          <p className="text-xs text-[#64748B] mt-0.5">
            Stage-wise financial progression across 96,654 canonical projects
          </p>
        </div>
        <div className="flex items-center gap-3 bg-[#F0FDF4] border border-[#DCFCE7] px-3 py-1.5 rounded text-xs">
          <span className="text-[#166534] font-medium">National Utilization:</span>
          <span className="font-mono font-bold text-[#15803D] text-sm">{utilizationRatePct}%</span>
        </div>
      </div>

      {/* 4-Stage Horizontal Pipeline */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-3 relative">
        {stages.map((stage, idx) => {
          const isSelected = selectedStage?.id === stage.id;
          return (
            <div
              key={stage.id}
              onClick={() => setSelectedStage(isSelected ? null : stage)}
              className={`p-4 rounded-lg bg-[#F8FAFC] border transition-all cursor-pointer relative ${getStageBg(
                stage.id
              )} ${
                isSelected
                  ? 'ring-2 ring-[#102A43] shadow-md bg-white border-[#102A43]'
                  : 'border-[#E2E8F0] hover:border-[#94A3B8] hover:bg-white'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <div className="p-1.5 rounded bg-white shadow-xs border border-[#E2E8F0]">
                  {getStageIcon(stage.id)}
                </div>
                <span className="text-[11px] font-bold font-mono px-2 py-0.5 rounded bg-white border border-[#E2E8F0] text-[#334E68]">
                  {stage.percentage_of_sanctioned}% of Sanctioned
                </span>
              </div>

              <div className="space-y-1">
                <span className="text-[11px] font-bold uppercase tracking-wider text-[#64748B] block">
                  {stage.name}
                </span>
                <div className="text-xl font-bold font-display text-[#102A43]">
                  {formatCr(stage.amount)}
                </div>
                <div className="text-xs text-[#64748B] flex items-center justify-between pt-2 border-t border-[#E2E8F0]">
                  <span>{formatNumber(stage.records_count || 0)} works</span>
                  <span className="text-[10px] text-[#2563EB] font-medium underline">Details</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Stage Detail Drawer / Info Box */}
      {selectedStage ? (
        <div className="p-4 rounded-lg bg-[#EFF6FF] border border-[#BFDBFE] flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 animate-fadeIn">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold uppercase tracking-wider text-[#1E40AF]">
                {selectedStage.name} Stage Definition
              </span>
              <span className="text-xs text-[#6B7280]">•</span>
              <span className="text-xs font-mono font-bold text-[#1E3A8A]">
                {formatCr(selectedStage.amount)} ({formatNumber(selectedStage.records_count || 0)} records)
              </span>
            </div>
            <p className="text-xs text-[#1E3A8A] leading-relaxed">
              {selectedStage.description}
            </p>
          </div>
          <div className="text-right shrink-0">
            <span className="text-[10px] uppercase font-bold text-[#64748B] block">Data Lineage</span>
            <span className="text-xs font-semibold text-[#102A43] bg-white px-2.5 py-1 rounded border border-[#CBD5E1]">
              {selectedStage.source}
            </span>
          </div>
        </div>
      ) : (
        <div className="text-[11px] text-[#64748B] flex items-center justify-between px-1">
          <span>Click any pipeline stage above to view granular data lineage and definitions.</span>
          <span className="text-[10px] font-mono text-[#94A3B8]">Source: Official MPLADS Master Ledgers</span>
        </div>
      )}
    </div>
  );
};
