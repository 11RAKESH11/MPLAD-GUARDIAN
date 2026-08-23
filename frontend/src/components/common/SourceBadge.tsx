import React from 'react';
import { SourceBadgeType } from '../../types';

interface SourceBadgeProps {
  type?: SourceBadgeType | string;
  sourceFile?: string;
  description?: string;
  className?: string;
}

export const SourceBadge: React.FC<SourceBadgeProps> = ({
  type = 'REAL SOURCE DATA',
  sourceFile,
  description,
  className = '',
}) => {
  const isReal = type === 'REAL CSV DATA' || type === 'OFFICIAL SOURCE' || type === 'REAL SOURCE DATA' || type === 'SOURCE DATA';
  const isAI = type === 'AI ANALYSIS' || type === 'DERIVED ANALYTICS' || type === 'ANALYTICAL';

  const label = isReal ? 'REAL SOURCE DATA' : isAI ? 'ANALYTICAL SIGNAL' : type;

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] font-mono tracking-tight border transition-colors ${
        isReal
          ? 'bg-[#F0F4F8] text-[#102A43] border-[#D9E2EC]'
          : isAI
          ? 'bg-[#EDF8F8] text-[#147A73] border-[#D6EFEF]'
          : 'bg-[#F0F2ED] text-[#667085] border-[#E5E7EB]'
      } ${className}`}
      title={description || (sourceFile ? `Source file: ${sourceFile}` : 'Official MPLADS Dataset')}
    >
      <span
        className={`w-1.5 h-1.5 rounded-full ${
          isReal ? 'bg-[#102A43]' : isAI ? 'bg-[#147A73]' : 'bg-[#98A2B3]'
        }`}
      />
      <span className="font-semibold uppercase">{label}</span>
    </span>
  );
};
