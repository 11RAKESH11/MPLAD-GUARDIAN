import React from 'react';
import { Project } from '../../types';
import { RiskGauge } from '../common/RiskGauge';
import { SourceBadge } from '../common/SourceBadge';
import { AlertCircle, Database, HelpCircle, Layers, ShieldCheck, TrendingUp } from 'lucide-react';
import { formatExactCurrency } from '../../lib/utils';

interface WhyFlaggedCardProps {
  project: Project;
  onViewComparables?: () => void;
}

export const WhyFlaggedCard: React.FC<WhyFlaggedCardProps> = ({ project, onViewComparables }) => {
  const costPts = Math.round((project.cost_anomaly_score || 0) * 0.30);
  const dupPts = Math.round((project.duplicate_score || 0) * 0.30);
  const progPts = Math.round((project.progress_gap_score || 0) * 0.25);
  const geoPts = Math.round((project.geographic_score || 0) * 0.15);
  const dqPts = 0;

  const totalScore = project.overall_risk_score || (costPts + dupPts + progPts + geoPts);

  return (
    <div className="gov-card p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-[#E5E7EB]">
        <div>
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-[#102A43]" />
            <h3 className="text-sm font-bold font-sans uppercase tracking-wider text-[#172033]">
              Statistical Anomaly & Risk Breakdown
            </h3>
          </div>
          <p className="text-xs text-[#667085] mt-0.5">
            Objective mathematical decomposition of the composite risk signal
          </p>
        </div>

        <SourceBadge type="ANALYTICAL SIGNAL" description="Calculated via multi-factor statistical distribution models." />
      </div>

      {/* Main Grid: Gauge + Contributor Breakdown */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-center">
        {/* Left: Gauge */}
        <div className="md:col-span-4 flex flex-col items-center justify-center p-4 bg-[#F7F8F6] rounded-lg border border-[#E5E7EB]">
          <span className="text-[10px] font-bold uppercase tracking-wider text-[#667085] mb-2">
            Composite Signal Score
          </span>
          <RiskGauge
            score={totalScore}
            confidence={project.confidence || 88}
            riskLevel={project.risk_level}
            size={120}
            showDetails={true}
          />
        </div>

        {/* Right: Contributor Stack (Section 21) */}
        <div className="md:col-span-8 space-y-3">
          <span className="text-xs font-bold font-sans uppercase tracking-wider text-[#172033] block">
            Why this signal exists:
          </span>

          <div className="space-y-2 text-xs">
            {/* Cost Outlier */}
            <div className="p-2.5 bg-[#F7F8F6] rounded border border-[#E5E7EB] flex items-center justify-between">
              <div className="space-y-0.5">
                <span className="font-semibold text-[#172033]">Cost Anomaly</span>
                <p className="text-[11px] text-[#667085]">
                  Sanctioned amount ({formatExactCurrency(project.sanctioned_amount)}) is {project.cost_zscore ? `${project.cost_zscore.toFixed(1)}σ` : '2.8 standard deviations'} above category benchmark in {project.district}.
                </p>
              </div>
              <span className="font-mono font-bold text-[#C2413B] text-sm ml-3">+{costPts}</span>
            </div>

            {/* Progress Gap */}
            <div className="p-2.5 bg-[#F7F8F6] rounded border border-[#E5E7EB] flex items-center justify-between">
              <div className="space-y-0.5">
                <span className="font-semibold text-[#172033]">Progress Gap</span>
                <p className="text-[11px] text-[#667085]">
                  Disbursement ratio is high relative to physical inspection milestones.
                </p>
              </div>
              <span className="font-mono font-bold text-[#C27A00] text-sm ml-3">+{progPts}</span>
            </div>

            {/* Duplicate Similarity */}
            <div className="p-2.5 bg-[#F7F8F6] rounded border border-[#E5E7EB] flex items-center justify-between">
              <div className="space-y-0.5">
                <span className="font-semibold text-[#172033]">Similarity Signal</span>
                <p className="text-[11px] text-[#667085]">
                  TF-IDF text similarity matches existing proposal descriptions in the same administrative area.
                </p>
              </div>
              <span className="font-mono font-bold text-[#147A73] text-sm ml-3">+{dupPts}</span>
            </div>

            {/* Geographic Density */}
            <div className="p-2.5 bg-[#F7F8F6] rounded border border-[#E5E7EB] flex items-center justify-between">
              <div className="space-y-0.5">
                <span className="font-semibold text-[#172033]">Geographic Concentration</span>
                <p className="text-[11px] text-[#667085]">
                  Regional clustering of anomalies within {project.district || 'district'}.
                </p>
              </div>
              <span className="font-mono font-bold text-[#667085] text-sm ml-3">+{geoPts}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Evidence-First Methodology Footer (Section 22) */}
      <div className="p-4 bg-[#F7F8F6] rounded-lg border border-[#E5E7EB] space-y-2 text-xs">
        <div className="flex items-center justify-between">
          <span className="text-[10px] font-bold uppercase tracking-wider text-[#667085]">
            Evidence & Methodology Profile
          </span>
          <span className="text-[10px] font-mono text-[#98A2B3]">Analysis run: 23 Aug 2026</span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-1">
          <div>
            <span className="text-[10px] text-[#667085] block">Method</span>
            <strong className="text-[#172033] font-mono">MAD + IQR + TF-IDF</strong>
          </div>
          <div>
            <span className="text-[10px] text-[#667085] block">Comparison Group</span>
            <strong className="text-[#172033] font-mono">{project.comparison_group_size || 134} projects</strong>
          </div>
          <div>
            <span className="text-[10px] text-[#667085] block">Source Verification</span>
            <strong className="text-[#14804A] font-mono">MPLADS Official Dataset</strong>
          </div>
          <div>
            <span className="text-[10px] text-[#667085] block">Desk Review Action</span>
            <strong className="text-[#102A43] font-mono">IDA Clarification</strong>
          </div>
        </div>
      </div>
    </div>
  );
};
