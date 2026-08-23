import React from 'react';
import { Search, RefreshCw } from 'lucide-react';

interface EmptyStateProps {
  title?: string;
  description?: string;
  actionText?: string;
  onAction?: () => void;
  icon?: React.ReactNode;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title = 'No Records Found',
  description = 'No items matched the selected filters or search query.',
  actionText,
  onAction,
  icon,
}) => (
  <div className="civic-card p-12 text-center flex flex-col items-center justify-center my-6">
    <div className="p-3 rounded-full bg-[#F1F3F0] text-[#52606D] mb-3">
      {icon || <Search className="w-6 h-6 text-[#10243E]" />}
    </div>
    <h3 className="text-base font-bold text-[#17202A] mb-1 font-display">{title}</h3>
    <p className="text-xs text-[#52606D] max-w-md mb-5 leading-relaxed">{description}</p>
    {actionText && onAction && (
      <button
        onClick={onAction}
        className="inline-flex items-center gap-2 px-4 py-2 bg-[#10243E] hover:bg-[#193354] text-white text-xs font-semibold rounded-md shadow-civic transition-colors"
      >
        <RefreshCw className="w-3.5 h-3.5" />
        <span>{actionText}</span>
      </button>
    )}
  </div>
);
