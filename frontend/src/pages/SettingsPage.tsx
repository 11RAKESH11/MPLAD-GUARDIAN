import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { SourceBadge } from '../components/common/SourceBadge';
import { formatDate } from '../lib/utils';
import { History, Cpu, Server } from 'lucide-react';

export const SettingsPage: React.FC = () => {
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getAuditLogs({ limit: 30 }).then((res) => {
      setLogs(res.logs);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-[#E5E7EB]">
        <div>
          <h2 className="text-xl lg:text-2xl font-extrabold text-[#172033] tracking-tight font-display">
            System Configuration & Governance Lineage
          </h2>
          <p className="text-xs text-[#667085] mt-0.5">
            AI engine parameters, analytical weights, and institutional audit trail
          </p>
        </div>

        <SourceBadge type="REAL SOURCE DATA" />
      </div>

      {/* Model Parameters Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="gov-card p-6 space-y-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded bg-[#EDF8F8] text-[#147A73]">
              <Cpu className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-[#172033] font-display uppercase">
                AI Composite Risk Model (v1.0)
              </h3>
              <p className="text-xs text-[#667085]">Normalized multi-factor analytical weights</p>
            </div>
          </div>

          <div className="space-y-2.5 text-xs pt-2">
            <div className="flex items-center justify-between p-2.5 bg-[#F7F8F6] rounded border border-[#E5E7EB]">
              <span className="text-[#667085]">Cost Anomaly Weight</span>
              <strong className="text-[#C27A00] font-mono">30% (MAD + Z-Score)</strong>
            </div>
            <div className="flex items-center justify-between p-2.5 bg-[#F7F8F6] rounded border border-[#E5E7EB]">
              <span className="text-[#667085]">Duplicate Similarity Weight</span>
              <strong className="text-[#147A73] font-mono">30% (TF-IDF Cosine)</strong>
            </div>
            <div className="flex items-center justify-between p-2.5 bg-[#F7F8F6] rounded border border-[#E5E7EB]">
              <span className="text-[#667085]">Progress Gap Weight</span>
              <strong className="text-[#102A43] font-mono">25% (Milestone Rules)</strong>
            </div>
            <div className="flex items-center justify-between p-2.5 bg-[#F7F8F6] rounded border border-[#E5E7EB]">
              <span className="text-[#667085]">Geographic Concentration</span>
              <strong className="text-[#667085] font-mono">15% (Spatial Density)</strong>
            </div>
          </div>
        </div>

        <div className="gov-card p-6 space-y-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded bg-[#F0F4F8] text-[#102A43]">
              <Server className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-[#172033] font-display uppercase">
                Database & Ingestion Layer
              </h3>
              <p className="text-xs text-[#667085]">PostgreSQL / SQLite High-Performance Storage Engine</p>
            </div>
          </div>

          <div className="space-y-2.5 text-xs pt-2">
            <div className="flex items-center justify-between p-2.5 bg-[#F7F8F6] rounded border border-[#E5E7EB]">
              <span className="text-[#667085]">Indexed Projects</span>
              <strong className="text-[#172033] font-mono">96,654 lifecycles</strong>
            </div>
            <div className="flex items-center justify-between p-2.5 bg-[#F7F8F6] rounded border border-[#E5E7EB]">
              <span className="text-[#667085]">Expenditure Vouchers</span>
              <strong className="text-[#172033] font-mono">106,442 records</strong>
            </div>
            <div className="flex items-center justify-between p-2.5 bg-[#F7F8F6] rounded border border-[#E5E7EB]">
              <span className="text-[#667085]">Parliamentarian Portfolios</span>
              <strong className="text-[#172033] font-mono">764 MPs (LS + RS)</strong>
            </div>
            <div className="flex items-center justify-between p-2.5 bg-[#F7F8F6] rounded border border-[#E5E7EB]">
              <span className="text-[#667085]">Storage Engine</span>
              <strong className="text-[#102A43] font-mono">mplad.db (WAL Mode)</strong>
            </div>
          </div>
        </div>
      </div>

      {/* Audit Logs Table */}
      <div className="gov-card p-6 space-y-4 shadow-card">
        <div className="flex items-center justify-between pb-3 border-b border-[#E5E7EB]">
          <div className="flex items-center gap-2">
            <History className="w-4 h-4 text-[#102A43]" />
            <h3 className="text-sm font-bold font-sans uppercase tracking-wide text-[#172033]">
              System Audit Trail & Governance Action Log
            </h3>
          </div>
          <span className="text-xs font-mono text-[#667085]">Immutable Audit Log</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#F7F8F6] border-b border-[#E5E7EB] text-[#667085] font-sans font-bold uppercase text-[11px]">
              <tr>
                <th className="p-3">Timestamp</th>
                <th className="p-3">User</th>
                <th className="p-3">Role</th>
                <th className="p-3">Action</th>
                <th className="p-3">Target</th>
                <th className="p-3">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E5E7EB]">
              {logs.map((log, idx) => (
                <tr key={idx} className="hover:bg-[#F7F8F6]">
                  <td className="p-3 text-[#667085] font-mono">{formatDate(log.created_at)}</td>
                  <td className="p-3 font-semibold text-[#172033]">{log.user_name}</td>
                  <td className="p-3">
                    <span className="px-2 py-0.5 rounded text-[10px] bg-[#F0F4F8] text-[#102A43] border border-[#D9E2EC] font-semibold">
                      {log.user_role}
                    </span>
                  </td>
                  <td className="p-3 font-semibold text-[#C27A00]">{log.action}</td>
                  <td className="p-3 text-[#667085] font-mono">{log.target_id || log.target_type}</td>
                  <td className="p-3 text-[#667085] max-w-md truncate">{log.details}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
