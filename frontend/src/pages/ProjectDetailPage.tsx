import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { api } from '../services/api';
import { Project } from '../types';
import { WhyFlaggedCard } from '../components/explainer/WhyFlaggedCard';
import { ComparableProjectsList } from '../components/explainer/ComparableProjectsList';
import { ProjectRelationshipGraph } from '../components/explainer/ProjectRelationshipGraph';
import { EvidenceRoomModal } from '../components/explainer/EvidenceRoomModal';
import { RiskBadge } from '../components/common/RiskBadge';
import { SourceBadge } from '../components/common/SourceBadge';
import { CardSkeleton } from '../components/common/LoadingSkeleton';
import { formatExactCurrency, formatDate, formatNumber } from '../lib/utils';
import {
  ArrowLeft, Building2, Calendar, CreditCard, Database,
  FileCode2, Receipt, User, Info, GitCommit, CheckCircle2,
  ExternalLink, Eye, ShieldAlert
} from 'lucide-react';

export const ProjectDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [project, setProject] = useState<Project | null>(null);
  const [lineage, setLineage] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'overview' | 'relationships' | 'vouchers' | 'comparables' | 'lineage' | 'raw'>('overview');
  const [isEvidenceOpen, setIsEvidenceOpen] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    const decodedId = decodeURIComponent(id);
    
    Promise.all([
      api.getProjectDetail(decodedId),
      api.getProjectLineage(decodedId).catch(() => null)
    ])
      .then(([p, l]) => {
        setProject(p);
        setLineage(l);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Failed to load project details', err);
        setLoading(false);
      });
  }, [id]);

  if (loading || !project) {
    return (
      <div className="space-y-6 p-6">
        <div className="h-10 w-48 bg-slate-800 rounded animate-pulse" />
        <CardSkeleton count={4} />
      </div>
    );
  }

  const baseAmt = (project.sanctioned_amount || 0) > 0 ? project.sanctioned_amount : (project.recommended_amount || 0);
  const spentAmt = Math.max(project.disbursed_amount || 0, project.expenditure_amount || 0);
  const utilPct = baseAmt > 0 ? Math.min(100, Math.round((spentAmt / baseAmt) * 100)) : 0;

  return (
    <div className="space-y-6 pb-12">
      {/* Evidence Room Modal */}
      {isEvidenceOpen && (
        <EvidenceRoomModal
          alertId={project.work_code}
          isOpen={isEvidenceOpen}
          onClose={() => setIsEvidenceOpen(false)}
        />
      )}

      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate(-1)}
            className="p-2 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-400 hover:text-slate-200 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="font-mono text-xs font-bold text-indigo-400">{project.work_code}</span>
              <span className="px-2 py-0.5 rounded text-[10px] bg-slate-800 text-slate-300 border border-slate-700">
                {project.house === 'LOK_SABHA' ? 'Lok Sabha' : 'Rajya Sabha'}
              </span>
              <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-800 text-slate-300 border border-slate-700">
                FY {project.financial_year || '2025-26'}
              </span>
            </div>
            <h1 className="text-xl font-bold text-slate-100 leading-snug">
              {project.work_type || project.description || 'MPLADS Project Dossier'}
            </h1>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <RiskBadge level={project.risk_level} score={project.overall_risk_score} size="lg" />
          {project.overall_risk_score >= 50 && (
            <button
              onClick={() => setIsEvidenceOpen(true)}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-medium transition-colors shadow-sm"
            >
              <Eye className="w-3.5 h-3.5" />
              Evidence Room
            </button>
          )}
        </div>
      </div>

      {/* Tabs Navigation */}
      <div className="flex flex-wrap border-b border-slate-800 gap-4 text-xs font-mono font-medium">
        {[
          { id: 'overview', label: 'Dossier Overview', icon: Info },
          { id: 'relationships', label: 'Relationship Graph', icon: GitCommit },
          { id: 'vouchers', label: `Payment Vouchers (${project.vouchers?.length || 0})`, icon: Receipt },
          { id: 'comparables', label: `Peer Comparables (${project.comparable_projects?.length || 0})`, icon: Database },
          { id: 'lineage', label: '5-Tier Data Lineage', icon: CheckCircle2 },
          { id: 'raw', label: 'Raw CSV Fields', icon: FileCode2 },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`pb-3 transition-colors border-b-2 flex items-center gap-1.5 ${
                isActive
                  ? 'border-indigo-500 text-indigo-400 font-bold'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Tab Contents */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Key Metrics Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800">
              <div className="text-[10px] font-mono uppercase text-slate-400 mb-1 flex items-center gap-1.5">
                <CreditCard className="w-3.5 h-3.5 text-indigo-400" />
                Sanctioned Amount
              </div>
              <div className="text-xl font-bold font-mono text-slate-100">
              ₹{formatNumber(project.sanctioned_amount || 0)}
              </div>
              <div className="text-[11px] text-slate-400 mt-1">
                Recommended: ₹{formatNumber(project.recommended_amount || 0)}
              </div>
            </div>

            <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800">
              <div className="text-[10px] font-mono uppercase text-slate-400 mb-1 flex items-center gap-1.5">
                <Receipt className="w-3.5 h-3.5 text-emerald-400" />
                Cumulative Expenditure
              </div>
              <div className="text-xl font-bold font-mono text-emerald-400">
                ₹{formatNumber(spentAmt)}
              </div>
              <div className="text-[11px] text-slate-400 mt-1">
                Utilization Rate: <span className="font-bold text-slate-200">{utilPct}%</span>
              </div>
            </div>

            <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800">
              <div className="text-[10px] font-mono uppercase text-slate-400 mb-1 flex items-center gap-1.5">
                <User className="w-3.5 h-3.5 text-amber-400" />
                Recommending MP
              </div>
              <div className="text-sm font-bold text-slate-100 truncate">
                {project.mp_name || 'MPLADS Authority'}
              </div>
              <div className="text-[11px] text-slate-400 mt-1 truncate">
                {project.constituency || 'Constituency'}, {project.state}
              </div>
            </div>

            <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800">
              <div className="text-[10px] font-mono uppercase text-slate-400 mb-1 flex items-center gap-1.5">
                <Building2 className="w-3.5 h-3.5 text-purple-400" />
                Implementing Agency
              </div>
              <div className="text-sm font-bold text-slate-100 truncate">
                {project.ida_name || 'District Authority'}
              </div>
              <div className="text-[11px] text-slate-400 mt-1">
                Status: <span className="font-semibold text-indigo-300">{project.status}</span>
              </div>
            </div>
          </div>

          {/* AI / Risk Rationale Card */}
          <WhyFlaggedCard project={project} />

          {/* Embedded Relationship Graph */}
          <div className="pt-2">
            <ProjectRelationshipGraph workCode={project.work_code} />
          </div>
        </div>
      )}

      {/* Tab: Relationships */}
      {activeTab === 'relationships' && (
        <div>
          <ProjectRelationshipGraph workCode={project.work_code} />
        </div>
      )}

      {/* Tab: Vouchers */}
      {activeTab === 'vouchers' && (
        <div className="bg-slate-900/60 rounded-xl border border-slate-800 p-4">
          <h3 className="text-sm font-bold text-slate-200 mb-3">Linked Payment Expenditure Vouchers</h3>
          {(!project.vouchers || project.vouchers.length === 0) ? (
            <div className="text-xs text-slate-400 py-8 text-center font-mono">
              No individual contractor vouchers recorded for this project work.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-950 text-slate-400 font-mono text-[10px] uppercase border-b border-slate-800">
                  <tr>
                    <th className="py-2.5 px-3">Date</th>
                    <th className="py-2.5 px-3">Vendor / Contractor</th>
                    <th className="py-2.5 px-3">Status</th>
                    <th className="py-2.5 px-3 text-right">Disbursed Amount</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 text-slate-300">
                  {project.vouchers.map((v, i) => (
                    <tr key={i} className="hover:bg-slate-800/30">
                      <td className="py-2.5 px-3 font-mono text-[11px]">{v.expenditure_date || '—'}</td>
                      <td className="py-2.5 px-3 font-medium text-slate-200">{v.vendor_name || 'Standard Agency'}</td>
                      <td className="py-2.5 px-3">
                        <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-500/20 text-emerald-400">
                          {v.payment_status || 'DISBURSED'}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 text-right font-mono font-bold text-slate-100">
                        ₹{formatNumber(v.disbursed_amount || 0)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Tab: Comparables */}
      {activeTab === 'comparables' && (
        <div>
          <ComparableProjectsList
            comparables={project.comparable_projects || []}
            currentWorkCode={project.work_code}
          />
        </div>
      )}

      {/* Tab: Data Lineage */}
      {activeTab === 'lineage' && lineage && (
        <div className="bg-slate-900/60 rounded-xl border border-slate-800 p-6 space-y-4">
          <div>
            <h3 className="text-sm font-bold text-slate-200">5-Tier End-to-End Data Traceability</h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Verified record lineage linking high-level dashboard signals down to raw source CSV lines.
            </p>
          </div>

          <div className="space-y-3 pt-2">
            {lineage.tiers?.map((t: any) => (
              <div key={t.tier} className="flex items-center gap-3 p-3 bg-slate-950/70 rounded-lg border border-slate-800 text-xs">
                <span className="w-6 h-6 rounded-full bg-indigo-950 text-indigo-400 flex items-center justify-center font-mono font-bold text-xs">
                  {t.tier}
                </span>
                <div className="w-56 shrink-0 font-mono text-slate-400 text-[11px]">{t.name}</div>
                <div className="text-slate-200 font-mono text-[11px] truncate flex-1">{t.source}</div>
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab: Raw CSV Fields */}
      {activeTab === 'raw' && (
        <div className="bg-slate-900/60 rounded-xl border border-slate-800 p-4 space-y-2">
          <h3 className="text-sm font-bold text-slate-200">Raw Source Ingestion Payload</h3>
          <pre className="p-4 bg-slate-950 rounded-lg text-xs font-mono text-slate-300 overflow-x-auto max-h-96">
            {JSON.stringify(project.raw_data || project, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
};
