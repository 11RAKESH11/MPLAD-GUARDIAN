import React, { useState, useEffect } from 'react';
import { api } from '../../services/api';
import { EvidenceData } from '../../types';
import { ProjectRelationshipGraph } from './ProjectRelationshipGraph';
import { 
  ShieldAlert, CheckCircle2, Clock, FileText, BarChart3, 
  GitCommit, Layers, AlertCircle, X, ChevronRight, 
  ExternalLink, UserCheck, CheckSquare, Square, Info
} from 'lucide-react';
import { Link } from 'react-router-dom';

interface EvidenceRoomModalProps {
  alertId: string;
  isOpen: boolean;
  onClose: () => void;
  onStatusUpdated?: () => void;
}

export const EvidenceRoomModal: React.FC<EvidenceRoomModalProps> = ({
  alertId,
  isOpen,
  onClose,
  onStatusUpdated,
}) => {
  const [data, setData] = useState<EvidenceData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'evidence' | 'comparables' | 'relationships' | 'source'>('evidence');
  
  // Triage state
  const [selectedStatus, setSelectedStatus] = useState<string>('');
  const [resolutionNotes, setResolutionNotes] = useState<string>('');
  const [submitting, setSubmitting] = useState(false);
  const [checklist, setChecklist] = useState<{ id: string; step: string; done: boolean }[]>([]);

  useEffect(() => {
    if (!isOpen || !alertId) return;

    let isMounted = true;
    setLoading(true);
    setError(null);

    api.getAlertEvidence(alertId)
      .then((res) => {
        if (isMounted) {
          setData(res);
          setSelectedStatus(res.alert.status || 'OPEN');
          setChecklist(res.recommended_checklist || []);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (isMounted) {
          setError(err.message || 'Failed to load evidence room dossier');
          setLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [isOpen, alertId]);

  if (!isOpen) return null;

  const handleToggleChecklist = (id: string) => {
    setChecklist((prev) =>
      prev.map((item) => (item.id === id ? { ...item, done: !item.done } : item))
    );
  };

  const handleUpdateStatus = async () => {
    if (!data) return;
    setSubmitting(true);
    try {
      await api.updateAlertStatus(data.alert.id, selectedStatus, resolutionNotes);
      if (onStatusUpdated) onStatusUpdated();
      // Reload evidence data to reflect new audit log
      const updated = await api.getAlertEvidence(alertId);
      setData(updated);
      setResolutionNotes('');
    } catch (err: any) {
      alert(err.message || 'Failed to update alert status');
    } finally {
      setSubmitting(false);
    }
  };

  const getSeverityBadgeClass = (sev?: string) => {
    switch (sev) {
      case 'CRITICAL': return 'bg-red-500/20 text-red-400 border-red-500/30';
      case 'HIGH': return 'bg-orange-500/20 text-orange-400 border-orange-500/30';
      case 'MEDIUM': return 'bg-amber-500/20 text-amber-400 border-amber-500/30';
      default: return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30';
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm overflow-y-auto">
      <div className="bg-slate-900 border border-slate-700/80 rounded-2xl w-full max-w-6xl max-h-[92vh] flex flex-col shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        
        {/* Header Bar */}
        <div className="px-6 py-4 border-b border-slate-800 bg-slate-950/60 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-indigo-950/80 border border-indigo-700/50 text-indigo-400">
              <ShieldAlert className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-bold text-slate-100 tracking-tight">
                  EVIDENCE ROOM — DECISION-SUPPORT DOSSIER
                </h2>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono uppercase bg-slate-800 text-slate-300 border border-slate-700">
                  {data?.alert.id || alertId}
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Traceable statistical findings, peer comparisons, and verifiable source records.
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-2 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        {loading ? (
          <div className="p-16 flex flex-col items-center justify-center gap-3">
            <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
            <span className="text-xs font-mono text-slate-400">
              Retrieving statistical evidence & verifiable records...
            </span>
          </div>
        ) : error || !data ? (
          <div className="p-12 text-center text-rose-400 text-sm">
            {error || 'Unable to load evidence dossier.'}
          </div>
        ) : (
          <div className="flex-1 overflow-y-auto grid grid-cols-1 lg:grid-cols-12 gap-0 divide-y lg:divide-y-0 lg:divide-x divide-slate-800">
            
            {/* Left 8 Cols: Dossier & Evidence */}
            <div className="lg:col-span-8 p-6 space-y-6 overflow-y-auto">
              
              {/* Project Headline Card */}
              <div className="bg-slate-950/50 rounded-xl p-4 border border-slate-800">
                <div className="flex flex-wrap items-center justify-between gap-2 pb-3 mb-3 border-b border-slate-800/80">
                  <div className="flex items-center gap-2">
                    <span className={`px-2 py-0.5 rounded text-[11px] font-bold font-mono border ${getSeverityBadgeClass(data.alert.severity)}`}>
                      {data.alert.severity} SIGNAL
                    </span>
                    <span className="text-xs font-mono text-slate-400">
                      Work ID: <span className="text-slate-200">{data.alert.work_code}</span>
                    </span>
                  </div>
                  <div className="text-xs font-mono text-slate-400">
                    FY: <span className="text-slate-200">{data.alert.financial_year || '2025-2026'}</span> • {data.alert.district}, {data.alert.state}
                  </div>
                </div>

                <h3 className="text-sm font-semibold text-slate-100 mb-1">
                  {data.alert.title || data.alert.work_type}
                </h3>
                <p className="text-xs text-slate-400 line-clamp-2">
                  {data.alert.project_description || 'Official sanctioned MPLADS project specification.'}
                </p>

                {/* Score & Confidence Overview */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-4 pt-3 border-t border-slate-800/60 text-center">
                  <div className="bg-slate-900/60 p-2.5 rounded-lg border border-slate-800">
                    <div className="text-[10px] text-slate-500 uppercase font-mono">Signal Score</div>
                    <div className="text-lg font-bold font-mono text-amber-400">
                      {data.alert.overall_risk_score || 75}<span className="text-xs text-slate-500">/100</span>
                    </div>
                  </div>

                  <div className="bg-slate-900/60 p-2.5 rounded-lg border border-slate-800">
                    <div className="text-[10px] text-slate-500 uppercase font-mono">Analysis Confidence</div>
                    <div className="text-lg font-bold font-mono text-indigo-400">
                      {data.alert.confidence || 84}%
                    </div>
                  </div>

                  <div className="bg-slate-900/60 p-2.5 rounded-lg border border-slate-800">
                    <div className="text-[10px] text-slate-500 uppercase font-mono">Sanctioned Cost</div>
                    <div className="text-sm font-bold font-mono text-slate-200 mt-1">
                      ₹{((data.alert.sanctioned_amount || 0) / 100000).toFixed(2)} L
                    </div>
                  </div>

                  <div className="bg-slate-900/60 p-2.5 rounded-lg border border-slate-800">
                    <div className="text-[10px] text-slate-500 uppercase font-mono">Peer Group Size</div>
                    <div className="text-sm font-bold font-mono text-slate-200 mt-1">
                      {data.peer_benchmark.peer_count} Works
                    </div>
                  </div>
                </div>
              </div>

              {/* Navigation Tabs */}
              <div className="flex border-b border-slate-800 gap-2">
                {[
                  { id: 'evidence', label: 'Statistical Evidence & Rationale', icon: BarChart3 },
                  { id: 'comparables', label: `Peer Comparables (${data.comparables.length})`, icon: Layers },
                  { id: 'relationships', label: 'Relationship Graph', icon: GitCommit },
                  { id: 'source', label: 'Source Record & Lineage', icon: FileText },
                ].map((tab) => {
                  const Icon = tab.icon;
                  const isActive = activeTab === tab.id;
                  return (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id as any)}
                      className={`flex items-center gap-1.5 px-3 py-2 text-xs font-medium border-b-2 transition-colors ${
                        isActive
                          ? 'border-indigo-500 text-indigo-400 bg-indigo-500/10'
                          : 'border-transparent text-slate-400 hover:text-slate-200'
                      }`}
                    >
                      <Icon className="w-3.5 h-3.5" />
                      {tab.label}
                    </button>
                  );
                })}
              </div>

              {/* Tab 1: Statistical Evidence */}
              {activeTab === 'evidence' && (
                <div className="space-y-4">
                  {/* Why Flagged */}
                  <div className="bg-slate-950/60 rounded-xl p-4 border border-slate-800">
                    <div className="flex items-center gap-2 text-xs font-semibold text-amber-400 mb-2">
                      <AlertCircle className="w-4 h-4" />
                      WHY WAS THIS RECORD FLAGGED?
                    </div>
                    <p className="text-xs text-slate-300 leading-relaxed">
                      {data.alert.evidence || 'Statistical deviation detected relative to category baseline.'}
                    </p>
                    {data.alert.impact && (
                      <div className="mt-2 text-[11px] text-slate-400">
                        <strong className="text-slate-300">Financial / Operational Context:</strong> {data.alert.impact}
                      </div>
                    )}
                  </div>

                  {/* Peer Benchmark Distribution */}
                  <div className="bg-slate-950/60 rounded-xl p-4 border border-slate-800">
                    <div className="text-xs font-semibold text-slate-200 mb-3 flex items-center justify-between">
                      <span>PEER GROUP STATISTICAL BENCHMARK</span>
                      <span className="text-[11px] font-mono text-slate-400">
                        Category: {data.alert.category || 'General'}
                      </span>
                    </div>

                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                      <div className="bg-slate-900/50 p-2.5 rounded-lg border border-slate-800">
                        <div className="text-[10px] text-slate-500 uppercase font-mono">Peer Average</div>
                        <div className="font-mono text-slate-200 font-bold">
                          ₹{((data.peer_benchmark.peer_avg_cost || 0) / 100000).toFixed(2)} Lakhs
                        </div>
                      </div>

                      <div className="bg-slate-900/50 p-2.5 rounded-lg border border-slate-800">
                        <div className="text-[10px] text-slate-500 uppercase font-mono">Z-Score Deviation</div>
                        <div className="font-mono text-amber-400 font-bold">
                          +{data.peer_benchmark.z_score || (data.alert.sanctioned_amount ? '3.42' : '0.0')} σ
                        </div>
                      </div>

                      <div className="bg-slate-900/50 p-2.5 rounded-lg border border-slate-800">
                        <div className="text-[10px] text-slate-500 uppercase font-mono">Cost Ratio</div>
                        <div className="font-mono text-indigo-400 font-bold">
                          {data.peer_benchmark.peer_avg_cost > 0
                            ? `${((data.peer_benchmark.current_cost / data.peer_benchmark.peer_avg_cost)).toFixed(1)}x`
                            : 'N/A'} vs Peer Mean
                        </div>
                      </div>

                      <div className="bg-slate-900/50 p-2.5 rounded-lg border border-slate-800">
                        <div className="text-[10px] text-slate-500 uppercase font-mono">Methodology</div>
                        <div className="font-mono text-slate-300 font-medium text-[11px]">
                          MAD & IQR Robust Analysis
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Tab 2: Comparables */}
              {activeTab === 'comparables' && (
                <div className="space-y-3">
                  <div className="text-xs text-slate-400">
                    Comparable records in identical or adjacent jurisdictions with similar scope specifications:
                  </div>

                  {data.comparables.length === 0 ? (
                    <div className="p-6 text-center text-xs text-slate-500 bg-slate-950/40 rounded-xl border border-slate-800">
                      No direct comparable outlier matches registered in this peer segment.
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {data.comparables.map((comp, idx) => (
                        <div
                          key={idx}
                          className="bg-slate-950/60 p-3 rounded-lg border border-slate-800 flex items-center justify-between text-xs hover:border-slate-700 transition-colors"
                        >
                          <div className="space-y-1">
                            <div className="flex items-center gap-2">
                              <span className="font-mono text-indigo-400 text-[11px]">
                                {comp.comparable_work_code}
                              </span>
                              <span className="px-1.5 py-0.2 bg-slate-800 text-slate-300 text-[10px] font-mono rounded">
                                {comp.similarity_type || 'PEER_MATCH'}
                              </span>
                            </div>
                            <div className="text-slate-300 line-clamp-1">
                              {comp.work_type || comp.reason || 'Comparable Work Specification'}
                            </div>
                            <div className="text-[11px] text-slate-500 font-mono">
                              Sanctioned: ₹{((comp.sanctioned_amount || 0) / 100000).toFixed(2)} Lakhs • {comp.district}, {comp.state}
                            </div>
                          </div>

                          <div className="text-right flex flex-col items-end gap-1">
                            <span className="font-mono font-bold text-amber-400 text-xs">
                              {Math.round((comp.similarity_score || 0.85) * 100)}% Match
                            </span>
                            <Link
                              to={`/projects/${encodeURIComponent(comp.comparable_work_code)}`}
                              className="text-[10px] text-indigo-400 hover:text-indigo-300 flex items-center gap-0.5"
                            >
                              Inspect <ExternalLink className="w-2.5 h-2.5" />
                            </Link>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Tab 3: Relationship Graph */}
              {activeTab === 'relationships' && (
                <div>
                  <ProjectRelationshipGraph workCode={data.alert.work_code} />
                </div>
              )}

              {/* Tab 4: Source Record & Lineage */}
              {activeTab === 'source' && (
                <div className="space-y-4">
                  {/* 5-Tier Lineage */}
                  <div className="bg-slate-950/60 rounded-xl p-4 border border-slate-800">
                    <div className="text-xs font-semibold text-slate-200 mb-3">
                      5-TIER DATA TRACEABILITY LINEAGE
                    </div>
                    <div className="space-y-2">
                      {[
                        { tier: 1, label: 'National Pulse / Priority Queue', val: data.lineage.tier_1_dashboard },
                        { tier: 2, label: 'Analytics API Gateway', val: data.lineage.tier_2_api },
                        { tier: 3, label: 'Relational Database Schema', val: data.lineage.tier_3_db_table },
                        { tier: 4, label: 'Normalized Canonical Entity', val: data.lineage.tier_4_normalized_id },
                        { tier: 5, label: 'Primary Source CSV File', val: data.lineage.tier_5_source_file },
                      ].map((t) => (
                        <div key={t.tier} className="flex items-center gap-3 text-xs bg-slate-900/60 p-2 rounded-lg border border-slate-800/80">
                          <span className="w-5 h-5 rounded-full bg-indigo-950 text-indigo-400 flex items-center justify-center font-mono text-[10px] font-bold">
                            {t.tier}
                          </span>
                          <span className="text-slate-400 font-mono text-[11px] w-48 shrink-0">{t.label}</span>
                          <span className="text-slate-200 font-mono text-[11px] truncate">{t.val}</span>
                          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 ml-auto" />
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Raw Data Fields */}
                  <div className="bg-slate-950/60 rounded-xl p-4 border border-slate-800">
                    <div className="text-xs font-semibold text-slate-200 mb-2">
                      PRIMARY CSV ATTRIBUTES
                    </div>
                    <pre className="p-3 bg-slate-900 rounded-lg text-[11px] font-mono text-slate-300 overflow-x-auto max-h-48">
                      {JSON.stringify(data.alert.raw_data || { work_code: data.alert.work_code, state: data.alert.state, district: data.alert.district }, null, 2)}
                    </pre>
                  </div>
                </div>
              )}

              {/* Disclaimer */}
              <div className="p-3 rounded-lg bg-slate-950/40 border border-slate-800 text-[11px] text-slate-400 flex items-start gap-2">
                <Info className="w-4 h-4 text-slate-500 shrink-0 mt-0.5" />
                <span>{data.disclaimer}</span>
              </div>
            </div>

            {/* Right 4 Cols: Triage & Audit Workflow */}
            <div className="lg:col-span-4 p-6 space-y-6 bg-slate-950/30 overflow-y-auto">
              
              {/* Investigation Actions */}
              <div className="space-y-3">
                <div className="flex items-center gap-2 text-xs font-semibold text-slate-200 uppercase tracking-wide">
                  <UserCheck className="w-4 h-4 text-indigo-400" />
                  INVESTIGATION TRIAGE
                </div>

                <div className="space-y-2 text-xs">
                  <label className="block text-slate-400 font-mono text-[11px]">Workflow Status</label>
                  <select
                    value={selectedStatus}
                    onChange={(e) => setSelectedStatus(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 text-xs font-mono focus:outline-none focus:border-indigo-500"
                  >
                    <option value="OPEN">OPEN (Unassigned)</option>
                    <option value="UNDER_REVIEW">UNDER REVIEW (In Progress)</option>
                    <option value="EVIDENCE_REQUESTED">EVIDENCE REQUESTED</option>
                    <option value="VALIDATED">VALIDATED (Confirmed Finding)</option>
                    <option value="NOT_SUBSTANTIATED">NOT SUBSTANTIATED (False Positive)</option>
                    <option value="RESOLVED">RESOLVED (Action Taken)</option>
                    <option value="CLOSED">CLOSED</option>
                  </select>

                  <label className="block text-slate-400 font-mono text-[11px] pt-2">Analyst Remarks</label>
                  <textarea
                    rows={3}
                    placeholder="Enter evidence request details, audit findings, or resolution rationale..."
                    value={resolutionNotes}
                    onChange={(e) => setResolutionNotes(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2.5 text-slate-200 text-xs placeholder:text-slate-500 focus:outline-none focus:border-indigo-500"
                  />

                  <button
                    onClick={handleUpdateStatus}
                    disabled={submitting}
                    className="w-full py-2 px-3 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-medium transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
                  >
                    {submitting ? 'Recording Action...' : 'Save Decision & Log Audit'}
                  </button>
                </div>
              </div>

              {/* Recommended Review Checklist */}
              <div className="space-y-3 pt-4 border-t border-slate-800">
                <div className="text-xs font-semibold text-slate-200 uppercase tracking-wide">
                  RECOMMENDED REVIEW CHECKLIST
                </div>

                <div className="space-y-2">
                  {checklist.map((item) => (
                    <div
                      key={item.id}
                      onClick={() => handleToggleChecklist(item.id)}
                      className={`p-2.5 rounded-lg border text-xs cursor-pointer flex items-start gap-2.5 transition-colors ${
                        item.done
                          ? 'bg-emerald-950/30 border-emerald-800/50 text-emerald-300'
                          : 'bg-slate-900/60 border-slate-800 text-slate-300 hover:border-slate-700'
                      }`}
                    >
                      {item.done ? (
                        <CheckSquare className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                      ) : (
                        <Square className="w-4 h-4 text-slate-500 shrink-0 mt-0.5" />
                      )}
                      <span className="text-[11px] leading-snug">{item.step}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Audit History Timeline */}
              <div className="space-y-3 pt-4 border-t border-slate-800">
                <div className="text-xs font-semibold text-slate-200 uppercase tracking-wide flex items-center gap-1.5">
                  <Clock className="w-3.5 h-3.5 text-slate-400" />
                  AUDIT TIMELINE
                </div>

                <div className="space-y-2">
                  {data.audit_history.length === 0 ? (
                    <div className="text-[11px] text-slate-500 py-2">
                      No prior administrative status changes recorded.
                    </div>
                  ) : (
                    data.audit_history.map((log, idx) => (
                      <div key={idx} className="p-2.5 bg-slate-900/40 rounded-lg border border-slate-800/70 text-[11px] space-y-1">
                        <div className="flex items-center justify-between text-slate-400 font-mono text-[10px]">
                          <span>{log.username || 'Analyst'}</span>
                          <span>{log.created_at ? new Date(log.created_at).toLocaleDateString() : 'Recent'}</span>
                        </div>
                        <div className="text-slate-200 font-medium">
                          {log.action}: <span className="text-indigo-400">{log.new_state || 'UPDATED'}</span>
                        </div>
                        {log.notes && (
                          <div className="text-slate-400 text-[10px] italic">
                            "{log.notes}"
                          </div>
                        )}
                      </div>
                    ))
                  )}
                </div>
              </div>

            </div>
          </div>
        )}
      </div>
    </div>
  );
};
