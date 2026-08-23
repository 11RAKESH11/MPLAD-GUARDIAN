import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { DataQualitySummary } from '../types';
import { SourceBadge } from '../components/common/SourceBadge';
import { CardSkeleton } from '../components/common/LoadingSkeleton';
import { formatNumber } from '../lib/utils';
import { ShieldCheck, CheckCircle2, FileCheck, Layers, AlertTriangle } from 'lucide-react';

export const DataQualityPage: React.FC = () => {
  const [data, setData] = useState<DataQualitySummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getDataQualitySummary().then((res) => {
      setData(res);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  if (loading || !data) {
    return (
      <div className="space-y-6">
        <div className="h-16 bg-white rounded animate-pulse border border-[#E5E7EB]" />
        <CardSkeleton count={4} />
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-xl lg:text-2xl font-extrabold text-[#172033] tracking-tight font-display">
            Data Quality & Source Integrity Center
          </h2>
          <p className="text-xs text-[#667085] mt-0.5">
            Validation metrics, field completeness rates, and raw anomaly audit registry across 374,141 records
          </p>
        </div>

        <SourceBadge type="REAL SOURCE DATA" />
      </div>

      {/* Health Gauges Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <div className="gov-card p-5 space-y-2">
          <div className="flex items-center justify-between text-xs text-[#667085] font-medium">
            <span>OVERALL HEALTH</span>
            <CheckCircle2 className="w-4 h-4 text-[#14804A]" />
          </div>
          <div className="text-3xl font-extrabold font-display text-[#14804A]">
            {data.overall_health_score}%
          </div>
          <div className="text-[11px] text-[#667085]">
            {formatNumber(data.metrics.total_records_monitored)} Monitored Records
          </div>
        </div>

        <div className="gov-card p-5 space-y-2">
          <div className="flex items-center justify-between text-xs text-[#667085] font-medium">
            <span>FIELD COMPLETENESS</span>
            <FileCheck className="w-4 h-4 text-[#102A43]" />
          </div>
          <div className="text-3xl font-extrabold font-display text-[#102A43]">
            {data.completeness_pct}%
          </div>
          <div className="text-[11px] text-[#667085]">
            Across 6 Critical Normalized Attributes
          </div>
        </div>

        <div className="gov-card p-5 space-y-2">
          <div className="flex items-center justify-between text-xs text-[#667085] font-medium">
            <span>SCHEMA VALIDITY</span>
            <ShieldCheck className="w-4 h-4 text-[#147A73]" />
          </div>
          <div className="text-3xl font-extrabold font-display text-[#147A73]">
            {data.validity_pct}%
          </div>
          <div className="text-[11px] text-[#667085]">
            Zero Discarded Records
          </div>
        </div>

        <div className="gov-card p-5 space-y-2">
          <div className="flex items-center justify-between text-xs text-[#667085] font-medium">
            <span>CROSS-LINK INTEGRITY</span>
            <Layers className="w-4 h-4 text-[#C27A00]" />
          </div>
          <div className="text-3xl font-extrabold font-display text-[#C27A00]">
            {data.cross_linkage_pct}%
          </div>
          <div className="text-[11px] text-[#667085]">
            Sanctioned ↔ Completed ↔ Expenditure
          </div>
        </div>
      </div>

      {/* Quality Matrix (Section 25) */}
      <div className="gov-card p-6 space-y-4 shadow-card">
        <div className="flex items-center justify-between pb-3 border-b border-[#E5E7EB]">
          <div>
            <h3 className="text-sm font-bold font-sans uppercase tracking-wide text-[#172033]">
              Quality Assurance & Field Validation Matrix
            </h3>
            <p className="text-xs text-[#667085]">Monitored data attributes, error thresholds, and handling status</p>
          </div>
          <span className="text-xs font-mono text-[#667085]">Audited Ingestion Log</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#F7F8F6] border-b border-[#E5E7EB] text-[#667085] font-sans font-bold uppercase text-[11px]">
              <tr>
                <th className="p-3">Issue Category</th>
                <th className="p-3">Severity</th>
                <th className="p-3">Source Dataset File</th>
                <th className="p-3">Target Field</th>
                <th className="p-3">Sample Value</th>
                <th className="p-3">Handling Resolution</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E5E7EB]">
              {data.issues_registry?.map((issue) => (
                <tr key={issue.id} className="hover:bg-[#F7F8F6]">
                  <td className="p-3 font-bold text-[#C27A00]">{issue.issue_type}</td>
                  <td className="p-3">
                    <span className="px-2 py-0.5 rounded text-[10px] bg-[#F0F2ED] text-[#667085] border border-[#E5E7EB]">
                      {issue.severity}
                    </span>
                  </td>
                  <td className="p-3 text-[#102A43] font-medium">{issue.file_name}</td>
                  <td className="p-3 text-[#667085] font-mono">{issue.field_name}</td>
                  <td className="p-3 text-[#C2413B] font-mono max-w-xs truncate">{issue.invalid_value}</td>
                  <td className="p-3 text-[#667085] max-w-sm">{issue.description}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
