import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, MapPin, AlertCircle, FileText, BarChart3, Database, ShieldCheck, X } from 'lucide-react';
import { api } from '../../services/api';

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
}

export const CommandPalette: React.FC<CommandPaletteProps> = ({ isOpen, onClose }) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        isOpen ? onClose() : null;
      }
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  useEffect(() => {
    if (!query.trim()) {
      setResults([]);
      return;
    }
    const timer = setTimeout(async () => {
      setLoading(true);
      try {
        const res = await api.getProjects({ q: query, limit: 5 });
        setResults(res.data);
      } catch {
        setResults([]);
      } finally {
        setLoading(false);
      }
    }, 200);
    return () => clearTimeout(timer);
  }, [query]);

  if (!isOpen) return null;

  const quickNav = [
    { label: 'Executive Overview', path: '/dashboard', icon: BarChart3 },
    { label: 'National Risk Command Map', path: '/risk-map', icon: MapPin },
    { label: 'Project Intelligence Explorer', path: '/projects', icon: FileText },
    { label: 'Alert Management Center', path: '/alerts', icon: AlertCircle },
    { label: 'State & Regional Intelligence', path: '/analytics/states', icon: MapPin },
    { label: 'Parliamentarian Dossiers', path: '/mps', icon: ShieldCheck },
    { label: 'Data Quality & Health Center', path: '/data-quality', icon: Database },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-20 px-4 bg-[#0B1626]/50 backdrop-blur-sm animate-fadeIn">
      <div
        className="w-full max-w-2xl bg-white border border-[#D9DED8] rounded-xl shadow-civicLg overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center px-4 py-3 border-b border-[#E1E5E1] bg-[#F8F9F8]">
          <Search className="w-4 h-4 text-[#10243E] mr-3" />
          <input
            autoFocus
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search projects, MPs, districts, states, work codes... (e.g. WS/MP620, Dharwad)"
            className="flex-1 bg-transparent border-none text-[#17202A] placeholder-[#7B8794] focus:outline-none text-xs font-mono"
          />
          {query && (
            <button onClick={() => setQuery('')} className="p-1 text-[#7B8794] hover:text-[#17202A]">
              <X className="w-3.5 h-3.5" />
            </button>
          )}
          <kbd className="ml-2 px-2 py-0.5 text-[10px] font-mono bg-[#EAF0F6] text-[#10243E] border border-[#D1DFEC] rounded">
            ESC
          </kbd>
        </div>

        <div className="max-h-96 overflow-y-auto p-2 divide-y divide-[#E1E5E1]">
          {!query && (
            <div className="p-2">
              <span className="text-[10px] font-bold uppercase tracking-wider text-[#7B8794] px-2 block mb-1">
                Quick Navigation
              </span>
              <div className="space-y-0.5">
                {quickNav.map((item) => {
                  const Icon = item.icon;
                  return (
                    <button
                      key={item.path}
                      onClick={() => {
                        navigate(item.path);
                        onClose();
                      }}
                      className="w-full flex items-center gap-3 px-3 py-2 text-xs text-[#52606D] hover:text-[#10243E] hover:bg-[#EAF0F6] rounded-md transition-colors text-left"
                    >
                      <Icon className="w-4 h-4 text-[#167D7F]" />
                      <span className="font-medium">{item.label}</span>
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {loading ? (
            <div className="py-8 text-center text-xs text-[#7B8794]">Searching records...</div>
          ) : results.length > 0 ? (
            <div className="p-2 space-y-1">
              <span className="text-[10px] font-bold uppercase tracking-wider text-[#7B8794] px-2 block mb-1">
                Matching Projects ({results.length})
              </span>
              {results.map((p) => (
                <div
                  key={p.work_code}
                  onClick={() => {
                    navigate(`/projects/${encodeURIComponent(p.work_code)}`);
                    onClose();
                  }}
                  className="p-3 hover:bg-[#F1F3F0] rounded-md cursor-pointer transition-colors border border-transparent hover:border-[#D9DED8]"
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-mono text-xs text-[#10243E] font-bold">{p.work_code}</span>
                    <span className="text-[11px] text-[#52606D]">{p.state} • {p.district}</span>
                  </div>
                  <p className="text-xs text-[#17202A] mt-1 line-clamp-1">{p.work_type || p.description}</p>
                </div>
              ))}
            </div>
          ) : query && !loading ? (
            <div className="py-8 text-center text-xs text-[#7B8794]">No matching records found.</div>
          ) : null}
        </div>
      </div>
    </div>
  );
};
