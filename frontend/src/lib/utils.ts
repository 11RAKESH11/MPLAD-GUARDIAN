import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { RiskLevel } from '../types';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatCurrency(amount: number | string | null | undefined): string {
  if (amount === null || amount === undefined || isNaN(Number(amount))) return '₹0';
  const num = Number(amount);
  const abs = Math.abs(num);
  if (abs >= 10000000) {
    const cr = num / 10000000;
    return `₹${cr.toLocaleString('en-IN', { minimumFractionDigits: cr % 1 === 0 ? 0 : 2, maximumFractionDigits: 2 })} Cr`;
  }
  if (abs >= 100000) {
    const l = num / 100000;
    return `₹${l.toLocaleString('en-IN', { minimumFractionDigits: l % 1 === 0 ? 0 : 2, maximumFractionDigits: 2 })} L`;
  }
  return `₹${num.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`;
}

export function formatExactCurrency(amount: number | string | null | undefined): string {
  if (amount === null || amount === undefined || isNaN(Number(amount))) return '₹0';
  return `₹${Number(amount).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`;
}

export function formatNumber(val: number | string | null | undefined): string {
  if (val === null || val === undefined || isNaN(Number(val))) return '0';
  return Number(val).toLocaleString('en-IN');
}

export function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr || dateStr.trim() === '') return '—';
  try {
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return dateStr;
    return d.toLocaleDateString('en-IN', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
    });
  } catch {
    return dateStr;
  }
}

export function getRiskBadgeClass(level: RiskLevel): string {
  switch (level) {
    case 'CRITICAL':
      return 'bg-[#FBF0F0] text-[#8F1D1D] border-[#F5DCDC] font-medium';
    case 'HIGH':
      return 'bg-[#FDF2F2] text-[#C2413B] border-[#F9DFDF] font-medium';
    case 'MEDIUM':
      return 'bg-[#FEF8EE] text-[#C27A00] border-[#FDF1DD] font-medium';
    case 'LOW':
      return 'bg-[#EDF7F1] text-[#14804A] border-[#D5EFE0] font-medium';
    default:
      return 'bg-slate-100 text-slate-700 border-slate-200';
  }
}

export function getRiskHex(level: RiskLevel): string {
  switch (level) {
    case 'CRITICAL':
      return '#8F1D1D';
    case 'HIGH':
      return '#C2413B';
    case 'MEDIUM':
      return '#C27A00';
    case 'LOW':
      return '#14804A';
    default:
      return '#667085';
  }
}
