import React, { useState, useEffect } from 'react';
import { Search, Bell, ChevronDown, Check, LogOut, Shield } from 'lucide-react';
import { User, UserRole } from '../../types';
import { api } from '../../services/api';
import { useNavigate } from 'react-router-dom';

interface TopNavProps {
  onOpenSearch: () => void;
  currentUser: User | null;
  onUserChange: (user: User) => void;
}

export const TopNav: React.FC<TopNavProps> = ({ onOpenSearch, currentUser, onUserChange }) => {
  const [showUserDropdown, setShowUserDropdown] = useState(false);
  const [unreadAlerts, setUnreadAlerts] = useState<number>(0);
  const navigate = useNavigate();

  useEffect(() => {
    api.getAlerts({ status: 'OPEN', limit: 1 }).then((res) => {
      setUnreadAlerts(res.meta.total);
    }).catch(() => {});
  }, []);

  const switchRole = async (role: UserRole) => {
    try {
      const accounts = await api.getDemoAccounts();
      const target = accounts.accounts.find((a: any) => a.role === role);
      if (target) {
        const res = await api.login(target.username, target.default_password);
        localStorage.setItem('mplad_auth_token', res.access_token);
        onUserChange(res.user);
        setShowUserDropdown(false);
      }
    } catch {
      const mockUser: User = {
        id: `mock-${role.toLowerCase()}`,
        username: role.toLowerCase(),
        full_name: role === 'ADMIN' ? 'Executive Administrator' : role === 'ANALYST' ? 'Senior Oversight Analyst' : 'Public Viewer',
        email: `${role.toLowerCase()}@mpladguardian.gov.in`,
        role: role,
        department: 'Parliamentary Oversight Cell'
      };
      onUserChange(mockUser);
      setShowUserDropdown(false);
    }
  };

  return (
    <header className="h-16 bg-white border-b border-[#E5E7EB] fixed top-0 right-0 left-64 z-20 px-6 flex items-center justify-between shadow-card">
      {/* Search Input Bar */}
      <button
        onClick={onOpenSearch}
        className="flex items-center gap-2.5 px-3 py-1.5 bg-[#F7F8F6] hover:bg-[#F0F2ED] border border-[#E5E7EB] rounded text-[#667085] text-xs w-96 transition-colors"
      >
        <Search className="w-3.5 h-3.5 text-[#102A43]" />
        <span className="flex-1 text-left font-normal truncate">
          Search projects, constituencies, districts or MPs...
        </span>
        <kbd className="px-1.5 py-0.2 text-[10px] font-mono bg-white text-[#98A2B3] border border-[#E5E7EB] rounded">
          Ctrl+K
        </kbd>
      </button>

      {/* Right Controls */}
      <div className="flex items-center gap-5">
        {/* Data Freshness Indicator */}
        <div className="hidden lg:flex items-center gap-1.5 text-xs text-[#667085]">
          <span className="w-1.5 h-1.5 rounded-full bg-[#14804A]" />
          <span>Data updated: <strong className="text-[#172033] font-medium">23 Aug 2026</strong></span>
        </div>

        {/* Engine Operational Pill */}
        <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-0.5 rounded bg-[#EDF7F1] border border-[#D5EFE0] text-[#14804A] text-[11px] font-medium">
          <span>AI Engine: Operational</span>
        </div>

        {/* Alerts Button */}
        <button
          onClick={() => navigate('/alerts')}
          className="relative p-1.5 rounded text-[#667085] hover:text-[#172033] hover:bg-[#F7F8F6] border border-[#E5E7EB] transition-colors"
          title="Risk Signals Inbox"
        >
          <Bell className="w-4 h-4" />
          {unreadAlerts > 0 && (
            <span className="absolute -top-1 -right-1 px-1.5 py-0.2 text-[9px] font-mono font-bold bg-[#C2413B] text-white rounded-full">
              {unreadAlerts}
            </span>
          )}
        </button>

        {/* User Profile */}
        <div className="relative">
          <button
            onClick={() => setShowUserDropdown(!showUserDropdown)}
            className="flex items-center gap-2.5 p-1 pr-2 rounded hover:bg-[#F7F8F6] border border-[#E5E7EB] transition-all bg-white"
          >
            <div className="w-7 h-7 rounded bg-[#102A43] text-white flex items-center justify-center font-bold text-xs font-display">
              {currentUser?.role?.charAt(0) || 'A'}
            </div>
            <div className="text-left">
              <span className="text-xs font-semibold text-[#172033] block leading-tight">
                {currentUser?.full_name || 'Administrator'}
              </span>
              <span className="text-[10px] font-mono text-[#667085] uppercase tracking-wider block">
                {currentUser?.role || 'ADMIN'}
              </span>
            </div>
            <ChevronDown className="w-3.5 h-3.5 text-[#98A2B3] ml-0.5" />
          </button>

          {showUserDropdown && (
            <div className="absolute right-0 mt-2 w-64 bg-white border border-[#E5E7EB] rounded-lg shadow-dropdown overflow-hidden z-50 animate-fadeIn">
              <div className="p-3 border-b border-[#E5E7EB] bg-[#F7F8F6]">
                <span className="text-[10px] font-bold tracking-wider text-[#98A2B3] uppercase block mb-1">
                  Active Session
                </span>
                <p className="text-xs font-bold text-[#172033]">{currentUser?.full_name}</p>
                <p className="text-[11px] text-[#667085] font-mono truncate">{currentUser?.email}</p>
              </div>

              <div className="p-2 space-y-1">
                <span className="text-[10px] font-bold tracking-wider text-[#98A2B3] uppercase px-2 block mb-1">
                  Switch Role
                </span>
                {(['ADMIN', 'ANALYST', 'VIEWER'] as UserRole[]).map((r) => (
                  <button
                    key={r}
                    onClick={() => switchRole(r)}
                    className={`w-full flex items-center justify-between px-3 py-1.5 rounded text-xs font-medium transition-colors ${
                      currentUser?.role === r
                        ? 'bg-[#F0F4F8] text-[#102A43] font-bold'
                        : 'text-[#667085] hover:bg-[#F7F8F6] hover:text-[#172033]'
                    }`}
                  >
                    <span>{r}</span>
                    {currentUser?.role === r && <Check className="w-3.5 h-3.5 text-[#102A43]" />}
                  </button>
                ))}
              </div>

              <div className="p-2 border-t border-[#E5E7EB]">
                <button
                  onClick={() => {
                    localStorage.removeItem('mplad_auth_token');
                    navigate('/login');
                  }}
                  className="w-full flex items-center gap-2 px-3 py-1.5 text-xs text-[#C2413B] hover:bg-[#FDF2F2] rounded transition-colors text-left font-medium"
                >
                  <LogOut className="w-3.5 h-3.5" />
                  <span>Sign Out</span>
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
