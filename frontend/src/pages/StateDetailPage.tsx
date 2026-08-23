import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import { formatCurrency, formatNumber } from '../lib/utils';
import { SourceBadge } from '../components/common/SourceBadge';
import { CardSkeleton } from '../components/common/LoadingSkeleton';
import { ArrowLeft } from 'lucide-react';

export const StateDetailPage: React.FC = () => {
  const { state } = useParams<{ state: string }>();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    if (!state) return;
    setLoading(true);
    api.getStateDetail(decodeURIComponent(state)).then((res) => {
      setData(res);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, [state]);

  if (loading || !data) {
    return (
      <div className="space-y-6">
        <div className="h-12 w-48 bg-white rounded animate-pulse" />
        <CardSkeleton count={4} />
      </div>
    );
  }

  const { overview, districts } = data;

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Header */}
      <div className="flex items-center justify-between pb-4 border-b border-[#E5E7EB]">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/analytics/states')}
            className="p-2 rounded bg-white hover:bg-[#F0F2ED] border border-[#E5E7EB] text-[#667085] hover:text-[#172033] transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <h2 className="text-xl lg:text-2xl font-extrabold text-[#172033] tracking-tight font-display">
              {overview.state} Regional Intelligence Dossier
            </h2>
            <p className="text-xs text-[#667085] mt-0.5">
              {overview.total_districts} Districts • {overview.total_mps} Parliamentarians • {formatNumber(overview.total_projects)} Works
            </p>
          </div>
        </div>

        <SourceBadge type="DERIVED ANALYTICS" />
      </div>

      {/* Top Metrics */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
        <div className="gov-card p-4">
          <span className="text-[#667085] text-[10px] block uppercase font-bold">Total Sanctioned</span>
          <span className="text-lg font-bold text-[#102A43] font-display">{formatCurrency(overview.total_sanctioned)}</span>
        </div>
        <div className="gov-card p-4">
          <span className="text-[#667085] text-[10px] block uppercase font-bold">Expenditure</span>
          <span className="text-lg font-bold text-[#147A73] font-display">{formatCurrency(overview.total_expenditure)}</span>
        </div>
        <div className="gov-card p-4">
          <span className="text-[#667085] text-[10px] block uppercase font-bold">Completed Works</span>
          <span className="text-lg font-bold text-[#14804A] font-mono">{formatNumber(overview.completed_works)}</span>
        </div>
        <div className="gov-card p-4">
          <span className="text-[#667085] text-[10px] block uppercase font-bold">Risk Signals</span>
          <span className="text-lg font-bold text-[#C2413B] font-mono">{overview.critical_count + overview.high_count}</span>
        </div>
      </div>

      {/* Districts Matrix */}
      <div className="gov-card p-6 space-y-4 shadow-card">
        <div className="flex items-center justify-between pb-3 border-b border-[#E5E7EB]">
          <h3 className="text-sm font-bold font-sans uppercase tracking-wide text-[#172033]">
            District Jurisdiction Matrix ({districts.length})
          </h3>
          <span className="text-xs text-[#667085]">Click any district to view associated projects</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3 max-h-[420px] overflow-y-auto pr-1">
          {districts.map((d: any) => (
            <div
              key={d.district}
              onClick={() => navigate(`/projects?state=${encodeURIComponent(overview.state)}&district=${encodeURIComponent(d.district)}`)}
              className="p-3.5 rounded bg-white border border-[#E5E7EB] hover:border-[#102A43] transition-all cursor-pointer select-none space-y-2 shadow-xs"
            >
              <div className="flex items-center justify-between gap-1">
                <span className="text-xs font-bold text-[#172033] truncate">{d.district}</span>
                {d.high_risk_count > 0 && (
                  <span className="px-1.5 py-0.2 rounded text-[9px] font-mono font-bold bg-[#FDF2F2] text-[#C2413B] border border-[#F9DFDF]">
                    {d.high_risk_count} Signals
                  </span>
                )}
              </div>
              <div className="text-[11px] text-[#667085] flex justify-between">
                <span>Projects:</span>
                <strong className="text-[#172033] font-mono">{formatNumber(d.total_projects)}</strong>
              </div>
              <div className="text-[11px] text-[#667085] flex justify-between">
                <span>Sanctioned:</span>
                <strong className="text-[#102A43] font-medium">{formatCurrency(d.total_sanctioned)}</strong>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
