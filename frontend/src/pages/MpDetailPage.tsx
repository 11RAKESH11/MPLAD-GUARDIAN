import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import { MPPortfolio } from '../types';
import { formatCurrency, formatNumber } from '../lib/utils';
import { SourceBadge } from '../components/common/SourceBadge';
import { CardSkeleton } from '../components/common/LoadingSkeleton';
import { ArrowLeft, ExternalLink } from 'lucide-react';

export const MpDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [mp, setMp] = useState<MPPortfolio | null>(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    api.getMpDetail(decodeURIComponent(id))
      .then((res) => {
        setMp(res);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [id]);

  if (loading || !mp) {
    return (
      <div className="space-y-6">
        <div className="h-12 w-48 bg-white rounded animate-pulse" />
        <CardSkeleton count={4} />
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Header */}
      <div className="flex items-center justify-between pb-4 border-b border-[#E5E7EB]">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/mps')}
            className="p-2 rounded bg-white hover:bg-[#F0F2ED] border border-[#E5E7EB] text-[#667085] hover:text-[#172033] transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="px-2 py-0.5 rounded text-[10px] bg-[#F0F4F8] text-[#102A43] border border-[#D9E2EC] font-semibold">
                {mp.house === 'LOK_SABHA' ? 'Lok Sabha' : 'Rajya Sabha'}
              </span>
              <span className="text-xs text-[#667085]">{mp.state} • {mp.constituency}</span>
            </div>
            <h2 className="text-xl lg:text-2xl font-bold text-[#172033] tracking-tight font-display">
              {mp.name}
            </h2>
          </div>
        </div>

        <SourceBadge type="DERIVED ANALYTICS" />
      </div>

      {/* Portfolio Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
        <div className="gov-card p-4">
          <span className="text-[#667085] text-[10px] block uppercase font-bold">Allocated Limit</span>
          <span className="text-lg font-bold text-[#172033] font-display">{formatCurrency(mp.allocated_limit)}</span>
        </div>
        <div className="gov-card p-4">
          <span className="text-[#667085] text-[10px] block uppercase font-bold">Sanctioned Funds</span>
          <span className="text-lg font-bold text-[#102A43] font-display">{formatCurrency(mp.total_sanctioned_amount)}</span>
        </div>
        <div className="gov-card p-4">
          <span className="text-[#667085] text-[10px] block uppercase font-bold">Expenditure</span>
          <span className="text-lg font-bold text-[#147A73] font-display">{formatCurrency(mp.total_expenditure_amount)}</span>
        </div>
        <div className="gov-card p-4">
          <span className="text-[#667085] text-[10px] block uppercase font-bold">Sanctioned Works</span>
          <span className="text-lg font-bold text-[#14804A] font-mono">{formatNumber(mp.total_sanctioned_works)}</span>
        </div>
      </div>

      {/* Works Table */}
      <div className="gov-card overflow-hidden space-y-4 p-6 shadow-card">
        <div className="flex items-center justify-between pb-3 border-b border-[#E5E7EB]">
          <div>
            <h3 className="text-sm font-bold font-sans uppercase tracking-wide text-[#172033]">
              Sponsored Developmental Works ({mp.projects?.length || 0})
            </h3>
            <p className="text-xs text-[#667085]">Indexed project proposals sponsored by this Member of Parliament</p>
          </div>
          <button
            onClick={() => navigate(`/projects?q=${encodeURIComponent(mp.name)}`)}
            className="px-3 py-1.5 bg-[#102A43] hover:bg-[#193354] text-white text-xs font-semibold rounded shadow-xs transition-colors"
          >
            View in Project Explorer
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#F7F8F6] border-b border-[#E5E7EB] text-[#667085] font-sans font-bold uppercase text-[11px]">
              <tr>
                <th className="p-3">Work Code / Title</th>
                <th className="p-3">District</th>
                <th className="p-3">Category</th>
                <th className="p-3 text-right">Sanctioned (₹)</th>
                <th className="p-3">Status</th>
                <th className="p-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E5E7EB]">
              {mp.projects?.map((p) => (
                <tr
                  key={p.work_code}
                  onClick={() => navigate(`/projects/${encodeURIComponent(p.work_code)}`)}
                  className="hover:bg-[#F7F8F6] cursor-pointer transition-colors"
                >
                  <td className="p-3 max-w-sm">
                    <span className="text-[#102A43] font-bold font-mono block truncate">{p.work_code}</span>
                    <span className="text-[#667085] text-[11px] line-clamp-1">{p.work_type}</span>
                  </td>
                  <td className="p-3 text-[#172033]">{p.district}</td>
                  <td className="p-3 text-[#667085]">{p.category}</td>
                  <td className="p-3 text-right font-semibold text-[#172033]">{formatCurrency(p.sanctioned_amount)}</td>
                  <td className="p-3">
                    <span className="px-2 py-0.5 rounded text-[10px] bg-[#F0F2ED] text-[#667085] border border-[#E5E7EB]">
                      {p.status}
                    </span>
                  </td>
                  <td className="p-3 text-right">
                    <ExternalLink className="w-3.5 h-3.5 text-[#98A2B3] hover:text-[#102A43] inline" />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
