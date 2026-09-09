import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { api } from '../services/api';
import { Project, Pagination } from '../types';
import { RiskBadge } from '../components/common/RiskBadge';
import { SourceBadge } from '../components/common/SourceBadge';
import { TableSkeleton } from '../components/common/LoadingSkeleton';
import { EmptyState } from '../components/common/EmptyState';
import { formatCurrency, formatNumber } from '../lib/utils';
import {
  Search,
  Download,
  ArrowUpDown,
  ChevronLeft,
  ChevronRight,
  ExternalLink,
  RotateCcw
} from 'lucide-react';

export const ProjectsPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [projects, setProjects] = useState<Project[]>([]);
  const [pagination, setPagination] = useState<Pagination | null>(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  const q = searchParams.get('q') || '';
  const state = searchParams.get('state') || '';
  const district = searchParams.get('district') || '';
  const category = searchParams.get('category') || '';
  const financial_year = searchParams.get('financial_year') || '';
  const status = searchParams.get('status') || '';
  const risk_level = searchParams.get('risk_level') || '';
  const sort_by = searchParams.get('sort_by') || 'overall_risk_score';
  const order = searchParams.get('order') || 'desc';
  const page = parseInt(searchParams.get('page') || '1', 10);
  const limit = parseInt(searchParams.get('limit') || '25', 10);

  const [searchInput, setSearchInput] = useState(q);

  const updateFilters = (newParams: Record<string, string | number | null>) => {
    const updated = new URLSearchParams(searchParams);
    Object.entries(newParams).forEach(([k, v]) => {
      if (v === null || v === '' || v === undefined) {
        updated.delete(k);
      } else {
        updated.set(k, String(v));
      }
    });
    setSearchParams(updated);
  };

  const loadProjects = async () => {
    setLoading(true);
    try {
      const res = await api.getProjects({
        q,
        state,
        district,
        category,
        financial_year,
        status,
        risk_level,
        sort_by,
        order,
        page,
        limit,
      });
      setProjects(res.data);
      setPagination(res.meta);
    } catch (err) {
      console.error('Failed to load projects', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProjects();
  }, [searchParams]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    updateFilters({ q: searchInput, page: 1 });
  };

  const resetFilters = () => {
    setSearchInput('');
    setSearchParams(new URLSearchParams());
  };

  const exportCSV = () => {
    if (!projects.length) return;
    const headers = ['Work Code', 'State', 'District', 'MP Name', 'Category', 'Sanctioned Amount', 'Disbursed Amount', 'Status', 'Risk Score', 'Risk Level'];
    const rows = projects.map(p => [
      p.work_code,
      p.state,
      p.district,
      p.mp_name,
      p.category,
      p.sanctioned_amount,
      p.expenditure_amount,
      p.status,
      p.overall_risk_score,
      p.risk_level
    ]);
    const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map(e => e.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `MPLADS_Projects_${Date.now()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-xl lg:text-2xl font-extrabold text-[#172033] tracking-tight font-display">
            Project Intelligence Explorer
          </h2>
          <p className="text-xs text-[#667085] mt-0.5">
            Structured repository of 96,654 parliamentary development proposals across India
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={exportCSV}
            className="px-3.5 py-1.5 bg-white hover:bg-[#F0F2ED] text-[#172033] text-xs font-semibold rounded border border-[#E5E7EB] inline-flex items-center gap-2 transition-colors"
          >
            <Download className="w-3.5 h-3.5 text-[#102A43]" />
            <span>Export CSV</span>
          </button>
          <SourceBadge type="REAL SOURCE DATA" />
        </div>
      </div>

      {/* Filter & Search Bar */}
      <div className="gov-card p-4 flex flex-wrap items-center justify-between gap-4 bg-white">
        <form onSubmit={handleSearchSubmit} className="flex items-center gap-2 flex-1 max-w-lg">
          <div className="relative flex-1">
            <Search className="w-3.5 h-3.5 text-[#98A2B3] absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder="Search work code, MP name, description, district..."
              className="w-full pl-9 pr-4 py-1.5 bg-[#F7F8F6] border border-[#E5E7EB] rounded text-xs text-[#172033] placeholder-[#98A2B3] focus:outline-none focus:border-[#102A43]"
            />
          </div>
          <button
            type="submit"
            className="px-3.5 py-1.5 bg-[#102A43] hover:bg-[#193354] text-white text-xs font-semibold rounded shadow-xs transition-colors"
          >
            Search
          </button>
        </form>

        <div className="flex flex-wrap items-center gap-3">
          {/* Risk Level Filter */}
          <select
            value={risk_level}
            onChange={(e) => updateFilters({ risk_level: e.target.value, page: 1 })}
            className="px-3 py-1.5 bg-white border border-[#E5E7EB] rounded text-xs text-[#667085] focus:outline-none focus:border-[#102A43]"
          >
            <option value="">All Risk Signals</option>
            <option value="CRITICAL">Critical Signal (80-100)</option>
            <option value="HIGH">High Signal (60-79)</option>
            <option value="MEDIUM">Review Required (40-59)</option>
            <option value="LOW">Low Signal (0-39)</option>
          </select>

          {/* Sort Selector */}
          <select
            value={sort_by}
            onChange={(e) => updateFilters({ sort_by: e.target.value, page: 1 })}
            className="px-3 py-1.5 bg-white border border-[#E5E7EB] rounded text-xs text-[#667085] focus:outline-none focus:border-[#102A43]"
          >
            <option value="overall_risk_score">Sort: Risk Score</option>
            <option value="sanctioned_amount">Sort: Sanctioned Amount</option>
            <option value="utilization_pct">Sort: Utilization %</option>
            <option value="sanction_date">Sort: Sanction Date</option>
          </select>

          <button
            onClick={() => updateFilters({ order: order === 'asc' ? 'desc' : 'asc' })}
            className="p-1.5 bg-white border border-[#E5E7EB] rounded text-[#667085] hover:text-[#172033] transition-colors"
            title={`Toggle order (${order.toUpperCase()})`}
          >
            <ArrowUpDown className="w-3.5 h-3.5" />
          </button>

          {(q || state || district || category || financial_year || status || risk_level) && (
            <button
              onClick={resetFilters}
              className="px-3 py-1.5 bg-[#FDF2F2] text-[#C2413B] border border-[#F9DFDF] rounded text-xs inline-flex items-center gap-1.5 hover:bg-[#F9DFDF] transition-colors"
            >
              <RotateCcw className="w-3 h-3" />
              <span>Reset</span>
            </button>
          )}
        </div>
      </div>

      {/* Projects Table (Section 19) */}
      {loading ? (
        <TableSkeleton rows={10} />
      ) : projects.length === 0 ? (
        <EmptyState
          title="No Projects Found"
          description="Try broadening your search query or resetting filters."
          actionText="Reset All Filters"
          onAction={resetFilters}
        />
      ) : (
        <div className="gov-card overflow-hidden shadow-card">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-[#F7F8F6] border-b border-[#E5E7EB] text-[#667085] font-sans font-bold uppercase tracking-wider text-[11px] sticky top-0">
                <tr>
                  <th className="p-3.5">Project / Work Code</th>
                  <th className="p-3.5">State / District</th>
                  <th className="p-3.5">Constituency / MP</th>
                  <th className="p-3.5">Category</th>
                  <th className="p-3.5 text-right">Sanctioned (₹)</th>
                  <th className="p-3.5 text-right">Utilized (₹)</th>
                  <th className="p-3.5">Status</th>
                  <th className="p-3.5 text-center">Risk Signal</th>
                  <th className="p-3.5 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E5E7EB]">
                {projects.map((p) => (
                  <tr
                    key={p.work_code}
                    onClick={() => navigate(`/projects/${encodeURIComponent(p.work_code)}`)}
                    className="hover:bg-[#F7F8F6] transition-colors cursor-pointer"
                  >
                    <td className="p-3.5 max-w-xs">
                      <span className="text-[#102A43] font-bold font-mono block truncate">{p.work_code}</span>
                      <span className="text-[#667085] line-clamp-1 text-[11px] mt-0.5">
                        {p.work_type || p.description || 'MPLADS Project'}
                      </span>
                    </td>

                    <td className="p-3.5">
                      <span className="text-[#172033] block font-medium">{p.state}</span>
                      <span className="text-[#98A2B3] text-[10px]">{p.district || p.constituency}</span>
                    </td>

                    <td className="p-3.5 max-w-[180px]">
                      <span className="text-[#172033] block truncate font-medium">{p.mp_name || 'N/A'}</span>
                      <span className="text-[#98A2B3] text-[10px]">{p.house === 'LOK_SABHA' ? 'Lok Sabha' : 'Rajya Sabha'}</span>
                    </td>

                    <td className="p-3.5 text-[#667085] max-w-[120px] truncate">
                      {p.category}
                    </td>

                    <td className="p-3.5 text-right font-semibold text-[#172033]">
                      {formatCurrency(p.sanctioned_amount)}
                    </td>

                    <td className="p-3.5 text-right font-medium text-[#147A73]">
                      {formatCurrency(p.expenditure_amount)}
                    </td>

                    <td className="p-3.5">
                      <span className="px-2 py-0.5 rounded text-[10px] bg-[#F0F2ED] text-[#667085] border border-[#E5E7EB]">
                        {p.status}
                      </span>
                    </td>

                    <td className="p-3.5 text-center">
                      <RiskBadge level={p.risk_level} score={p.overall_risk_score} size="sm" />
                    </td>

                    <td className="p-3.5 text-right">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          navigate(`/projects/${encodeURIComponent(p.work_code)}`);
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

          {/* Pagination Footer */}
          {pagination && (
            <div className="p-3.5 bg-[#F7F8F6] border-t border-[#E5E7EB] flex items-center justify-between text-xs text-[#667085]">
              <div>
                Showing <strong className="text-[#172033] font-mono">{((page - 1) * limit) + 1}</strong> to{' '}
                <strong className="text-[#172033] font-mono">{Math.min(page * limit, pagination.total)}</strong> of{' '}
                <strong className="text-[#172033] font-mono">{formatNumber(pagination.total)}</strong> records
              </div>

              <div className="flex items-center gap-2">
                <button
                  disabled={!pagination.has_prev}
                  onClick={() => updateFilters({ page: page - 1 })}
                  className={`p-1.5 rounded border border-[#E5E7EB] bg-white text-[#172033] transition-colors ${
                    !pagination.has_prev ? 'opacity-40 cursor-not-allowed' : 'hover:bg-[#F0F2ED]'
                  }`}
                >
                  <ChevronLeft className="w-3.5 h-3.5" />
                </button>
                <span className="px-2.5 py-1 bg-white border border-[#E5E7EB] rounded text-[#172033] font-medium font-mono text-[11px]">
                  {page} / {pagination.total_pages}
                </span>
                <button
                  disabled={!pagination.has_next}
                  onClick={() => updateFilters({ page: page + 1 })}
                  className={`p-1.5 rounded border border-[#E5E7EB] bg-white text-[#172033] transition-colors ${
                    !pagination.has_next ? 'opacity-40 cursor-not-allowed' : 'hover:bg-[#F0F2ED]'
                  }`}
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
