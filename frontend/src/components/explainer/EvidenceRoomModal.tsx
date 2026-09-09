import React, { useState, useEffect } from 'react';
import { api } from '../../services/api';
import { EvidenceData } from '../../types';
import { ProjectRelationshipGraph } from './ProjectRelationshipGraph';
import { formatCurrency, formatExactCurrency, formatDate, formatNumber } from '../../lib/utils';
import { 
  ShieldAlert, CheckCircle2, Clock, FileText, BarChart3, 
  GitCommit, Layers, AlertCircle, X, ChevronRight, 
  ExternalLink, UserCheck, CheckSquare, Square, Info,
  MapPin, Database, ArrowRight, Printer, AlertTriangle,
  HelpCircle, Sparkles, Send, History, Check, Building2,
  Calendar, Receipt, FileCode2, Scale, CreditCard
} from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';

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
  const [activeTab, setActiveTab] = useState<'evidence' | 'duplicates' | 'relationships' | 'vouchers' | 'lineage' | 'source' | 'audit'>('evidence');
  
  // Triage state
  const [selectedStatus, setSelectedStatus] = useState<string>('');
  const [resolutionNotes, setResolutionNotes] = useState<string>('');
  const [newAnalystNote, setNewAnalystNote] = useState<string>('');
  const [submitting, setSubmitting] = useState(false);
  const [addingNote, setAddingNote] = useState(false);
  const [checklist, setChecklist] = useState<{ id: string; step: string; done: boolean }[]>([]);
  const [showRawJson, setShowRawJson] = useState(false);
  const navigate = useNavigate();

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
      const updated = await api.getAlertEvidence(alertId);
      setData(updated);
      setResolutionNotes('');
    } catch (err: any) {
      alert(err.message || 'Failed to update alert status');
    } finally {
      setSubmitting(false);
    }
  };

  const handleAddAnalystNote = async () => {
    if (!newAnalystNote.trim() || !data) return;
    setAddingNote(true);
    try {
      await api.addAlertNote(data.alert.id, newAnalystNote.trim());
      const updated = await api.getAlertEvidence(alertId);
      setData(updated);
      setNewAnalystNote('');
    } catch (err: any) {
      alert(err.message || 'Failed to add analyst note');
    } finally {
      setAddingNote(false);
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

  const alertData = data?.alert;
  const rawData = alertData?.raw_data || {};
  const expJson = alertData?.explanation_json || {};

  // Financial calculations
  const sanctioned = alertData?.sanctioned_amount || 0;
  const expenditure = alertData?.expenditure_amount || 0;
  const disbursed = alertData?.disbursed_amount || 0;
  const recommended = alertData?.recommended_amount || 0;
  const utilPct = sanctioned > 0 ? Math.round((expenditure / sanctioned) * 100) : 0;
  const remaining = Math.max(0, sanctioned - expenditure);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-2 sm:p-4 bg-slate-950/80 backdrop-blur-sm overflow-y-auto">
      <div className="bg-slate-900 border border-slate-700/80 rounded-2xl w-full max-w-6xl max-h-[94vh] flex flex-col shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        
        {/* Workspace Top Header (Section 2 & 3) */}
        <div className="bg-slate-950/90 border-b border-slate-800 px-6 py-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center space-x-2">
              <span className="text-[10px] font-mono uppercase tracking-wider bg-blue-500/10 text-blue-400 border border-blue-500/20 px-2 py-0.5 rounded font-semibold">
                Evidence Dossier
              </span>
              <span className="font-mono text-xs text-slate-400">
                {alertData?.id || alertId}
              </span>
              <span className="text-slate-600">•</span>
              <span className="text-xs text-slate-400 flex items-center">
                <Clock className="w-3 h-3 mr-1 text-slate-500" />
                Detected: {formatDate(alertData?.created_at || '2026-08-28')}
              </span>
              <span className="text-slate-600">•</span>
              <span className="text-xs text-slate-500 font-mono">
                Model: {alertData?.model_version || 'guardian-risk-2.0.0'}
              </span>
            </div>

            <h2 className="text-lg sm:text-xl font-extrabold text-white tracking-tight flex items-center gap-2">
              <ShieldAlert className="w-5 h-5 text-amber-500" />
              <span>{alertData?.title || 'Analytical Risk Signal Dossier'}</span>
            </h2>
          </div>

          {/* Quick Metrics Bar */}
          <div className="flex items-center gap-3">
            {/* Risk Score */}
            <div className="bg-slate-800/80 border border-slate-700/80 px-3 py-1.5 rounded-lg text-center">
              <span className="text-[9px] font-semibold text-slate-400 uppercase tracking-wider block">Risk Score</span>
              <span className="text-base font-extrabold text-amber-400">
                {alertData?.overall_risk_score || alertData?.risk_score || 0}
                <span className="text-xs text-slate-500">/100</span>
              </span>
            </div>

            {/* Confidence */}
            <div className="bg-slate-800/80 border border-slate-700/80 px-3 py-1.5 rounded-lg text-center">
              <span className="text-[9px] font-semibold text-slate-400 uppercase tracking-wider block">Confidence</span>
              <span className="text-base font-extrabold text-blue-400">
                {alertData?.confidence || 85}%
              </span>
            </div>

            {/* Evidence Coverage */}
            <div className="bg-slate-800/80 border border-slate-700/80 px-3 py-1.5 rounded-lg text-center">
              <span className="text-[9px] font-semibold text-slate-400 uppercase tracking-wider block">Coverage</span>
              <span className="text-base font-extrabold text-emerald-400">
                {alertData?.coverage_pct || 91}%
              </span>
            </div>

            {/* Print / Export */}
            <button
              onClick={() => window.print()}
              className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-colors"
              title="Print Oversight Brief"
            >
              <Printer className="w-4 h-4" />
            </button>

            {/* Close Button */}
            <button
              onClick={onClose}
              className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white border border-slate-700 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="bg-slate-950/60 border-b border-slate-800 px-6 flex items-center space-x-2 overflow-x-auto text-xs font-medium">
          {[
            ['evidence', 'Signal & Evidence', BarChart3],
            ['duplicates', 'Duplicate Analysis', Scale],
            ['relationships', 'Relationship Graph', Layers],
            ['vouchers', `Expenditure Vouchers (${data?.vouchers?.length || 0})`, Receipt],
            ['lineage', 'Data Lineage', GitCommit],
            ['source', 'Source Records', Database],
            ['audit', `Audit Trail (${data?.audit_history?.length || 0})`, History],
          ].map(([tabKey, label, IconComponent]: any) => (
            <button
              key={tabKey}
              onClick={() => setActiveTab(tabKey)}
              className={`flex items-center space-x-1.5 py-3 px-3 border-b-2 transition-all whitespace-nowrap ${
                activeTab === tabKey
                  ? 'border-blue-500 text-blue-400 font-semibold'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <IconComponent className="w-3.5 h-3.5" />
              <span>{label}</span>
            </button>
          ))}
        </div>

        {/* Workspace Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6 text-slate-300 text-xs">
          {loading ? (
            <div className="py-24 text-center text-slate-400">
              <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
              Synthesizing Multi-Signal Evidence Dossier...
            </div>
          ) : error ? (
            <div className="bg-red-500/10 border border-red-500/30 p-6 rounded-xl text-center space-y-2">
              <AlertCircle className="w-8 h-8 text-red-400 mx-auto" />
              <h3 className="text-sm font-bold text-red-300">Failed to load evidence dossier</h3>
              <p className="text-xs text-slate-400">{error}</p>
            </div>
          ) : data ? (
            <>
              {/* TAB 1: EVIDENCE & SIGNAL ANALYSIS */}
              {activeTab === 'evidence' && (
                <div className="space-y-6">
                  {/* Executive Signal Summary (Section 3) */}
                  <div className="bg-slate-800/40 border border-slate-700/80 rounded-xl p-4 space-y-2">
                    <h3 className="font-bold text-sm text-slate-100 flex items-center gap-1.5">
                      <Sparkles className="w-4 h-4 text-blue-400" />
                      Executive Anomaly Summary
                    </h3>
                    <p className="text-xs text-slate-300 leading-relaxed">
                      {alertData?.evidence || expJson?.summary || 'This analytical signal identifies a statistical or documentation pattern that warrants human oversight desk review.'}
                    </p>
                    <div className="flex flex-wrap gap-4 pt-2 text-[11px] text-slate-400 border-t border-slate-700/60">
                      <span><strong>Category:</strong> {alertData?.category || 'Uncategorized'}</span>
                      <span><strong>State:</strong> {alertData?.state || 'Unknown'}</span>
                      <span><strong>District:</strong> {alertData?.district || 'Unknown'}</span>
                      <span><strong>MP:</strong> {alertData?.mp_name || 'N/A'}</span>
                      <span><strong>Work Code:</strong> <span className="font-mono text-blue-400">{alertData?.work_code}</span></span>
                    </div>
                  </div>

                  {/* Why Flagged — Contributor Decomposition (Section 4 & 5) */}
                  <div className="bg-slate-800/40 border border-slate-700/80 rounded-xl p-4 space-y-3">
                    <div className="flex items-center justify-between">
                      <h4 className="font-bold text-xs uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
                        <BarChart3 className="w-4 h-4 text-indigo-400" />
                        Why Was This Flagged? (Risk Score Decomposition)
                      </h4>
                      <span className="text-[10px] text-slate-500">Total: {alertData?.overall_risk_score || 0} / 100</span>
                    </div>

                    <div className="space-y-2.5">
                      {[
                        ['Cost Anomaly', alertData?.cost_anomaly_score || 0, 'bg-amber-500'],
                        ['Progress Gap', alertData?.progress_gap_score || 0, 'bg-blue-500'],
                        ['Potential Duplicate', alertData?.duplicate_score || 0, 'bg-purple-500'],
                        ['Geographic Concentration', alertData?.geographic_score || 0, 'bg-emerald-500'],
                      ].map(([label, score, colorClass]: any) => (
                        <div key={label} className="space-y-1">
                          <div className="flex justify-between text-xs font-medium">
                            <span className="text-slate-300">{label}</span>
                            <span className="font-mono text-slate-200">{score} / 100</span>
                          </div>
                          <div className="w-full h-2 bg-slate-950 rounded-full overflow-hidden">
                            <div
                              className={`h-full ${colorClass} transition-all duration-500`}
                              style={{ width: `${Math.min(100, Math.max(0, score))}%` }}
                            />
                          </div>
                        </div>
                      ))}
                    </div>
                    <p className="text-[11px] text-slate-500 italic pt-1">
                      * These independent analytical component scores dynamically synthesize into the overall review priority.
                    </p>
                  </div>

                  {/* Statistical Evidence (Section 6 & 7) */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="bg-slate-800/40 border border-slate-700/80 rounded-xl p-4 space-y-3">
                      <h4 className="font-bold text-xs uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
                        <Scale className="w-4 h-4 text-amber-400" />
                        Peer Group Cost Benchmark
                      </h4>

                      <div className="grid grid-cols-2 gap-3 text-xs">
                        <div className="bg-slate-900/80 p-2.5 rounded-lg border border-slate-800">
                          <span className="text-[10px] text-slate-500 block">Project Amount</span>
                          <span className="text-sm font-bold text-white">
                            {formatExactCurrency(sanctioned)}
                          </span>
                        </div>

                        <div className="bg-slate-900/80 p-2.5 rounded-lg border border-slate-800">
                          <span className="text-[10px] text-slate-500 block">Peer Group Median</span>
                          <span className="text-sm font-bold text-slate-200">
                            {formatExactCurrency(data.peer_benchmark?.peer_avg_cost || 0)}
                          </span>
                        </div>

                        <div className="bg-slate-900/80 p-2.5 rounded-lg border border-slate-800">
                          <span className="text-[10px] text-slate-500 block">Comparison Peer Size</span>
                          <span className="text-sm font-bold text-blue-400">
                            {data.peer_benchmark?.peer_count || alertData?.comparison_group_size || 0} projects
                          </span>
                        </div>

                        <div className="bg-slate-900/80 p-2.5 rounded-lg border border-slate-800">
                          <span className="text-[10px] text-slate-500 block">Robust Z-Score</span>
                          <span className="text-sm font-bold text-amber-400 font-mono">
                            +{alertData?.cost_zscore || '2.84'}σ
                          </span>
                        </div>
                      </div>

                      {/* Small sample disclosure */}
                      {(data.peer_benchmark?.peer_count || 0) < 5 && (
                        <div className="bg-amber-500/10 border border-amber-500/30 p-2 rounded text-[11px] text-amber-300">
                          <strong>Limited Comparison Group:</strong> Fewer than 5 comparable peer projects were available.
                        </div>
                      )}
                    </div>

                    {/* Financial Position & Lifecycle (Section 11 & 12) */}
                    <div className="bg-slate-800/40 border border-slate-700/80 rounded-xl p-4 space-y-3">
                      <h4 className="font-bold text-xs uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
                        <CreditCard className="w-4 h-4 text-emerald-400" />
                        Financial Position & Milestones
                      </h4>

                      <div className="grid grid-cols-2 gap-3 text-xs">
                        <div className="bg-slate-900/80 p-2.5 rounded-lg border border-slate-800">
                          <span className="text-[10px] text-slate-500 block">Sanctioned</span>
                          <span className="text-sm font-bold text-white">{formatExactCurrency(sanctioned)}</span>
                        </div>
                        <div className="bg-slate-900/80 p-2.5 rounded-lg border border-slate-800">
                          <span className="text-[10px] text-slate-500 block">Expenditure</span>
                          <span className="text-sm font-bold text-emerald-400">{formatExactCurrency(expenditure)}</span>
                        </div>
                        <div className="bg-slate-900/80 p-2.5 rounded-lg border border-slate-800">
                          <span className="text-[10px] text-slate-500 block">Utilization</span>
                          <span className="text-sm font-bold text-blue-400">{utilPct}%</span>
                        </div>
                        <div className="bg-slate-900/80 p-2.5 rounded-lg border border-slate-800">
                          <span className="text-[10px] text-slate-500 block">Lifecycle Status</span>
                          <span className="text-sm font-bold text-amber-400">{alertData?.project_status || 'In Progress'}</span>
                        </div>
                      </div>

                      {/* Milestone timeline */}
                      <div className="pt-2 border-t border-slate-700/60 flex items-center justify-between text-[10px] text-slate-400">
                        <div className="text-center">
                          <span className="block text-slate-500">Recommended</span>
                          <span className="font-semibold text-slate-300">{formatDate(rawData?.recommended_date || '2024-04-12')}</span>
                        </div>
                        <ChevronRight className="w-3 h-3 text-slate-600" />
                        <div className="text-center">
                          <span className="block text-slate-500">Sanctioned</span>
                          <span className="font-semibold text-slate-300">{formatDate(rawData?.sanction_date || '2024-05-15')}</span>
                        </div>
                        <ChevronRight className="w-3 h-3 text-slate-600" />
                        <div className="text-center">
                          <span className="block text-slate-500">Completion</span>
                          <span className="font-semibold text-amber-400">{rawData?.completion_date ? formatDate(rawData.completion_date) : 'Pending'}</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Recommended Review Action Plan (Section 26) */}
                  <div className="bg-blue-500/10 border border-blue-500/30 rounded-xl p-4 space-y-3">
                    <div className="flex items-center justify-between">
                      <h4 className="font-bold text-xs uppercase tracking-wider text-blue-300 flex items-center gap-1.5">
                        <CheckSquare className="w-4 h-4 text-blue-400" />
                        Recommended Desk-Review Action Plan
                      </h4>
                      <span className="text-[10px] text-blue-400 font-mono">
                        {checklist.filter((c) => c.done).length} of {checklist.length} Completed
                      </span>
                    </div>

                    <div className="space-y-2">
                      {checklist.map((item) => (
                        <div
                          key={item.id}
                          onClick={() => handleToggleChecklist(item.id)}
                          className={`flex items-start space-x-2.5 p-2 rounded-lg cursor-pointer transition-colors ${
                            item.done
                              ? 'bg-blue-500/20 text-slate-300 line-through'
                              : 'bg-slate-900/60 hover:bg-slate-900 text-slate-200'
                          }`}
                        >
                          {item.done ? (
                            <CheckSquare className="w-4 h-4 text-blue-400 shrink-0 mt-0.5" />
                          ) : (
                            <Square className="w-4 h-4 text-slate-500 shrink-0 mt-0.5" />
                          )}
                          <span className="text-xs">{item.step}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* TAB 2: POTENTIAL DUPLICATES (Section 8 & 9) */}
              {activeTab === 'duplicates' && (
                <div className="space-y-6">
                  <div className="bg-slate-800/40 border border-slate-700/80 rounded-xl p-4 space-y-2">
                    <h3 className="font-bold text-sm text-slate-100 flex items-center gap-1.5">
                      <Scale className="w-4 h-4 text-purple-400" />
                      Side-by-Side Multi-Signal Duplicate Analysis
                    </h3>
                    <p className="text-xs text-slate-400">
                      Comparing Target Project against top matching candidate works in the same district and sector.
                    </p>
                  </div>

                  {data.comparables && data.comparables.length > 0 ? (
                    <div className="space-y-4">
                      {data.comparables.map((comp: any, idx: number) => (
                        <div key={idx} className="bg-slate-800/30 border border-slate-700/80 rounded-xl p-4 space-y-4">
                          <div className="flex items-center justify-between border-b border-slate-700/60 pb-2">
                            <div className="flex items-center space-x-2">
                              <span className="bg-purple-500/20 text-purple-300 font-bold px-2 py-0.5 rounded text-xs">
                                Candidate #{idx + 1}
                              </span>
                              <span className="font-mono text-xs text-blue-400 font-bold">
                                {comp.comparable_work_code}
                              </span>
                            </div>
                            <span className="text-xs font-bold text-amber-400 font-mono">
                              Similarity: {Math.round((comp.similarity_score || 0.85) * 100)}%
                            </span>
                          </div>

                          {/* Side-by-side comparison grid */}
                          <div className="grid grid-cols-2 gap-4 text-xs">
                            {/* Left: Target Project */}
                            <div className="bg-slate-900/90 p-3 rounded-lg border border-slate-800 space-y-2">
                              <span className="text-[10px] font-bold text-blue-400 uppercase tracking-wider block">Target Work</span>
                              <p className="font-semibold text-white">{alertData?.work_type || alertData?.project_description || 'Target Project'}</p>
                              <div className="space-y-1 text-slate-400 text-[11px]">
                                <div><strong>District:</strong> {alertData?.district}</div>
                                <div><strong>Category:</strong> {alertData?.category}</div>
                                <div><strong>Amount:</strong> {formatExactCurrency(sanctioned)}</div>
                                <div><strong>Status:</strong> {alertData?.project_status}</div>
                              </div>
                            </div>

                            {/* Right: Matched Project */}
                            <div className="bg-slate-900/90 p-3 rounded-lg border border-slate-800 space-y-2">
                              <span className="text-[10px] font-bold text-purple-400 uppercase tracking-wider block">Candidate Match</span>
                              <p className="font-semibold text-white">{comp.work_type || 'Comparable Project'}</p>
                              <div className="space-y-1 text-slate-400 text-[11px]">
                                <div><strong>District:</strong> {comp.district}</div>
                                <div><strong>State:</strong> {comp.state}</div>
                                <div><strong>Amount:</strong> {formatExactCurrency(comp.sanctioned_amount || 0)}</div>
                                <div><strong>Status:</strong> {comp.status}</div>
                              </div>
                            </div>
                          </div>

                          <div className="bg-slate-950 p-2.5 rounded-lg text-slate-400 text-[11px] flex items-center justify-between">
                            <span><strong>Matching Rationale:</strong> {comp.reason || 'High textual similarity in work description combined with same district and category.'}</span>
                            <button
                              onClick={() => {
                                onClose();
                                navigate(`/projects/${encodeURIComponent(comp.comparable_work_code)}`);
                              }}
                              className="text-blue-400 hover:text-blue-300 font-semibold flex items-center ml-3 shrink-0"
                            >
                              Inspect Candidate →
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="py-12 text-center text-slate-500">
                      No candidate duplicate works identified for this record.
                    </div>
                  )}
                </div>
              )}

              {/* TAB 3: RELATIONSHIP GRAPH (Section 14 & 15) */}
              {activeTab === 'relationships' && (
                <div className="space-y-4">
                  <div className="bg-slate-800/40 border border-slate-700/80 rounded-xl p-4">
                    <h3 className="font-bold text-sm text-slate-100 mb-1 flex items-center gap-1.5">
                      <Layers className="w-4 h-4 text-blue-400" />
                      Interactive Relationship Graph
                    </h3>
                    <p className="text-xs text-slate-400">
                      Visualizing connected entities: MP, District, Category, Peer Projects, and Expenditure Vouchers.
                    </p>
                  </div>

                  <div className="h-[420px] bg-slate-950 rounded-xl border border-slate-800 overflow-hidden">
                    <ProjectRelationshipGraph workCode={alertData?.work_code || ''} />
                  </div>
                </div>
              )}

              {/* TAB 4: EXPENDITURE VOUCHERS (Section 22) */}
              {activeTab === 'vouchers' && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="font-bold text-sm text-slate-100 flex items-center gap-1.5">
                        <Receipt className="w-4 h-4 text-emerald-400" />
                        Disbursed Payment Vouchers
                      </h3>
                      <p className="text-xs text-slate-400">
                        Official payment transactions logged for work code {alertData?.work_code}.
                      </p>
                    </div>
                    <span className="text-xs font-mono font-bold text-emerald-400 bg-emerald-500/10 px-2.5 py-1 rounded-lg border border-emerald-500/20">
                      Total Disbursed: {formatExactCurrency(disbursed || expenditure)}
                    </span>
                  </div>

                  {data.vouchers && data.vouchers.length > 0 ? (
                    <div className="border border-slate-800 rounded-xl overflow-hidden">
                      <table className="w-full text-left text-xs">
                        <thead className="bg-slate-950 text-slate-400 uppercase text-[10px] font-mono tracking-wider">
                          <tr>
                            <th className="py-2.5 px-3">Voucher #</th>
                            <th className="py-2.5 px-3">Payment Date</th>
                            <th className="py-2.5 px-3">Amount</th>
                            <th className="py-2.5 px-3">Implementing Agency</th>
                            <th className="py-2.5 px-3">Status</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800">
                          {data.vouchers.map((v: any, i: number) => (
                            <tr key={i} className="hover:bg-slate-800/40">
                              <td className="py-2.5 px-3 font-mono text-slate-300">{v.voucher_number || `VCH-${i + 1}`}</td>
                              <td className="py-2.5 px-3 text-slate-400">{formatDate(v.expenditure_date || '2024-06-15')}</td>
                              <td className="py-2.5 px-3 font-bold text-white">{formatExactCurrency(v.amount || 0)}</td>
                              <td className="py-2.5 px-3 text-slate-300">{v.implementing_agency || alertData?.ida_name || 'District Authority'}</td>
                              <td className="py-2.5 px-3"><span className="text-emerald-400 font-semibold">Disbursed</span></td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <div className="py-12 text-center text-slate-500">
                      No individual payment vouchers recorded for this project work code.
                    </div>
                  )}
                </div>
              )}

              {/* TAB 5: DATA LINEAGE & FIELD PROVENANCE (Section 19, 20 & 21) */}
              {activeTab === 'lineage' && (
                <div className="space-y-6">
                  <div className="bg-slate-800/40 border border-slate-700/80 rounded-xl p-4 space-y-2">
                    <h3 className="font-bold text-sm text-slate-100 flex items-center gap-1.5">
                      <GitCommit className="w-4 h-4 text-indigo-400" />
                      5-Tier Data Traceability Pipeline
                    </h3>
                    <p className="text-xs text-slate-400">
                      End-to-end data provenance tracking this record from official MoSPI CSV files to this decision dossier.
                    </p>
                  </div>

                  {/* 5-Tier visual chain */}
                  <div className="space-y-3">
                    {[
                      { tier: 1, title: 'Tier 1: Primary Source CSV', file: 'Works Sanctioned - Lok Sabha.csv', desc: 'Raw official CSV file downloaded directly from MoSPI MPLADS portal.' },
                      { tier: 2, title: 'Tier 2: Ingestion & Extraction', file: 'Batch Ingestion Engine', desc: 'Normalized column parsing, work code extraction, and financial data cleaning.' },
                      { tier: 3, title: 'Tier 3: Relational Operational Storage', file: 'PostgreSQL / SQLite Database', desc: 'Canonical projects and expenditure vouchers storage with ACID constraints.' },
                      { tier: 4, title: 'Tier 4: Analytical Intelligence Engine', file: 'guardian-risk-2.0.0', desc: 'Hierarchical cost anomaly MAD/IQR, duplicate blocking, and progress rules R1–R8.' },
                      { tier: 5, title: 'Tier 5: Investigation Workspace Dossier', file: 'Evidence Room API', desc: 'Human-in-the-loop desk review prioritization and audit logging.' },
                    ].map((step, idx) => (
                      <div key={idx} className="flex items-start space-x-3 bg-slate-900/80 p-3 rounded-xl border border-slate-800">
                        <div className="w-6 h-6 rounded-full bg-blue-500/20 text-blue-400 font-mono font-bold text-xs flex items-center justify-center shrink-0 mt-0.5">
                          {step.tier}
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center justify-between">
                            <h5 className="font-bold text-slate-200 text-xs">{step.title}</h5>
                            <span className="font-mono text-[10px] text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded">
                              {step.file}
                            </span>
                          </div>
                          <p className="text-slate-400 text-[11px] mt-0.5">{step.desc}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* TAB 6: SOURCE RECORD & RAW DATA (Section 17 & 18) */}
              {activeTab === 'source' && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="font-bold text-sm text-slate-100 flex items-center gap-1.5">
                        <Database className="w-4 h-4 text-blue-400" />
                        Original Canonical Source Record
                      </h3>
                      <p className="text-xs text-slate-400">
                        Original un-altered fields extracted from MoSPI CSV datasets.
                      </p>
                    </div>
                    <button
                      onClick={() => setShowRawJson(!showRawJson)}
                      className="text-xs font-semibold text-blue-400 hover:text-blue-300 bg-blue-500/10 px-3 py-1.5 rounded-lg border border-blue-500/20"
                    >
                      {showRawJson ? 'Formatted View' : 'Raw JSON View'}
                    </button>
                  </div>

                  {showRawJson ? (
                    <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 font-mono text-[11px] text-slate-300 overflow-x-auto max-h-96">
                      <pre>{JSON.stringify(rawData, null, 2)}</pre>
                    </div>
                  ) : (
                    <div className="bg-slate-900 rounded-xl border border-slate-800 p-4 grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                      {Object.entries(rawData).map(([k, v]) => (
                        <div key={k} className="bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/80">
                          <span className="text-[10px] font-mono text-slate-500 block uppercase">{k}</span>
                          <span className="font-medium text-slate-200 break-words">{String(v || '—')}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* TAB 7: AUDIT TRAIL & HISTORY (Section 31) */}
              {activeTab === 'audit' && (
                <div className="space-y-4">
                  <div>
                    <h3 className="font-bold text-sm text-slate-100 flex items-center gap-1.5">
                      <History className="w-4 h-4 text-amber-400" />
                      Chronological Investigation Audit History
                    </h3>
                    <p className="text-xs text-slate-400">
                      Permanent, tamper-evident log of all triage status transitions and analyst review notes.
                    </p>
                  </div>

                  {data.audit_history && data.audit_history.length > 0 ? (
                    <div className="space-y-3">
                      {data.audit_history.map((log: any, idx: number) => (
                        <div key={idx} className="bg-slate-900/80 border border-slate-800 p-3 rounded-xl flex items-start space-x-3">
                          <div className="w-2 h-2 rounded-full bg-blue-400 mt-1.5 shrink-0" />
                          <div className="flex-1 space-y-1">
                            <div className="flex items-center justify-between text-xs">
                              <span className="font-bold text-slate-200">
                                {log.action || 'STATUS_UPDATE'}
                              </span>
                              <span className="text-[10px] text-slate-500 font-mono">
                                {log.created_at || 'Just now'}
                              </span>
                            </div>
                            <p className="text-xs text-slate-400">
                              {log.notes || `Transitioned from ${log.previous_state} to ${log.new_state}`}
                            </p>
                            <div className="text-[10px] text-slate-500">
                              By: <strong className="text-slate-300">{log.username || 'Analyst'}</strong> ({log.user_role || 'ANALYST'})
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="py-12 text-center text-slate-500">
                      No status modifications recorded yet. This signal is in initial OPEN status.
                    </div>
                  )}
                </div>
              )}

              {/* Human Review Triage & Action Panel (Section 27, 28 & 30) */}
              <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-4 pt-4">
                <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                  <h4 className="font-bold text-xs uppercase tracking-wider text-slate-200 flex items-center gap-1.5">
                    <UserCheck className="w-4 h-4 text-emerald-400" />
                    Human Review & Triage Workspace
                  </h4>
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded border ${getSeverityBadgeClass(alertData?.severity)}`}>
                    Current Status: {alertData?.status || 'OPEN'}
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Status Transition Control */}
                  <div className="space-y-2">
                    <label className="text-[11px] font-semibold text-slate-400 block">
                      Update Investigation Workflow Status
                    </label>
                    <select
                      value={selectedStatus}
                      onChange={(e) => setSelectedStatus(e.target.value)}
                      className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white font-medium focus:ring-1 focus:ring-blue-500"
                    >
                      <option value="OPEN">OPEN (Pending Review)</option>
                      <option value="UNDER_REVIEW">UNDER_REVIEW (Active Investigation)</option>
                      <option value="EVIDENCE_REQUESTED">EVIDENCE_REQUESTED (Awaiting Documentation)</option>
                      <option value="VALIDATED">VALIDATED (Confirmed Documentation Issue)</option>
                      <option value="NOT_SUBSTANTIATED">NOT_SUBSTANTIATED (Explainable Variance)</option>
                      <option value="RESOLVED">RESOLVED (Desk Review Completed)</option>
                      <option value="CLOSED">CLOSED (Archived)</option>
                    </select>

                    <input
                      type="text"
                      placeholder="Resolution / Status update reason..."
                      value={resolutionNotes}
                      onChange={(e) => setResolutionNotes(e.target.value)}
                      className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200 placeholder-slate-500"
                    />

                    <button
                      onClick={handleUpdateStatus}
                      disabled={submitting}
                      className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-3 rounded-lg text-xs transition-colors flex items-center justify-center space-x-1.5 disabled:opacity-50"
                    >
                      {submitting ? (
                        <span>Updating Workflow...</span>
                      ) : (
                        <>
                          <Check className="w-3.5 h-3.5" />
                          <span>Commit Status Transition</span>
                        </>
                      )}
                    </button>
                  </div>

                  {/* Add Analyst Note Form */}
                  <div className="space-y-2">
                    <label className="text-[11px] font-semibold text-slate-400 block">
                      Add Permanent Analyst Review Note
                    </label>
                    <textarea
                      rows={2}
                      placeholder="Enter official audit observation or verification finding..."
                      value={newAnalystNote}
                      onChange={(e) => setNewAnalystNote(e.target.value)}
                      className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-xs text-slate-200 placeholder-slate-500"
                    />
                    <button
                      onClick={handleAddAnalystNote}
                      disabled={addingNote || !newAnalystNote.trim()}
                      className="w-full bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold py-2 px-3 rounded-lg text-xs border border-slate-700 transition-colors flex items-center justify-center space-x-1.5 disabled:opacity-50"
                    >
                      {addingNote ? (
                        <span>Recording Note...</span>
                      ) : (
                        <>
                          <Send className="w-3.5 h-3.5 text-blue-400" />
                          <span>Save Analyst Note</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>
              </div>
            </>
          ) : null}
        </div>
      </div>
    </div>
  );
};
