import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import { MPPortfolio, Pagination } from '../types';
import { SourceBadge } from '../components/common/SourceBadge';
import { TableSkeleton } from '../components/common/LoadingSkeleton';
import { EmptyState } from '../components/common/EmptyState';
import { formatCurrency, formatNumber } from '../lib/utils';
import { Search, ExternalLink, ChevronLeft, ChevronRight } from 'lucide-react';

export const MpsAnalyticsPage: React.FC = () => {
  const [mps, setMps] = useState<MPPortfolio[]>([]);
  const [pagination, setPagination] = useState<Pagination | null>(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [house, setHouse] = useState('');
  const [page, setPage] = useState(1);
  const navigate = useNavigate();

  const loadMps = async () => {
    setLoading(true);
    try {
      const res = await api.getMps({ q: search, house, page, limit: 20 });
      setMps(res.data);
      setPagination(res.meta);
    } catch (err) {
      console.error('Failed to load MPs', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMps();
  }, [search, house, page]);

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-xl lg:text-2xl font-extrabold text-[#172033] tracking-tight font-display">
            Parliamentarian Development Portfolios
          </h2>
          <p className="text-xs text-[#667085] mt-0.5">
            Objective portfolio analytics across 764 Lok Sabha & Rajya Sabha Members of Parliament
          </p>
        </div>

        <SourceBadge type="DERIVED ANALYTICS" description="Objective developmental metrics without subjective bias." />
      </div>

      {/* Filter Bar */}
      <div className="gov-card p-4 flex flex-wrap items-center justify-between gap-4 bg-white">
        <div className="relative flex-1 max-w-md">
          <Search className="w-3.5 h-3.5 text-[#98A2B3] absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
            placeholder="Search MP Name, State, Constituency..."
            className="w-full pl-9 pr-4 py-1.5 bg-[#F7F8F6] border border-[#E5E7EB] rounded text-xs text-[#172033] placeholder-[#98A2B3] focus:outline-none focus:border-[#102A43]"
          />
        </div>

        <div className="flex items-center gap-3">
          <select
            value={house}
            onChange={(e) => {
              setHouse(e.target.value);
              setPage(1);
            }}
            className="px-3 py-1.5 bg-white border border-[#E5E7EB] rounded text-xs text-[#667085] focus:outline-none focus:border-[#102A43]"
          >
            <option value="">All Houses</option>
            <option value="LOK_SABHA">Lok Sabha (Elected)</option>
            <option value="RAJYA_SABHA">Rajya Sabha (State Rep)</option>
          </select>
        </div>
      </div>

      {/* Table */}
      {loading ? (
        <TableSkeleton rows={10} />
      ) : mps.length === 0 ? (
        <EmptyState title="No Parliamentarians Found" description="Try adjusting your search query." />
      ) : (
        <div className="gov-card overflow-hidden shadow-card">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-[#F7F8F6] border-b border-[#E5E7EB] text-[#667085] font-sans font-bold uppercase text-[11px]">
                <tr>
                  <th className="p-3.5">Hon'ble MP Name</th>
                  <th className="p-3.5">House / Type</th>
                  <th className="p-3.5">State / Constituency</th>
                  <th className="p-3.5 text-right">Allocated Limit (₹)</th>
                  <th className="p-3.5 text-right">Sanctioned Works</th>
                  <th className="p-3.5 text-right">Sanctioned (₹)</th>
                  <th className="p-3.5 text-right">Expenditure (₹)</th>
                  <th className="p-3.5 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E5E7EB]">
                {mps.map((m) => (
                  <tr
                    key={m.id}
                    onClick={() => navigate(`/mps/${encodeURIComponent(m.id)}`)}
                    className="hover:bg-[#F7F8F6] transition-colors cursor-pointer"
                  >
                    <td className="p-3.5 font-bold text-[#172033] max-w-xs truncate">
                      {m.name}
                    </td>

                    <td className="p-3.5">
                      <span className="px-2 py-0.5 rounded text-[10px] bg-[#F0F2ED] text-[#667085] border border-[#E5E7EB]">
                        {m.house === 'LOK_SABHA' ? 'Lok Sabha' : 'Rajya Sabha'}
                      </span>
                    </td>

                    <td className="p-3.5">
                      <span className="text-[#172033] block font-medium">{m.state}</span>
                      <span className="text-[#98A2B3] text-[10px]">{m.constituency}</span>
                    </td>

                    <td className="p-3.5 text-right text-[#667085]">
                      {formatCurrency(m.allocated_limit)}
                    </td>

                    <td className="p-3.5 text-right text-[#172033] font-bold font-mono">
                      {formatNumber(m.total_sanctioned_works)}
                    </td>

                    <td className="p-3.5 text-right text-[#102A43] font-medium">
                      {formatCurrency(m.total_sanctioned_amount)}
                    </td>

                    <td className="p-3.5 text-right text-[#147A73] font-medium">
                      {formatCurrency(m.total_expenditure_amount)}
                    </td>

                    <td className="p-3.5 text-right">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          navigate(`/mps/${encodeURIComponent(m.id)}`);
                        }}
                        className="p-1 text-[#98A2B3] hover:text-[#102A43] rounded hover:bg-[#F0F4F8] transition-colors"
                      >
                        <ExternalLink className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {pagination && (
            <div className="p-3.5 bg-[#F7F8F6] border-t border-[#E5E7EB] flex items-center justify-between text-xs text-[#667085]">
              <div>
                Page <strong className="text-[#172033] font-mono">{page}</strong> of <strong className="text-[#172033] font-mono">{pagination.total_pages}</strong>
              </div>
              <div className="flex items-center gap-2">
                <button
                  disabled={!pagination.has_prev}
                  onClick={() => setPage(page - 1)}
                  className="p-1.5 rounded border border-[#E5E7EB] bg-white disabled:opacity-40"
                >
                  <ChevronLeft className="w-3.5 h-3.5" />
                </button>
                <button
                  disabled={!pagination.has_next}
                  onClick={() => setPage(page + 1)}
                  className="p-1.5 rounded border border-[#E5E7EB] bg-white disabled:opacity-40"
                >
                  <ChevronRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
