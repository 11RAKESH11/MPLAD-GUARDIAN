import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Compass, ArrowRight, ArrowLeft, CheckCircle, ShieldAlert, FileText, Database, MapPin } from 'lucide-react';
import { Modal } from '../common/Modal';

interface GuidedTourProps {
  isOpen: boolean;
  onClose: () => void;
}

export const GuidedInvestigationTour: React.FC<GuidedTourProps> = ({ isOpen, onClose }) => {
  const [currentStep, setCurrentStep] = useState(0);
  const navigate = useNavigate();

  const tourSteps = [
    {
      title: 'Step 1: National Scope & Verified Primary Dataset',
      icon: Database,
      badge: 'REAL CSV DATA',
      summary: 'MPLAD GUARDIAN is engineered on 374,141 verified primary records across 12 official Lok Sabha & Rajya Sabha CSV files.',
      details: [
        '96,654 unique project lifecycles across 36 States & Union Territories.',
        '₹57,511+ Crore in sanctioned funds analyzed with zero synthetic fabrication.',
        '106,442 vendor expenditure vouchers cross-linked into project lifecycles.',
      ],
      actionText: 'Proceed to Risk Command Map',
      onAction: () => navigate('/risk-map'),
    },
    {
      title: 'Step 2: Regional Concentration & Geographic Intelligence',
      icon: MapPin,
      badge: 'SPATIAL INTELLIGENCE',
      summary: 'The Geographic Intelligence module highlights regional density of high-cost anomalies and progress delays.',
      details: [
        'Multilevel drill-down: National → State → District → Works.',
        'Maintains complete analytical filter state without guessing exact GPS coordinates.',
        'Computes regional anomaly indices across 760+ districts.',
      ],
      actionText: 'Triage High-Risk Alerts',
      onAction: () => navigate('/alerts'),
    },
    {
      title: 'Step 3: Prioritized Alert Management & Desk Audit',
      icon: ShieldAlert,
      badge: 'DECISION SUPPORT',
      summary: 'Statistical models surface actionable oversight signals categorized by Cost Anomaly, Duplicate Similarity, and Progress Gaps.',
      details: [
        '270 prioritized alerts with analytical evidence and impact descriptions.',
        'Audited review workflow for analysts: Open → Acknowledged → Resolved.',
        'Ethical framing: Analytical signals that assist human reviewers without accusing.',
      ],
      actionText: 'Inspect Top Flagged Project',
      onAction: () => navigate('/projects/WS%2FMP792%2F2025-2026%2F225865'),
    },
    {
      title: 'Step 4: Explainable AI Dossier ("Why Flagged?")',
      icon: FileText,
      badge: 'EXPLAINABLE AI',
      summary: 'Every flagged proposal includes an explainable breakdown answering WHAT was detected, WHY it was flagged, and HOW it compares.',
      details: [
        'Multi-factor weights: Cost (30%), Duplicate (30%), Progress Gap (25%), Geographic (15%).',
        'Z-score & MAD comparisons against verified category and state baselines.',
        'Comparable project matcher detecting 70%+ text description similarity.',
        'Complete source traceability down to original CSV records and payment vouchers.',
      ],
      actionText: 'Explore Project Explorer',
      onAction: () => {
        navigate('/projects');
        onClose();
      },
    },
  ];

  const step = tourSteps[currentStep];
  const Icon = step.icon;

  const handleNext = () => {
    step.onAction();
    if (currentStep < tourSteps.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      onClose();
    }
  };

  const handlePrev = () => {
    if (currentStep > 0) setCurrentStep(currentStep - 1);
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="MPLAD GUARDIAN — Guided Investigation Tour"
      subtitle="Institutional Demonstration for Evaluators & Senior Stakeholders"
      maxWidth="xl"
    >
      <div className="space-y-6">
        {/* Step Progress Bar */}
        <div className="flex items-center justify-between gap-2 border-b border-[#E1E5E1] pb-4">
          {tourSteps.map((s, i) => (
            <div
              key={i}
              onClick={() => {
                s.onAction();
                setCurrentStep(i);
              }}
              className={`flex-1 h-1.5 rounded-full cursor-pointer transition-all ${
                i === currentStep
                  ? 'bg-[#10243E]'
                  : i < currentStep
                  ? 'bg-[#287D4B]'
                  : 'bg-[#E1E5E1]'
              }`}
            />
          ))}
        </div>

        {/* Step Content Card */}
        <div className="p-5 rounded-lg bg-[#F8F9F8] border border-[#E1E5E1] space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-md bg-[#EAF0F6] text-[#10243E]">
                <Icon className="w-5 h-5" />
              </div>
              <div>
                <h4 className="text-sm font-bold text-[#17202A] font-display">{step.title}</h4>
                <span className="text-[10px] font-sans font-semibold text-[#167D7F] uppercase tracking-wider">
                  {step.badge}
                </span>
              </div>
            </div>
            <span className="text-xs font-mono text-[#7B8794]">
              {currentStep + 1} of {tourSteps.length}
            </span>
          </div>

          <p className="text-xs text-[#52606D] leading-relaxed font-normal">
            {step.summary}
          </p>

          <div className="space-y-2 pt-2 border-t border-[#E1E5E1]">
            {step.details.map((d, idx) => (
              <div key={idx} className="flex items-start gap-2.5 text-xs text-[#17202A]">
                <CheckCircle className="w-4 h-4 text-[#287D4B] flex-shrink-0 mt-0.5" />
                <span>{d}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Modal Actions */}
        <div className="flex items-center justify-between pt-2">
          <button
            onClick={handlePrev}
            disabled={currentStep === 0}
            className={`px-4 py-2 rounded-md text-xs font-semibold inline-flex items-center gap-1.5 transition-all ${
              currentStep === 0
                ? 'opacity-40 cursor-not-allowed text-[#7B8794]'
                : 'text-[#52606D] hover:text-[#17202A] bg-[#F1F3F0] hover:bg-[#E1E5E1]'
            }`}
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Previous</span>
          </button>

          <button
            onClick={handleNext}
            className="px-5 py-2 bg-[#10243E] hover:bg-[#193354] text-white text-xs font-bold rounded-md shadow-civic inline-flex items-center gap-2 transition-all"
          >
            <span>{step.actionText}</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </Modal>
  );
};
