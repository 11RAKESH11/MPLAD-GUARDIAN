import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import { User, UserRole } from '../types';
import { Shield, Lock, User as UserIcon, ArrowRight, CheckCircle2 } from 'lucide-react';

interface LoginPageProps {
  onLoginSuccess: (user: User) => void;
}

export const LoginPage: React.FC<LoginPageProps> = ({ onLoginSuccess }) => {
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('admin123');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleLogin = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const res = await api.login(username, password);
      localStorage.setItem('mplad_auth_token', res.access_token);
      onLoginSuccess(res.user);
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.message || 'Authentication failed. Please verify credentials.');
    } finally {
      setLoading(false);
    }
  };

  const quickRoleLogin = async (role: UserRole) => {
    const userMap: Record<UserRole, { u: string; p: string }> = {
      ADMIN: { u: 'admin', p: 'admin123' },
      ANALYST: { u: 'analyst', p: 'analyst123' },
      VIEWER: { u: 'viewer', p: 'viewer123' },
    };
    const creds = userMap[role];
    setUsername(creds.u);
    setPassword(creds.p);
    setLoading(true);
    setError('');
    try {
      const res = await api.login(creds.u, creds.p);
      localStorage.setItem('mplad_auth_token', res.access_token);
      onLoginSuccess(res.user);
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.message || 'Login failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F7F8F6] flex items-center justify-center p-4 lg:p-8 font-sans">
      <div className="w-full max-w-4xl bg-white border border-[#E5E7EB] rounded-xl shadow-dropdown overflow-hidden grid grid-cols-1 lg:grid-cols-12 min-h-[560px]">
        {/* Left Side: Deep Navy Civic Brand Hero */}
        <div className="lg:col-span-6 bg-[#102A43] p-8 lg:p-12 text-white flex flex-col justify-between relative overflow-hidden">
          <div className="space-y-6 relative z-10">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded bg-white/10 border border-white/20 flex items-center justify-center">
                <Shield className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="font-extrabold text-base tracking-tight text-white font-display">
                  MPLAD GUARDIAN
                </h1>
                <span className="text-[10px] text-slate-300 tracking-wider uppercase font-sans">
                  National Development Intelligence
                </span>
              </div>
            </div>

            <div className="space-y-3 pt-6">
              <h2 className="text-2xl font-bold tracking-tight leading-snug font-display">
                Public Development Monitoring & Decision Intelligence
              </h2>
              <p className="text-xs text-slate-300 leading-relaxed font-normal">
                Continuous oversight of public MPLADS developmental expenditure across 36 States & UTs through verified data validation, statistical anomaly detection, and explainable risk analytics.
              </p>
            </div>

            <div className="space-y-2.5 pt-4">
              <div className="flex items-center gap-2 text-xs text-slate-300">
                <CheckCircle2 className="w-4 h-4 text-[#14804A]" />
                <span>374,141 verified primary records analyzed</span>
              </div>
              <div className="flex items-center gap-2 text-xs text-slate-300">
                <CheckCircle2 className="w-4 h-4 text-[#14804A]" />
                <span>Zero synthetic fabrication of GPS coordinates</span>
              </div>
              <div className="flex items-center gap-2 text-xs text-slate-300">
                <CheckCircle2 className="w-4 h-4 text-[#14804A]" />
                <span>Explainable MAD + Z-score anomaly scoring</span>
              </div>
            </div>
          </div>

          <div className="pt-8 border-t border-white/10 flex items-center justify-between text-[11px] text-slate-400 font-sans">
            <span>Decision Support System</span>
            <span className="font-mono text-slate-400">Govt of India</span>
          </div>
        </div>

        {/* Right Side: Clean Authentication Panel */}
        <div className="lg:col-span-6 p-8 lg:p-12 flex flex-col justify-between bg-white space-y-6">
          <div className="space-y-6">
            <div>
              <h3 className="text-xl font-bold text-[#172033] tracking-tight font-display">
                Sign In to Command Center
              </h3>
              <p className="text-xs text-[#667085] mt-1">
                Enter your credentials or select an evaluation role below
              </p>
            </div>

            <form onSubmit={handleLogin} className="space-y-4 text-xs">
              {error && (
                <div className="p-3 bg-[#FDF2F2] border border-[#F9DFDF] text-[#C2413B] rounded text-xs">
                  {error}
                </div>
              )}

              <div className="space-y-1.5">
                <label className="text-[#667085] uppercase font-bold text-[10px] tracking-wider block">
                  Username
                </label>
                <div className="relative">
                  <UserIcon className="w-4 h-4 text-[#98A2B3] absolute left-3 top-1/2 -translate-y-1/2" />
                  <input
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    className="w-full pl-9 pr-3 py-2 bg-[#F7F8F6] border border-[#E5E7EB] rounded text-[#172033] focus:outline-none focus:border-[#102A43]"
                    required
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <label className="text-[#667085] uppercase font-bold text-[10px] tracking-wider block">
                  Password
                </label>
                <div className="relative">
                  <Lock className="w-4 h-4 text-[#98A2B3] absolute left-3 top-1/2 -translate-y-1/2" />
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full pl-9 pr-3 py-2 bg-[#F7F8F6] border border-[#E5E7EB] rounded text-[#172033] focus:outline-none focus:border-[#102A43]"
                    required
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full py-2.5 bg-[#102A43] hover:bg-[#193354] text-white font-bold rounded shadow-xs inline-flex items-center justify-center gap-2 transition-colors"
              >
                <span>{loading ? 'Authenticating...' : 'Sign In'}</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </form>

            {/* Quick Roles */}
            <div className="pt-4 border-t border-[#E5E7EB] space-y-2">
              <span className="text-[10px] uppercase font-bold text-[#98A2B3] tracking-wider block">
                1-Click Quick Roles
              </span>

              <div className="grid grid-cols-3 gap-2 text-xs">
                <button
                  type="button"
                  onClick={() => quickRoleLogin('ADMIN')}
                  className="p-2 bg-[#F7F8F6] hover:bg-[#F0F4F8] border border-[#E5E7EB] hover:border-[#102A43] rounded text-center transition-colors"
                >
                  <strong className="text-[#102A43] block text-[11px]">ADMIN</strong>
                  <span className="text-[9px] text-[#667085] block">Executive</span>
                </button>

                <button
                  type="button"
                  onClick={() => quickRoleLogin('ANALYST')}
                  className="p-2 bg-[#F7F8F6] hover:bg-[#FEF8EE] border border-[#E5E7EB] hover:border-[#C27A00] rounded text-center transition-colors"
                >
                  <strong className="text-[#C27A00] block text-[11px]">ANALYST</strong>
                  <span className="text-[9px] text-[#667085] block">Oversight</span>
                </button>

                <button
                  type="button"
                  onClick={() => quickRoleLogin('VIEWER')}
                  className="p-2 bg-[#F7F8F6] hover:bg-[#EDF7F1] border border-[#E5E7EB] hover:border-[#14804A] rounded text-center transition-colors"
                >
                  <strong className="text-[#14804A] block text-[11px]">VIEWER</strong>
                  <span className="text-[9px] text-[#667085] block">Public</span>
                </button>
              </div>
            </div>
          </div>

          <div className="text-center text-[10px] text-[#98A2B3]">
            Official Decision-Support & Anomaly Detection Platform • Govt of India
          </div>
        </div>
      </div>
    </div>
  );
};
