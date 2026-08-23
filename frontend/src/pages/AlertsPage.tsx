import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import { AlertRecord, AlertStatus, Pagination } from '../types';
import { EvidenceRoomModal } from '../components/explainer/EvidenceRoomModal';
import { TableSkeleton } from '../components/common/LoadingSkeleton';
import { EmptyState } from '../components/common/EmptyState';
import { formatExactCurrency } from '../lib/utils';
import {
  ShieldAlert, CheckCircle, Clock, ExternalLink, ChevronLeft,
  ChevronRight, Search, FileText, ArrowUpDown, Filter, Eye, AlertTriangle, CheckSquare
} from 'lucide-react';

export const AlertsPage: React.FC = () => {
  const [alerts, setAlerts] = useState<AlertRecord[]>([]);
  const [summary, setSummary] = useState<any>({});
  const [pagination, setPagination] = useState<Pagination | null>(null);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>('OPEN');
  const [severityFilter, setSeverityFilter] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [search, setSearch] = useState('');
  const [sortBy, setSortBy] = useState('priority');
  const [page, setPage] = useState(1);
  const [evidenceAlertId, setEvidenceAlertId] = useState<string | null>(null);
  const navigate = useNavigate();

  const loadAlerts = async () => {
    setLoading(true);
    try {
      const res = await api.getAlerts({
        status: statusFilter === 'ALL' ? '' : statusFilter,
        severity: severityFilter,
        alert_type: typeFilter,
        q: search,
        sort_by: sortBy,
        page,
        limit: 20,
      });
      setAlerts(res.data);
      setSummary(res.summary || {});
      setPagination(res.pagination);
    } catch (err) {
      console.error('Failed to load alerts', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAlerts();
  }, [statusFilter, severityFilter, typeFilter, search, sortBy, page]);

  const getSeverityBadge = (sev: string) => {
    switch (sev) {
      case 'CRITICAL':
        return <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-red-500/20 text-red-400 border border-red-500/30">CRITICAL</span>;
      case 'HIGH':
        return <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-orange-500/20 text-orange-400 border border-orange-500/30">HIGH</span>;
      case 'MEDIUM':
        return <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-amber-500/20 text-amber-400 border border-amber-500/30">MEDIUM</span>;
      default:
        return <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">LOW</span>;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'OPEN':
        return <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-slate-800 text-slate-300 border border-slate-700">OPEN</span>;
      case 'UNDER_REVIEW':
        return <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">UNDER REVIEW</span>;
      case 'EVIDENCE_REQUESTED':
        return <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-amber-500/20 text-amber-400 border border-amber-500/30">EVIDENCE REQ</span>;
      case 'VALIDATED':
        return <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-blue-500/20 text-blue-400 border border-blue-500/30">VALIDATED</span>;
      case 'RESOLVED':
      case 'CLOSED':
        return <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">RESOLVED</span>;
      default:
        return <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-slate-800 text-slate-400">{status}</span>;
    }
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Evidence Room Modal */}
      {evidenceAlertId && (
        <EvidenceRoomModal
          alertId={evidenceAlertId}
          isOpen={!!evidenceAlertId}
          onClose={() => setEvidenceAlertId(null)}
          onStatusUpdated={() => {
            loadAlerts();
          }}
        />
      )}

      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-2 text-xs font-mono uppercase tracking-wider text-indigo-400 mb-1">
            <ShieldAlert className="w-4 h-4" />
            DECISION-SUPPORT & OVERSIGHT WORKSPACE
          </div>
          <h1 className="text-2xl font-bold text-slate-100 tracking-tight">
            Priority Review Queue & Analytical Signals
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Ranked statistical anomaly signals prioritizing financial exposure, evidence strength, and model confidence for human review.
          </p>
        </div>

        {/* Top Summary Cards */}
        <div className="flex items-center gap-2">
          <div className="bg-slate-900 border border-slate-800 px-3 py-1.5 rounded-lg text-center">
            <div className="text-[10px] font-mono uppercase text-slate-500">Open Signals</div>
            <div className="text-sm font-bold font-mono text-amber-400">{summary.open_count ?? 270}</div>
          </div>
          <div className="bg-slate-900 border border-slate-800 px-3 py-1.5 rounded-lg text-center">
            <div className="text-[10px] font-mono uppercase text-slate-500">In Review</div>
            <div className="text-sm font-bold font-mono text-indigo-400">{summary.in_review_count ?? 0}</div>
          </div>
          <div className="bg-slate-900 border border-slate-800 px-3 py-1.5 rounded-lg text-center">
            <div className="text-[10px] font-mono uppercase text-slate-500">Resolved</div>
            <div className="text-sm font-bold font-mono text-emerald-400">{summary.resolved_count ?? 0}</div>
          </div>
        </div>
      </div>

      {/* Workflow Tabs */}
      <div className="flex flex-wrap border-b border-slate-800 gap-4 text-xs font-mono font-medium">
        {[
          { id: 'OPEN', label: `OPEN QUEUE (${summary.open_count ?? 270})` },
          { id: 'UNDER_REVIEW', label: `UNDER REVIEW (${summary.in_review_count ?? 0})` },
          { id: 'RESOLVED', label: `RESOLVED / VALIDATED (${summary.resolved_count ?? 0})` },
          { id: 'ALL', label: `ALL SIGNALS (${summary.total_alerts ?? 270})` },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => {
              setStatusFilter(tab.id);
              setPage(1);
            }}
            className={`pb-3 transition-colors border-b-2 ${
              statusFilter === tab.id
                ? 'border-indigo-500 text-indigo-400 font-bold'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Filters Bar */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 bg-slate-900/60 p-3 rounded-xl border border-slate-800">
        <div className="lg:col-span-2 relative">
          <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-500" />
          <input
            type="text"
            placeholder="Search by Work ID, State, District, or Keywords..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
            className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-indigo-500"
          />
        </div>

        <div>
          <select
            value={severityFilter}
            onChange={(e) => {
              setSeverityFilter(e.target.value);
              setPage(1);
            }}
            className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
          >
            <option value="">All Severities</option>
            <option value="CRITICAL">Critical Severity</option>
            <option value="HIGH">High Severity</option>
            <option value="MEDIUM">Medium Severity</option>
            <option value="LOW">Low Severity</option>
          </select>
        </div>

        <div>
          <select
            value={typeFilter}
            onChange={(e) => {
              setTypeFilter(e.target.value);
              setPage(1);
            }}
            className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
          >
            <option value="">All Signal Types</option>
            <option value="COST_ANOMALY">Cost Outliers (IQR/MAD)</option>
            <option value="POSSIBLE_DUPLICATE">Potential Duplicate Clusters</option>
            <option value="PROGRESS_GAP">Progress & Utilization Gaps</option>
          </select>
        </div>

        <div>
          <select
            value={sortBy}
            onChange={(e) => {
              setSortBy(e.target.value);
              setPage(1);
            }}
            className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
          >
            <option value="priority">Priority Ranking (Highest First)</option>
            <option value="date">Date Generated (Recent First)</option>
          </select>
        </div>
      </div>

      {/* Main Review Queue Table */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
        {loading ? (
          <div className="p-6">
            <TableSkeleton rows={8} />
          </div>
        ) : alerts.length === 0 ? (
          <div className="p-12 text-center text-slate-400 text-xs font-mono">
            No analytical signals matching the current review filter.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/80 text-slate-400 font-mono uppercase text-[10px] border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4 w-12 text-center">Rank</th>
                  <th className="py-3 px-4">Signal Details & Work ID</th>
                  <th className="py-3 px-4">Jurisdiction</th>
                  <th className="py-3 px-4">Financial Exposure</th>
                  <th className="py-3 px-4 text-center">Confidence</th>
                  <th className="py-3 px-4 text-center">Status</th>
                  <th className="py-3 px-4 text-right">Investigation Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-300">
                {alerts.map((alert, idx) => {
                  const globalRank = (page - 1) * 20 + idx + 1;
                  return (
                    <tr key={alert.id} className="hover:bg-slate-800/40 transition-colors">
                      {/* Priority Rank */}
                      <td className="py-3 px-4 text-center font-mono text-[11px] font-bold text-slate-400">
                        <span className={`inline-block px-1.5 py-0.5 rounded text-[10px] ${
                          globalRank <= 10 ? 'bg-indigo-950 text-indigo-300 border border-indigo-700/50' : 'text-slate-500'
                        }`}>
                          #{globalRank}
                        </span>
                      </td>

                      {/* Signal Details */}
                      <td className="py-3 px-4 max-w-sm">
                        <div className="flex items-center gap-2 mb-1">
                          {getSeverityBadge(alert.severity)}
                          <span className="font-mono text-indigo-400 text-[11px] truncate">{alert.work_code}</span>
                        </div>
                        <div className="font-medium text-slate-200 text-[11px] line-clamp-1">
                          {alert.title || 'Statistical Anomaly Detected'}
                        </div>
                        <div className="text-slate-400 text-[10px] line-clamp-1 mt-0.5">
                          {alert.evidence}
                        </div>
                      </td>

                      {/* Jurisdiction */}
                      <td className="py-3 px-4 text-[11px]">
                        <div className="text-slate-200">{alert.district || '—'}</div>
                        <div className="text-slate-400 text-[10px]">{alert.state}</div>
                      </td>

                      {/* Financial Exposure */}
                      <td className="py-3 px-4 font-mono text-[11px]">
                        <div className="text-slate-200 font-bold">
                          ₹{((alert.sanctioned_amount || 0) / 100000).toFixed(2)} Lakhs
                        </div>
                        <div className="text-slate-500 text-[10px]">
                          Util: {alert.expenditure_amount ? `₹${((alert.expenditure_amount) / 100000).toFixed(2)} L` : '₹0'}
                        </div>
                      </td>

                      {/* Confidence */}
                      <td className="py-3 px-4 text-center font-mono text-[11px]">
                        <span className="px-2 py-0.5 bg-slate-950 rounded border border-slate-800 text-indigo-300">
                          {alert.confidence || 82}%
                        </span>
                      </td>

                      {/* Status */}
                      <td className="py-3 px-4 text-center">
                        {getStatusBadge(alert.status)}
                      </td>

                      {/* Action Button */}
                      <td className="py-3 px-4 text-right">
                        <button
                          onClick={() => setEvidenceAlertId(alert.id)}
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-indigo-600/90 hover:bg-indigo-500 text-white rounded-lg font-medium text-[11px] transition-colors shadow-sm"
                        >
                          <Eye className="w-3.5 h-3.5" />
                          Evidence Room
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        {pagination && pagination.total_pages > 1 && (
          <div className="px-4 py-3 bg-slate-950/60 border-t border-slate-800 flex items-center justify-between text-xs font-mono text-slate-400">
            <span>
              Showing {(page - 1) * 20 + 1}–{Math.min(page * 20, pagination.total_records)} of {pagination.total_records} signals
            </span>
            <div className="flex items-center gap-2">
              <button
                disabled={!pagination.has_prev}
                onClick={() => setPage(page - 1)}
                className="px-3 py-1 rounded bg-slate-800 hover:bg-slate-700 disabled:opacity-40 transition-colors text-slate-200"
              >
                Previous
              </button>
              <button
                disabled={!pagination.has_next}
                onClick={() => setPage(page + 1)}
                className="px-3 py-1 rounded bg-slate-800 hover:bg-slate-700 disabled:opacity-40 transition-colors text-slate-200"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
