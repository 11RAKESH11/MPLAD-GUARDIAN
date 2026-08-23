import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { AuditLogRecord, Pagination } from '../types';
import { ShieldCheck, Search, Filter, Clock, FileText, ArrowRight, UserCheck, CheckCircle } from 'lucide-react';
import { TableSkeleton } from '../components/common/LoadingSkeleton';

export const AuditLogsPage: React.FC = () => {
  const [logs, setLogs] = useState<AuditLogRecord[]>([]);
  const [pagination, setPagination] = useState<Pagination>({
    page: 1,
    limit: 25,
    total_records: 0,
    total_pages: 1,
    has_next: false,
    has_prev: false,
  });
  const [loading, setLoading] = useState(true);
  const [actionFilter, setActionFilter] = useState('');
  const [targetTypeFilter, setTargetTypeFilter] = useState('');

  const fetchLogs = (page = 1) => {
    setLoading(true);
    api.getAuditLogs({
      page,
      limit: 25,
      action: actionFilter,
      target_type: targetTypeFilter,
    })
      .then((res) => {
        setLogs(res.logs || []);
        if (res.pagination) {
          setPagination(res.pagination);
        }
        setLoading(false);
      })
      .catch(() => {
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchLogs(1);
  }, [actionFilter, targetTypeFilter]);

  const getActionBadgeColor = (action: string) => {
    if (action.includes('STATUS') || action.includes('UPDATE')) return 'bg-indigo-500/20 text-indigo-400 border-indigo-500/30';
    if (action.includes('RESOLVED') || action.includes('VALIDATED')) return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30';
    if (action.includes('TRIAGE') || action.includes('INSPECTION')) return 'bg-amber-500/20 text-amber-400 border-amber-500/30';
    return 'bg-slate-800 text-slate-300 border-slate-700';
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-2 text-xs font-mono uppercase tracking-wider text-indigo-400 mb-1">
            <ShieldCheck className="w-4 h-4" />
            GOVERNANCE & DECISION TRACEABILITY
          </div>
          <h1 className="text-2xl font-bold text-slate-100 tracking-tight">
            System Audit Trail & Review History
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Immutable chronological record of analyst inspections, evidence requests, triage status transitions, and administrative actions.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="px-3 py-1 bg-slate-900 border border-slate-800 rounded-lg text-xs font-mono text-slate-300">
            {pagination.total_records} Verified Events
          </span>
        </div>
      </div>

      {/* Filters Bar */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 bg-slate-900/60 p-3 rounded-xl border border-slate-800">
        <div>
          <label className="block text-[11px] font-mono text-slate-400 mb-1">Filter by Action</label>
          <select
            value={actionFilter}
            onChange={(e) => setActionFilter(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
          >
            <option value="">All Administrative Actions</option>
            <option value="STATUS">Status Updates</option>
            <option value="TRIAGE">Signal Triage</option>
            <option value="EVIDENCE">Evidence Inspection</option>
            <option value="INITIALIZATION">System Initialization</option>
          </select>
        </div>

        <div>
          <label className="block text-[11px] font-mono text-slate-400 mb-1">Target Entity Type</label>
          <select
            value={targetTypeFilter}
            onChange={(e) => setTargetTypeFilter(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
          >
            <option value="">All Entities</option>
            <option value="ALERT">Analytical Signals & Alerts</option>
            <option value="PROJECT">Project Records</option>
            <option value="SYSTEM">System Configurations</option>
          </select>
        </div>

        <div className="flex items-end">
          <button
            onClick={() => { setActionFilter(''); setTargetTypeFilter(''); }}
            className="w-full py-1.5 px-3 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs font-mono transition-colors"
          >
            Reset Filters
          </button>
        </div>
      </div>

      {/* Audit Log Table */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
        {loading ? (
          <div className="p-6">
            <TableSkeleton rows={6} />
          </div>
        ) : logs.length === 0 ? (
          <div className="p-12 text-center text-slate-500 text-xs font-mono">
            No audit log records matching the specified filters.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/80 text-slate-400 font-mono uppercase text-[10px] border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4">Timestamp</th>
                  <th className="py-3 px-4">Actor / Role</th>
                  <th className="py-3 px-4">Action</th>
                  <th className="py-3 px-4">Target Entity</th>
                  <th className="py-3 px-4">Transition</th>
                  <th className="py-3 px-4">Remarks / Evidence</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-300">
                {logs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-3 px-4 font-mono text-[11px] text-slate-400 whitespace-nowrap">
                      {log.created_at || 'Recent'}
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-1.5">
                        <UserCheck className="w-3.5 h-3.5 text-indigo-400" />
                        <span className="font-medium text-slate-200">{log.username || 'System'}</span>
                        <span className="text-[10px] font-mono text-slate-500">({log.user_role || 'ADMIN'})</span>
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-mono border ${getActionBadgeColor(log.action)}`}>
                        {log.action}
                      </span>
                    </td>
                    <td className="py-3 px-4 font-mono text-[11px] text-indigo-300">
                      {log.target_type}: {log.target_id}
                    </td>
                    <td className="py-3 px-4 font-mono text-[11px]">
                      {log.previous_state ? (
                        <span className="flex items-center gap-1">
                          <span className="text-slate-500">{log.previous_state}</span>
                          <ArrowRight className="w-3 h-3 text-slate-600" />
                          <span className="text-emerald-400 font-bold">{log.new_state}</span>
                        </span>
                      ) : (
                        <span className="text-slate-400">{log.new_state || 'PROCESSED'}</span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-slate-400 max-w-xs truncate text-[11px]">
                      {log.notes || '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        {pagination.total_pages > 1 && (
          <div className="px-4 py-3 bg-slate-950/60 border-t border-slate-800 flex items-center justify-between text-xs font-mono text-slate-400">
            <span>
              Page {pagination.page} of {pagination.total_pages}
            </span>
            <div className="flex items-center gap-2">
              <button
                disabled={!pagination.has_prev}
                onClick={() => fetchLogs(pagination.page - 1)}
                className="px-3 py-1 rounded bg-slate-800 hover:bg-slate-700 disabled:opacity-40 transition-colors text-slate-200"
              >
                Previous
              </button>
              <button
                disabled={!pagination.has_next}
                onClick={() => fetchLogs(pagination.page + 1)}
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
