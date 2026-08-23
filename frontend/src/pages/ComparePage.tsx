import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { StateSummary } from '../types';
import { formatCurrency, formatNumber } from '../lib/utils';
import { GitCompare, Building2, ArrowRight, CheckCircle2, ShieldAlert, Sliders, Info } from 'lucide-react';
import { SourceBadge } from '../components/common/SourceBadge';

export const ComparePage: React.FC = () => {
  const [states, setStates] = useState<StateSummary[]>([]);
  const [stateA, setStateA] = useState<string>('Maharashtra');
  const [stateB, setStateB] = useState<string>('Uttar Pradesh');
  const [loading, setLoading] = useState(true);

  // Scenario Simulation States
  const [simCompletionDelta, setSimCompletionDelta] = useState<number>(10);
  const [simExpRealignment, setSimExpRealignment] = useState<number>(15);

  useEffect(() => {
    api.getStates().then((res) => {
      setStates(res.states);
      if (res.states.length > 1) {
        setStateA(res.states[0].state);
        setStateB(res.states[1].state);
      }
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  const dataA = states.find((s) => s.state === stateA);
  const dataB = states.find((s) => s.state === stateB);

  return (
    <div className="space-y-8 animate-fadeIn pb-12">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-[#E5E7EB]">
        <div>
          <h1 className="text-2xl font-bold text-[#172033] tracking-tight font-display">
            Comparative Development & Scenario Intelligence
          </h1>
          <p className="text-xs text-[#667085] mt-0.5">
            Objective side-by-side evaluation across state developmental indicators with hypothetical policy impact simulations.
          </p>
        </div>

        <SourceBadge type="DERIVED ANALYTICS" />
      </div>

      {/* Selectors */}
      <div className="gov-card p-5 grid grid-cols-1 md:grid-cols-2 gap-6 bg-[#F7F8F6] border border-[#E5E7EB] rounded-xl">
        <div className="space-y-1.5">
          <label className="text-xs font-bold uppercase tracking-wider text-[#667085] block">
            Primary Jurisdiction (State A)
          </label>
          <select
            value={stateA}
            onChange={(e) => setStateA(e.target.value)}
            className="w-full p-2.5 bg-white border border-[#E5E7EB] rounded-lg text-xs font-medium text-[#172033] focus:outline-none focus:border-[#102A43]"
          >
            {states.map((s) => (
              <option key={s.state} value={s.state}>{s.state}</option>
            ))}
          </select>
        </div>

        <div className="space-y-1.5">
          <label className="text-xs font-bold uppercase tracking-wider text-[#667085] block">
            Comparative Jurisdiction (State B)
          </label>
          <select
            value={stateB}
            onChange={(e) => setStateB(e.target.value)}
            className="w-full p-2.5 bg-white border border-[#E5E7EB] rounded-lg text-xs font-medium text-[#172033] focus:outline-none focus:border-[#102A43]"
          >
            {states.map((s) => (
              <option key={s.state} value={s.state}>{s.state}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Side-by-Side Comparison Cards */}
      {dataA && dataB && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Card A */}
          <div className="gov-card p-6 space-y-5 border border-[#E5E7EB] rounded-xl border-t-4 border-t-[#102A43] bg-white">
            <div className="flex items-center justify-between pb-3 border-b border-[#E5E7EB]">
              <div className="flex items-center gap-2">
                <Building2 className="w-5 h-5 text-[#102A43]" />
                <h3 className="text-lg font-bold text-[#172033] font-display">{dataA.state}</h3>
              </div>
              <span className="text-xs font-mono text-[#667085]">{dataA.total_districts} Districts</span>
            </div>

            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="p-3 bg-[#F7F8F6] rounded-lg border border-[#E5E7EB]">
                <span className="text-[#667085] text-[10px] uppercase font-bold block">Total Works</span>
                <span className="text-lg font-bold text-[#172033] font-mono">{formatNumber(dataA.total_projects)}</span>
              </div>
              <div className="p-3 bg-[#F7F8F6] rounded-lg border border-[#E5E7EB]">
                <span className="text-[#667085] text-[10px] uppercase font-bold block">Completion Rate</span>
                <span className="text-lg font-bold text-[#14804A] font-mono">{dataA.completion_pct}%</span>
              </div>
              <div className="p-3 bg-[#F7F8F6] rounded-lg border border-[#E5E7EB]">
                <span className="text-[#667085] text-[10px] uppercase font-bold block">Sanctioned</span>
                <span className="text-sm font-bold text-[#172033] font-mono">{formatCurrency(dataA.total_sanctioned)}</span>
              </div>
              <div className="p-3 bg-[#F7F8F6] rounded-lg border border-[#E5E7EB]">
                <span className="text-[#667085] text-[10px] uppercase font-bold block">Expenditure</span>
                <span className="text-sm font-bold text-[#172033] font-mono">{formatCurrency(dataA.total_expenditure)}</span>
              </div>
            </div>

            <div className="p-3 bg-[#F7F8F6] rounded-lg border border-[#E5E7EB] flex items-center justify-between text-xs font-mono">
              <span className="text-slate-600">Fund Utilization Rate</span>
              <strong className="text-[#102A43]">{dataA.utilization_pct}%</strong>
            </div>
          </div>

          {/* Card B */}
          <div className="gov-card p-6 space-y-5 border border-[#E5E7EB] rounded-xl border-t-4 border-t-[#3E63DD] bg-white">
            <div className="flex items-center justify-between pb-3 border-b border-[#E5E7EB]">
              <div className="flex items-center gap-2">
                <Building2 className="w-5 h-5 text-[#3E63DD]" />
                <h3 className="text-lg font-bold text-[#172033] font-display">{dataB.state}</h3>
              </div>
              <span className="text-xs font-mono text-[#667085]">{dataB.total_districts} Districts</span>
            </div>

            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="p-3 bg-[#F7F8F6] rounded-lg border border-[#E5E7EB]">
                <span className="text-[#667085] text-[10px] uppercase font-bold block">Total Works</span>
                <span className="text-lg font-bold text-[#172033] font-mono">{formatNumber(dataB.total_projects)}</span>
              </div>
              <div className="p-3 bg-[#F7F8F6] rounded-lg border border-[#E5E7EB]">
                <span className="text-[#667085] text-[10px] uppercase font-bold block">Completion Rate</span>
                <span className="text-lg font-bold text-[#14804A] font-mono">{dataB.completion_pct}%</span>
              </div>
              <div className="p-3 bg-[#F7F8F6] rounded-lg border border-[#E5E7EB]">
                <span className="text-[#667085] text-[10px] uppercase font-bold block">Sanctioned</span>
                <span className="text-sm font-bold text-[#172033] font-mono">{formatCurrency(dataB.total_sanctioned)}</span>
              </div>
              <div className="p-3 bg-[#F7F8F6] rounded-lg border border-[#E5E7EB]">
                <span className="text-[#667085] text-[10px] uppercase font-bold block">Expenditure</span>
                <span className="text-sm font-bold text-[#172033] font-mono">{formatCurrency(dataB.total_expenditure)}</span>
              </div>
            </div>

            <div className="p-3 bg-[#F7F8F6] rounded-lg border border-[#E5E7EB] flex items-center justify-between text-xs font-mono">
              <span className="text-slate-600">Fund Utilization Rate</span>
              <strong className="text-[#3E63DD]">{dataB.utilization_pct}%</strong>
            </div>
          </div>
        </div>
      )}

      {/* What-If / Scenario Simulation */}
      {dataA && (
        <div className="gov-card p-6 bg-white border border-[#E5E7EB] rounded-xl space-y-5">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-[#E5E7EB]">
            <div className="flex items-center gap-2">
              <Sliders className="w-5 h-5 text-indigo-600" />
              <div>
                <h3 className="text-base font-bold text-[#172033]">
                  Scenario Simulation Workspace — {dataA.state}
                </h3>
                <span className="text-[11px] text-amber-700 font-mono font-semibold">
                  SIMULATION ONLY — NOT A FORECAST OR OFFICIAL PROJECTION
                </span>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-xs">
            {/* Slider 1 */}
            <div className="space-y-2 bg-[#F7F8F6] p-4 rounded-lg border border-[#E5E7EB]">
              <div className="flex justify-between">
                <span className="font-semibold text-[#172033]">Target Completion Acceleration</span>
                <span className="font-mono font-bold text-indigo-600">+{simCompletionDelta}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="30"
                value={simCompletionDelta}
                onChange={(e) => setSimCompletionDelta(Number(e.target.value))}
                className="w-full accent-indigo-600"
              />
              <p className="text-[11px] text-[#667085]">
                Simulates accelerated physical completion of currently sanctioned works.
              </p>
            </div>

            {/* Slider 2 */}
            <div className="space-y-2 bg-[#F7F8F6] p-4 rounded-lg border border-[#E5E7EB]">
              <div className="flex justify-between">
                <span className="font-semibold text-[#172033]">Disbursement Liquidation Efficiency</span>
                <span className="font-mono font-bold text-indigo-600">+{simExpRealignment}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="30"
                value={simExpRealignment}
                onChange={(e) => setSimExpRealignment(Number(e.target.value))}
                className="w-full accent-indigo-600"
              />
              <p className="text-[11px] text-[#667085]">
                Simulates expedited contractor voucher settlement and physical verification.
              </p>
            </div>
          </div>

          {/* Simulated Impact Output */}
          <div className="p-4 bg-indigo-50/60 rounded-xl border border-indigo-100 grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
            <div>
              <span className="text-indigo-900/70 text-[10px] uppercase font-mono block">Baseline Completed Works</span>
              <span className="text-base font-bold font-mono text-indigo-950">{formatNumber(dataA.completed_works)}</span>
            </div>
            <div>
              <span className="text-indigo-900/70 text-[10px] uppercase font-mono block">Simulated Additional Completed</span>
              <span className="text-base font-bold font-mono text-emerald-700">
                +{Math.round(dataA.total_projects * (simCompletionDelta / 100)).toLocaleString()} works
              </span>
            </div>
            <div>
              <span className="text-indigo-900/70 text-[10px] uppercase font-mono block">Simulated New Completion Rate</span>
              <span className="text-base font-bold font-mono text-indigo-900">
                {Math.min(100, Math.round(dataA.completion_pct + simCompletionDelta))}%
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
