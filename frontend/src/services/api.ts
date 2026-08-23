import { DashboardOverview, NarrativeInsight, Project, Pagination, StateSummary, MPPortfolio, AlertRecord, DataQualitySummary, User, EvidenceData, RelationshipGraphData, AuditLogRecord } from '../types';

const API_BASE = '/api';

function getAuthHeader(): HeadersInit {
  const token = localStorage.getItem('mplad_auth_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errorMsg = `HTTP Error ${res.status}`;
    try {
      const json = await res.json();
      errorMsg = json.detail || json.message || errorMsg;
    } catch {
      // ignore
    }
    throw new Error(errorMsg);
  }
  return res.json();
}

export const api = {
  // Auth
  login: async (username: string, password: string): Promise<{ access_token: string; user: User }> => {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });
    return handleResponse(res);
  },

  getMe: async (): Promise<User> => {
    const res = await fetch(`${API_BASE}/auth/me`, {
      headers: getAuthHeader(),
    });
    return handleResponse(res);
  },

  getDemoAccounts: async () => {
    const res = await fetch(`${API_BASE}/auth/demo-accounts`);
    return handleResponse<{ accounts: any[] }>(res);
  },

  // Dashboard
  getDashboardOverview: async (): Promise<DashboardOverview> => {
    const res = await fetch(`${API_BASE}/dashboard/overview`, {
      headers: getAuthHeader(),
    });
    return handleResponse(res);
  },

  getDashboardInsights: async (): Promise<{ insights: NarrativeInsight[] }> => {
    const res = await fetch(`${API_BASE}/dashboard/insights`, {
      headers: getAuthHeader(),
    });
    return handleResponse(res);
  },

  getDashboardTrends: async (): Promise<any> => {
    const res = await fetch(`${API_BASE}/dashboard/trends`, {
      headers: getAuthHeader(),
    });
    return handleResponse(res);
  },

  // Projects
  getProjects: async (params: Record<string, any> = {}): Promise<{ data: Project[]; pagination: Pagination }> => {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([key, val]) => {
      if (val !== undefined && val !== null && val !== '') {
        query.append(key, String(val));
      }
    });
    const res = await fetch(`${API_BASE}/projects?${query.toString()}`, {
      headers: getAuthHeader(),
    });
    return handleResponse(res);
  },

  getProjectDetail: async (workCode: string): Promise<Project> => {
    const res = await fetch(`${API_BASE}/projects/${encodeURIComponent(workCode)}`, {
      headers: getAuthHeader(),
    });
    return handleResponse(res);
  },

  getProjectRelationships: async (workCode: string): Promise<RelationshipGraphData> => {
    const res = await fetch(`${API_BASE}/projects/${encodeURIComponent(workCode)}/relationships`, {
      headers: getAuthHeader(),
    });
    return handleResponse(res);
  },

  getProjectLineage: async (workCode: string): Promise<any> => {
    const res = await fetch(`${API_BASE}/projects/${encodeURIComponent(workCode)}/lineage`, {
      headers: getAuthHeader(),
    });
    return handleResponse(res);
  },

  // Risks & Map
  getRiskSummary: async (): Promise<any> => {
    const res = await fetch(`${API_BASE}/risks/summary`, {
      headers: getAuthHeader(),
    });
    return handleResponse(res);
  },

  getRiskMapData: async (): Promise<{ states: any[]; disclaimer: string }> => {
    const res = await fetch(`${API_BASE}/risks/map`, {
      headers: getAuthHeader(),
    });
    return handleResponse(res);
  },

  getAnalyticsMapData: async (params: Record<string, any> = {}): Promise<{ states: any[]; national: any; disclaimer: string }> => {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([key, val]) => {
      if (val !== undefined && val !== null && val !== '') {
        query.append(key, String(val));
      }
    });
    const res = await fetch(`${API_BASE}/analytics/map?${query.toString()}`, {
      headers: getAuthHeader(),
    });
    return handleResponse(res);
  },

  getStateMapDetails: async (state: string): Promise<{ state: string; code: string; districts: any[]; categories: any[]; disclaimer: string }> => {
    const res = await fetch(`${API_BASE}/analytics/map/state/${encodeURIComponent(state)}`, {
      headers: getAuthHeader(),
    });
    return handleResponse(res);
  },

  getDistrictMapData: async (state: string): Promise<{ state: string; districts: any[] }> => {
    const res = await fetch(`${API_BASE}/risks/map/districts?state=${encodeURIComponent(state)}`, {
      headers: getAuthHeader(),
    });
    return handleResponse(res);
  },

  analyzeCustomProject: async (payload: any): Promise<any> => {
    const res = await fetch(`${API_BASE}/risks/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
      body: JSON.stringify(payload),
    });
    return handleResponse(res);
  },

  // States
  getStates: async (): Promise<{ states: StateSummary[] }> => {
    const res = await fetch(`${API_BASE}/states`, {
      headers: getAuthHeader(),
    });
    return handleResponse(res);
  },

  getStateDetail: async (stateName: string): Promise<any> => {
    const res = await fetch(`${API_BASE}/states/${encodeURIComponent(stateName)}`, {
      headers: getAuthHeader(),
    });
    return handleResponse(res);
  },

  // MPs
  getMps: async (params: Record<string, any> = {}): Promise<{ data: MPPortfolio[]; pagination: Pagination }> => {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([key, val]) => {
      if (val !== undefined && val !== null && val !== '') {
        query.append(key, String(val));
      }
    });
    const res = await fetch(`${API_BASE}/mps?${query.toString()}`, {
      headers: getAuthHeader(),
    });
    return handleResponse(res);
  },

  getMpDetail: async (mpId: string): Promise<MPPortfolio> => {
    const res = await fetch(`${API_BASE}/mps/${encodeURIComponent(mpId)}`, {
      headers: getAuthHeader(),
    });
    return handleResponse(res);
  },

  // Alerts & Evidence
  getAlerts: async (params: Record<string, any> = {}): Promise<{ data: AlertRecord[]; summary: any; pagination: Pagination }> => {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([key, val]) => {
      if (val !== undefined && val !== null && val !== '') {
        query.append(key, String(val));
      }
    });
    const res = await fetch(`${API_BASE}/alerts?${query.toString()}`, {
      headers: getAuthHeader(),
    });
    return handleResponse(res);
  },

  getAlertDetail: async (alertId: string): Promise<AlertRecord> => {
    const res = await fetch(`${API_BASE}/alerts/${encodeURIComponent(alertId)}`, {
      headers: getAuthHeader(),
    });
    return handleResponse(res);
  },

  getAlertEvidence: async (alertId: string): Promise<EvidenceData> => {
    const res = await fetch(`${API_BASE}/alerts/${encodeURIComponent(alertId)}/evidence`, {
      headers: getAuthHeader(),
    });
    return handleResponse(res);
  },

  updateAlertStatus: async (alertId: string, status: string, resolution_notes: string = '', assigned_to: string = '') => {
    const res = await fetch(`${API_BASE}/alerts/${encodeURIComponent(alertId)}/status`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
      body: JSON.stringify({ status, resolution_notes, assigned_to }),
    });
    return handleResponse(res);
  },

  // Data Quality
  getDataQualitySummary: async (): Promise<DataQualitySummary> => {
    const res = await fetch(`${API_BASE}/data-quality/summary`, {
      headers: getAuthHeader(),
    });
    return handleResponse(res);
  },

  // Audit Logs
  getAuditLogs: async (params: Record<string, any> = {}): Promise<{ logs: AuditLogRecord[]; pagination: Pagination }> => {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([key, val]) => {
      if (val !== undefined && val !== null && val !== '') {
        query.append(key, String(val));
      }
    });
    const res = await fetch(`${API_BASE}/audit-logs?${query.toString()}`, {
      headers: getAuthHeader(),
    });
    return handleResponse(res);
  },
};
