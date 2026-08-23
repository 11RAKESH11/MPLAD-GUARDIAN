import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  MapPin,
  FileSpreadsheet,
  AlertOctagon,
  Building2,
  Users2,
  Database,
  SlidersHorizontal,
  FileText,
  GitCompare,
  Shield,
  ShieldCheck
} from 'lucide-react';

export const Sidebar: React.FC = () => {
  const navSections = [
    {
      title: 'OVERVIEW',
      items: [
        { label: 'National Pulse', path: '/dashboard', icon: LayoutDashboard },
        { label: 'National GIS Map', path: '/risk-map', icon: MapPin },
      ],
    },
    {
      title: 'DEVELOPMENT',
      items: [
        { label: 'Projects Explorer', path: '/projects', icon: FileSpreadsheet },
        { label: 'States & Districts', path: '/analytics/states', icon: Building2 },
        { label: 'MP Portfolios', path: '/mps', icon: Users2 },
        { label: 'Compare Indicators', path: '/compare', icon: GitCompare },
      ],
    },
    {
      title: 'MONITORING & DECISION',
      items: [
        { label: 'Priority Review Queue', path: '/alerts', icon: AlertOctagon, badge: '270' },
        { label: 'Data Quality & Health', path: '/data-quality', icon: Database },
      ],
    },
    {
      title: 'GOVERNANCE & AUDIT',
      items: [
        { label: 'System Audit Trail', path: '/audit', icon: ShieldCheck },
        { label: 'Reports & Briefs', path: '/reports', icon: FileText },
        { label: 'Platform Settings', path: '/settings', icon: SlidersHorizontal },
      ],
    },
  ];

  return (
    <aside className="w-64 bg-white border-r border-[#E5E7EB] flex flex-col h-screen fixed left-0 top-0 z-30 select-none">
      {/* Brand Header */}
      <div className="p-5 border-b border-[#E5E7EB] flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded bg-[#102A43] flex items-center justify-center relative shadow-xs">
            <Shield className="w-4 h-4 text-white" />
          </div>
          <div>
            <h1 className="font-bold text-sm tracking-tight text-[#102A43] font-display">
              MPLAD GUARDIAN
            </h1>
            <span className="text-[10px] text-[#667085] tracking-tight font-sans block">
              National Development Intelligence
            </span>
          </div>
        </div>
      </div>

      {/* Navigation Sections */}
      <div className="flex-1 overflow-y-auto px-3 py-3 space-y-4">
        {navSections.map((sec, idx) => (
          <div key={idx} className="space-y-1">
            <span className="text-[10px] font-sans font-bold tracking-wider text-[#98A2B3] px-3 uppercase">
              {sec.title}
            </span>
            <div className="space-y-0.5 pt-0.5">
              {sec.items.map((item) => {
                const Icon = item.icon;
                return (
                  <NavLink
                    key={item.path}
                    to={item.path}
                    className={({ isActive }) =>
                      `flex items-center justify-between px-3 py-1.5 rounded text-xs font-medium transition-colors ${
                        isActive
                          ? 'bg-[#F0F4F8] text-[#102A43] font-semibold border-l-2 border-[#102A43]'
                          : 'text-[#667085] hover:text-[#172033] hover:bg-[#F7F8F6]'
                      }`
                    }
                  >
                    <div className="flex items-center gap-2.5">
                      <Icon className="w-4 h-4 opacity-75" />
                      <span>{item.label}</span>
                    </div>
                    {item.badge && (
                      <span className="px-1.5 py-0.2 text-[10px] font-mono font-semibold bg-[#FDF2F2] text-[#C2413B] border border-[#F9DFDF] rounded">
                        {item.badge}
                      </span>
                    )}
                  </NavLink>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      {/* System Status Footer */}
      <div className="p-4 border-t border-[#E5E7EB] bg-[#F7F8F6] space-y-1.5 text-xs text-[#667085]">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5 text-[11px] font-medium text-[#172033]">
            <span className="w-2 h-2 rounded-full bg-[#14804A]" />
            <span>AI Engine: Operational</span>
          </div>
        </div>
        <div className="text-[11px] flex items-center justify-between">
          <span>Records Ingested</span>
          <strong className="text-[#172033] font-mono">374,141</strong>
        </div>
        <div className="text-[10px] font-mono text-[#98A2B3]">
          ● Data updated 23 Aug 2026
        </div>
      </div>
    </aside>
  );
};
