import React from 'react';
import { RiskLevel } from '../../types';
import { getRiskHex } from '../../lib/utils';

interface RiskGaugeProps {
  score: number;
  confidence?: number;
  riskLevel?: RiskLevel;
  size?: number;
  showDetails?: boolean;
}

export const RiskGauge: React.FC<RiskGaugeProps> = ({
  score,
  confidence,
  riskLevel = 'LOW',
  size = 110,
  showDetails = true,
}) => {
  const strokeWidth = 7;
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const normalizedScore = Math.min(100, Math.max(0, score));
  const strokeDashoffset = circumference - (normalizedScore / 100) * circumference;
  const riskColor = getRiskHex(riskLevel);

  return (
    <div className="flex flex-col items-center justify-center select-none text-center">
      <div className="relative flex items-center justify-center" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="transform -rotate-90">
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke="#E5E7EB"
            strokeWidth={strokeWidth}
            fill="transparent"
          />
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke={riskColor}
            strokeWidth={strokeWidth}
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            fill="transparent"
            className="transition-all duration-700 ease-out"
          />
        </svg>

        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-2xl font-bold font-display text-[#172033] tracking-tight leading-none">
            {Math.round(score)}
          </span>
          <span className="text-[10px] font-mono uppercase text-[#667085] mt-0.5">
            / 100
          </span>
        </div>
      </div>

      {showDetails && (
        <div className="mt-2 text-center">
          <span
            className="text-xs font-semibold font-sans uppercase px-2 py-0.5 rounded"
            style={{ color: riskColor, backgroundColor: `${riskColor}15` }}
          >
            {riskLevel === 'LOW' ? 'Low Signal' : riskLevel === 'MEDIUM' ? 'Review Required' : riskLevel === 'HIGH' ? 'High Signal' : 'Critical Signal'}
          </span>
          {confidence !== undefined && (
            <div className="text-[10px] font-mono text-[#667085] mt-1">
              Confidence: <strong>{Math.round(confidence)}%</strong>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
