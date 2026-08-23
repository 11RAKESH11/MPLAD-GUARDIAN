import React from 'react';
import { ComparableProject } from '../../types';
import { RiskBadge } from '../common/RiskBadge';
import { formatExactCurrency } from '../../lib/utils';
import { ExternalLink, GitCompare, CheckCircle2, ArrowRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface ComparableProjectsListProps {
  comparables: ComparableProject[];
  currentWorkCode: string;
}

export const ComparableProjectsList: React.FC<ComparableProjectsListProps> = ({
  comparables,
  currentWorkCode,
}) => {
  const navigate = useNavigate();

  if (!comparables || comparables.length === 0) {
    return (
      <div className="gov-card p-8 text-center text-xs text-[#667085]">
        No direct duplicate similarity candidates detected for this project within the same district/category.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h4 className="text-sm font-bold text-[#172033] uppercase font-sans tracking-wide">
            Potential Duplicate Matches & Similarity Comparison ({comparables.length})
          </h4>
          <p className="text-xs text-[#667085]">
            Semantic description and financial proximity matches requiring desk audit review
          </p>
        </div>
        <span className="text-[11px] font-mono text-[#667085]">TF-IDF Cosine & Proximity</span>
      </div>

      <div className="space-y-4">
        {comparables.map((comp, idx) => (
          <div
            key={idx}
            className="gov-card p-5 space-y-4 border-l-4 border-l-[#147A73]"
          >
            {/* Top Match Bar */}
            <div className="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-[#E5E7EB]">
              <div className="flex items-center gap-2">
                <span className="px-2 py-0.5 rounded text-[11px] font-mono font-bold bg-[#EDF8F8] text-[#147A73] border border-[#D6EFEF]">
                  TEXT SIMILARITY: {Math.round(comp.similarity_score)}%
                </span>
                <span className="px-2 py-0.5 rounded text-[11px] font-mono font-bold bg-[#F0F4F8] text-[#102A43] border border-[#D9E2EC]">
                  LOCATION: Same District ({comp.district})
                </span>
              </div>

              <span className="text-[11px] font-bold text-[#C27A00] uppercase font-mono">
                POTENTIAL MATCH — REQUIRES REVIEW
              </span>
            </div>

            {/* Side-by-Side Visual Comparison (Section 23) */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
              {/* Left: Project A */}
              <div className="p-3.5 bg-[#F7F8F6] rounded border border-[#E5E7EB] space-y-2">
                <span className="text-[10px] font-bold uppercase tracking-wider text-[#667085] block">
                  Project A (Current Dossier)
                </span>
                <span className="font-mono font-bold text-[#102A43] block truncate">{currentWorkCode}</span>
                <p className="text-[#172033] line-clamp-2 text-[11px]">
                  Primary proposal under active investigation
                </p>
              </div>

              {/* Right: Project B (Candidate) */}
              <div className="p-3.5 bg-[#F7F8F6] rounded border border-[#E5E7EB] space-y-2">
                <span className="text-[10px] font-bold uppercase tracking-wider text-[#667085] block">
                  Project B (Comparable Proposal)
                </span>
                <span className="font-mono font-bold text-[#102A43] block truncate">{comp.comparable_work_code}</span>
                <p className="text-[#172033] line-clamp-2 text-[11px]">
                  {comp.work_type || 'Developmental Project'}
                </p>
                {comp.sanctioned_amount !== undefined && (
                  <div className="text-[11px] text-[#667085] pt-1">
                    Sanctioned: <strong className="text-[#172033]">{formatExactCurrency(comp.sanctioned_amount)}</strong>
                  </div>
                )}
              </div>
            </div>

            {/* Actions */}
            <div className="pt-2 flex items-center justify-between">
              {comp.reason && (
                <span className="text-xs text-[#C27A00]">
                  Finding: {comp.reason}
                </span>
              )}

              <button
                onClick={() => navigate(`/projects/${encodeURIComponent(comp.comparable_work_code)}`)}
                className="ml-auto inline-flex items-center gap-1.5 text-xs text-[#102A43] hover:text-[#1769E0] font-semibold"
              >
                <span>Inspect Comparable Record</span>
                <ExternalLink className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
