import React, { useState } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { TopNav } from './TopNav';
import { CommandPalette } from '../common/CommandPalette';
import { User } from '../../types';

interface AppLayoutProps {
  currentUser: User | null;
  onUserChange: (user: User) => void;
}

export const AppLayout: React.FC<AppLayoutProps> = ({ currentUser, onUserChange }) => {
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const location = useLocation();

  const pathParts = location.pathname.split('/').filter(Boolean);
  const breadcrumbs = pathParts.length === 0 ? ['National Overview'] : pathParts.map((p) => p.replace('-', ' ').toUpperCase());

  return (
    <div className="min-h-screen bg-[#F7F8F6] text-[#172033] flex flex-col font-sans">
      <Sidebar />
      <TopNav
        onOpenSearch={() => setIsSearchOpen(true)}
        currentUser={currentUser}
        onUserChange={onUserChange}
      />

      <main className="ml-64 mt-16 p-8 flex-1 overflow-y-auto">
        {/* Breadcrumbs */}
        <div className="mb-6 flex items-center justify-between pb-3 border-b border-[#E5E7EB]">
          <div className="flex items-center gap-2 text-xs font-sans text-[#667085]">
            <span className="font-semibold text-[#102A43]">MPLAD GUARDIAN</span>
            {breadcrumbs.map((b, i) => (
              <React.Fragment key={i}>
                <span className="text-[#D1D5DB]">/</span>
                <span className={i === breadcrumbs.length - 1 ? 'text-[#172033] font-semibold' : ''}>
                  {decodeURIComponent(b)}
                </span>
              </React.Fragment>
            ))}
          </div>

          <div className="text-[11px] text-[#667085] hidden md:block">
            Public Development Monitoring & Decision Intelligence
          </div>
        </div>

        {/* Page Content */}
        <Outlet />
      </main>

      {/* Global Command Palette */}
      <CommandPalette isOpen={isSearchOpen} onClose={() => setIsSearchOpen(false)} />
    </div>
  );
};
