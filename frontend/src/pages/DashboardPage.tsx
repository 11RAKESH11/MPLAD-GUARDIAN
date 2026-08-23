import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import { DashboardOverview, NarrativeInsight } from '../types';
import { MetricCard } from '../components/common/MetricCard';
import { CardSkeleton } from '../components/common/LoadingSkeleton';
import { SourceBadge } from '../components/common/SourceBadge';
import { IndiaRiskMap } from '../components/map/IndiaRiskMap';
import { EvidenceRoomModal } from '../components/explainer/EvidenceRoomModal';
import { formatCurrency, formatNumber } from '../lib/utils';
import {
  FileText, DollarSign, TrendingUp, Activity, ArrowRight,
  ShieldAlert, ArrowUpRight, CheckCircle2, Layers, BarChart3,
  Eye, Compass, Sparkles
} from 'lucide-react';
import {
  ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid
} from 'recharts';

export const DashboardPage: React.FC = () => {
  const [overview, setOverview] = useState<DashboardOverview | null>(null);
  const [insights, setInsights] = useState<NarrativeInsight[]>([]);
  const [trends, setTrends] = useState<any>(null);
  const [mapData, setMapData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [rankingMetric, setRankingMetric] = useState<'total_projects' | 'total_sanctioned' | 'completion_rate_pct' | 'utilization_pct'>('total_projects');
  const [evidenceAlertId, setEvidenceAlertId] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    Promise.all([
      api.getDashboardOverview(),
      api.getDashboardInsights(),
      api.getDashboardTrends(),
      api.getRiskMapData(),
    ]).then(([o, ins, tr, mp]) => {
      setOverview(o);
      setInsights(ins.insights);
      setTrends(tr);
      setMapData(mp.states);
      setLoading(false);
    }).catch((err) => {
      console.error('Failed to load dashboard', err);
      setLoading(false);
    });
  }, []);

  if (loading || !overview) {
    return (
      <div className="space-y-6">
        <div className="h-24 bg-white rounded-lg animate-pulse border border-[#E5E7EB]" />
        <CardSkeleton count={5} />
        <CardSkeleton count={3} />
      </div>
    );
  }

  const { kpis, risk_metrics } = overview;

  const fyTrendsData = trends?.financial_year_trends?.map((f: any) => ({
    year: f.financial_year,
    recommended: Math.round((f.sanctioned_funds || 0) * 1.15 / 10000000),
    sanctioned: Math.round((f.sanctioned_funds || 0) / 10000000),
    completed: Math.round((f.expenditure_funds || 0) / 10000000),
  })) || [];

  const rankedStates = [...mapData].sort((a, b) => b[rankingMetric] - a[rankingMetric]).slice(0, 7);

  return (
    <div className="space-y-8 animate-fadeIn pb-12">
      {/* Evidence Room Modal */}
      {evidenceAlertId && (
        <EvidenceRoomModal
          alertId={evidenceAlertId}
          isOpen={!!evidenceAlertId}
          onClose={() => setEvidenceAlertId(null)}
        />
      )}

      {/* 1. National Development Pulse Hero */}
      <div className="gov-card p-6 bg-white flex flex-col lg:flex-row lg:items-center justify-between gap-6 border border-[#E5E7EB] rounded-xl">
        <div className="space-y-2 max-w-3xl">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-[#102A43]" />
            <span className="text-[11px] font-sans font-bold tracking-wider text-[#102A43] uppercase">
              National Development Overview
            </span>
          </div>

          <h2 className="text-xl lg:text-2xl font-bold text-[#172033] tracking-tight font-display">
            Public Development Monitoring & Decision Intelligence
          </h2>

          <p className="text-xs text-[#667085] leading-relaxed">
            Continuous oversight of MPLADS project activity, financial utilization, completion patterns, and statistical risk signals across 36 States & UTs.
          </p>
        </div>

        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
          <button
            onClick={() => navigate('/alerts')}
            className="px-4 py-2 bg-[#102A43] text-white hover:bg-[#1E3A8A] text-xs font-semibold rounded-lg transition-colors flex items-center justify-center gap-2 shadow-sm"
          >
            <ShieldAlert className="w-4 h-4" />
            Priority Queue ({risk_metrics.critical_count + risk_metrics.high_count} Signals)
          </button>
        </div>
      </div>

      {/* 2. Core KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <MetricCard
          title="Total Projects Monitored"
          value={formatNumber(kpis.total_projects)}
          subtitle="374,141 Source Records"
          icon={FileText}
        />

        <MetricCard
          title="Sanctioned Funds"
          value={formatCurrency(kpis.total_sanctioned_funds)}
          subtitle={`Rec: ${formatCurrency(kpis.total_recommended_funds)}`}
          icon={DollarSign}
        />

        <MetricCard
          title="Cumulative Expenditure"
          value={formatCurrency(kpis.total_expenditure_funds || kpis.total_disbursed_funds)}
          subtitle={`${kpis.utilization_rate_pct}% Overall Utilization`}
          icon={TrendingUp}
        />

        <MetricCard
          title="Completed Works"
          value={formatNumber(kpis.completed_works)}
          subtitle={`${Math.round((kpis.completed_works / kpis.total_projects) * 100)}% Completion Rate`}
          icon={CheckCircle2}
        />

        <MetricCard
          title="Analytical Risk Signals"
          value={formatNumber(risk_metrics.critical_count + risk_metrics.high_count)}
          subtitle={`${risk_metrics.critical_count} Critical • ${risk_metrics.high_count} High`}
          icon={Activity}
          onClick={() => navigate('/alerts')}
        />
      </div>

      {/* 3. National GIS Map */}
      <div className="space-y-2">
        <IndiaRiskMap />
      </div>

      {/* 4. Narrative Analytical Insights */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-base font-bold text-[#172033] font-display">
              Key Analytical Findings & Recommendations
            </h3>
            <p className="text-xs text-[#667085]">
              Automated statistical pattern detection and actionable oversight highlights
            </p>
          </div>
          <button
            onClick={() => navigate('/alerts')}
            className="text-xs font-semibold text-[#102A43] hover:underline flex items-center gap-1"
          >
            View All Signals <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {insights.slice(0, 3).map((insight) => (
            <div
              key={insight.id}
              className="gov-card p-4 bg-white flex flex-col justify-between border border-[#E5E7EB] rounded-xl hover:border-[#102A43] transition-colors"
            >
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-[#102A43] bg-[#F0F4F8] px-2 py-0.5 rounded">
                    {insight.badge}
                  </span>
                  <span className="text-[10px] text-[#667085] font-mono">
                    {insight.severity}
                  </span>
                </div>

                <h4 className="text-xs font-bold text-[#172033] leading-snug">
                  {insight.title}
                </h4>

                <p className="text-[11px] text-[#667085] line-clamp-3 leading-relaxed">
                  {insight.summary}
                </p>
              </div>

              <div className="pt-3 mt-3 border-t border-[#F0F2ED] flex items-center justify-between">
                <span className="text-[10px] font-semibold text-[#102A43]">
                  {insight.action}
                </span>
                <button
                  onClick={() => navigate('/alerts')}
                  className="p-1 rounded hover:bg-[#F0F2ED] text-[#102A43]"
                >
                  <ArrowUpRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 5. Temporal Trends & State Rankings */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* FY Trends Area Chart */}
        <div className="lg:col-span-2 gov-card p-6 bg-white border border-[#E5E7EB] rounded-xl space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-[#172033] font-display">
                Multi-Year Financial Trends
              </h3>
              <p className="text-[11px] text-[#667085]">
                Sanctioned allocation vs actual expenditure over financial years (₹ in Crores)
              </p>
            </div>
            <SourceBadge type="DERIVED ANALYTICS" />
          </div>

          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={fyTrendsData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                <defs>
                  <linearGradient id="sanctionedGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#102A43" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#102A43" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="completedGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#2E7D32" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#2E7D32" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#F0F2ED" />
                <XAxis dataKey="year" tick={{ fontSize: 11, fill: '#667085' }} />
                <YAxis tick={{ fontSize: 11, fill: '#667085' }} tickFormatter={(val) => `₹${val} Cr`} />
                <Tooltip
                  formatter={(val: any) => [`₹${val} Cr`, '']}
                  contentStyle={{ backgroundColor: '#172033', color: '#fff', borderRadius: '8px', fontSize: '11px' }}
                />
                <Area type="monotone" dataKey="sanctioned" name="Sanctioned" stroke="#102A43" strokeWidth={2} fillOpacity={1} fill="url(#sanctionedGrad)" />
                <Area type="monotone" dataKey="completed" name="Expenditure" stroke="#2E7D32" strokeWidth={2} fillOpacity={1} fill="url(#completedGrad)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* State Performance Leaderboard */}
        <div className="gov-card p-6 bg-white border border-[#E5E7EB] rounded-xl space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-[#172033] font-display">
              State Activity Distribution
            </h3>
            <select
              value={rankingMetric}
              onChange={(e) => setRankingMetric(e.target.value as any)}
              className="text-[11px] font-sans font-semibold border border-[#D9E2EC] rounded px-2 py-1 bg-white text-[#172033]"
            >
              <option value="total_projects">Projects</option>
              <option value="total_sanctioned">Funds</option>
              <option value="utilization_pct">Utilization %</option>
              <option value="completion_rate_pct">Completion %</option>
            </select>
          </div>

          <div className="space-y-3">
            {rankedStates.map((st, i) => (
              <div
                key={st.state}
                onClick={() => navigate(`/analytics/states/${encodeURIComponent(st.state)}`)}
                className="flex items-center justify-between p-2 rounded-lg hover:bg-[#F0F4F8] cursor-pointer transition-colors text-xs"
              >
                <div className="flex items-center gap-2">
                  <span className="w-5 font-mono text-[10px] text-[#667085] font-bold">#{i + 1}</span>
                  <span className="font-semibold text-[#172033]">{st.state}</span>
                </div>
                <div className="font-mono font-bold text-[#102A43]">
                  {rankingMetric === 'total_projects' && `${st.total_projects.toLocaleString()} works`}
                  {rankingMetric === 'total_sanctioned' && formatCurrency(st.total_sanctioned)}
                  {rankingMetric === 'utilization_pct' && `${st.utilization_pct}%`}
                  {rankingMetric === 'completion_rate_pct' && `${st.completion_rate_pct}%`}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
