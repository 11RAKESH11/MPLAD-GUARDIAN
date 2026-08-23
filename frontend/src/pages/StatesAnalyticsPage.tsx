import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import { StateSummary } from '../types';
import { SourceBadge } from '../components/common/SourceBadge';
import { CardSkeleton } from '../components/common/LoadingSkeleton';
import { formatCurrency, formatNumber } from '../lib/utils';
import { Building2, Search, ArrowRight } from 'lucide-react';

export const StatesAnalyticsPage: React.FC = () => {
  const [states, setStates] = useState<StateSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    api.getStates().then((res) => {
      setStates(res.states);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  const filteredStates = states.filter((s) =>
    s.state.toLowerCase().includes(search.toLowerCase())
  );

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-16 bg-white rounded animate-pulse border border-[#E5E7EB]" />
        <CardSkeleton count={8} />
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fadeIn">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-xl lg:text-2xl font-extrabold text-[#172033] tracking-tight font-display">
            State & Regional Development Intelligence
          </h2>
          <p className="text-xs text-[#667085] mt-0.5">
            Comparative performance, risk distribution, and funding analytics across 36 States & UTs
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="relative w-64">
            <Search className="w-3.5 h-3.5 text-[#98A2B3] absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search State or UT..."
              className="w-full pl-9 pr-4 py-1.5 bg-white border border-[#E5E7EB] rounded text-xs text-[#172033] placeholder-[#98A2B3] focus:outline-none focus:border-[#102A43]"
            />
          </div>
          <SourceBadge type="DERIVED ANALYTICS" />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {filteredStates.map((st) => (
          <div
            key={st.state}
            onClick={() => navigate(`/analytics/states/${encodeURIComponent(st.state)}`)}
            className="gov-card gov-card-hover p-6 cursor-pointer space-y-4 flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between pb-3 border-b border-[#E5E7EB]">
                <div className="flex items-center gap-2.5">
                  <div className="p-1.5 rounded bg-[#F0F4F8] text-[#102A43]">
                    <Building2 className="w-4 h-4" />
                  </div>
                  <h3 className="text-base font-bold text-[#172033] tracking-tight font-display">{st.state}</h3>
                </div>
                {st.high_risk_count > 0 ? (
                  <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-[#FDF2F2] text-[#C2413B] border border-[#F9DFDF]">
                    {st.high_risk_count} Signals
                  </span>
                ) : (
                  <span className="px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-[#EDF7F1] text-[#14804A] border-[#D5EFE0]">
                    Normal
                  </span>
                )}
              </div>

              <div className="grid grid-cols-2 gap-3 pt-3 text-xs">
                <div>
                  <span className="text-[#667085] text-[10px] uppercase font-bold block">Projects</span>
                  <span className="text-sm font-bold text-[#172033] font-mono">{formatNumber(st.total_projects)}</span>
                </div>
                <div>
                  <span className="text-[#667085] text-[10px] uppercase font-bold block">Districts</span>
                  <span className="text-sm font-bold text-[#172033] font-mono">{st.total_districts}</span>
                </div>
                <div>
                  <span className="text-[#667085] text-[10px] uppercase font-bold block">Sanctioned</span>
                  <span className="text-xs font-bold text-[#102A43] block truncate">{formatCurrency(st.total_sanctioned)}</span>
                </div>
                <div>
                  <span className="text-[#667085] text-[10px] uppercase font-bold block">Utilization</span>
                  <span className="text-xs font-bold text-[#14804A] font-mono">{st.utilization_pct}%</span>
                </div>
              </div>
            </div>

            <div className="pt-3 border-t border-[#E5E7EB] flex items-center justify-between text-xs">
              <span className="text-[#667085] text-[11px]">{st.total_mps} Parliamentarians</span>
              <span className="text-[#102A43] hover:text-[#1769E0] font-semibold inline-flex items-center gap-1">
                <span>View Districts</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
