export type RiskLevel = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
export type SourceBadgeType = 'REAL CSV DATA' | 'OFFICIAL SOURCE' | 'DERIVED ANALYTICS' | 'AI ANALYSIS' | 'DEMO DATA';
export type AlertSeverity = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
export type AlertStatus = 'OPEN' | 'UNDER_REVIEW' | 'EVIDENCE_REQUESTED' | 'VALIDATED' | 'NOT_SUBSTANTIATED' | 'RESOLVED' | 'CLOSED' | 'ACKNOWLEDGED';
export type UserRole = 'ADMIN' | 'ANALYST' | 'VIEWER';

export interface User {
  id: string;
  username: string;
  full_name: string;
  email: string;
  role: UserRole;
  department: string;
}

export interface Project {
  id: string;
  work_code: string;
  house: 'LOK_SABHA' | 'RAJYA_SABHA';
  mp_code: string;
  mp_name: string;
  mp_type: string;
  state: string;
  district: string;
  constituency: string;
  ida_name: string;
  category: string;
  work_type: string;
  description: string;
  status: string;
  recommended_date: string | null;
  sanction_date: string | null;
  completion_date: string | null;
  financial_year: string;
  recommended_amount: number;
  sanctioned_amount: number;
  disbursed_amount: number;
  expenditure_amount: number;
  utilization_pct: number;
  vendor_count: number;
  voucher_count: number;
  has_image: number;
  
  // Joined risk fields
  overall_risk_score: number;
  risk_level: RiskLevel;
  confidence: number;
  cost_anomaly_score: number;
  duplicate_score: number;
  progress_gap_score: number;
  geographic_score: number;
  data_quality_score?: number;
  coverage_pct?: number;
  cost_zscore?: number;
  cost_mad_score?: number;
  comparison_group_size?: number;
  explanation_json?: RiskExplanation;
  recommendation?: string;
  model_version?: string;
  calculated_at?: string;
  
  // Detailed fields
  raw_data?: Record<string, any>;
  vouchers?: ExpenditureVoucher[];
  comparable_projects?: ComparableProject[];
  traceability?: TraceabilityInfo;
}

export interface RiskContributor {
  name: string;
  score: number;
  weight: number;
  detail: string;
}

export interface RiskExplanation {
  summary: string;
  why_flagged: string[];
  contributors: RiskContributor[];
  recommendation: string;
  disclaimer: string;
}

export interface ComparableProject {
  comparable_work_code: string;
  similarity_score: number;
  similarity_type: string;
  reason: string;
  work_type?: string;
  state?: string;
  district?: string;
  sanctioned_amount?: number;
  status?: string;
  overall_risk_score?: number;
  risk_level?: RiskLevel;
}

export interface ExpenditureVoucher {
  id: number;
  work_code: string;
  state: string;
  ida_name: string;
  mp_name: string;
  constituency: string;
  expenditure_date: string;
  vendor_name: string;
  payment_status: string;
  disbursed_amount: number;
  house: string;
}

export interface TraceabilityInfo {
  source_type: string;
  house: string;
  primary_id: string;
  has_recommended_record: boolean;
  has_sanctioned_record: boolean;
  has_completed_record: boolean;
  voucher_count: number;
  last_synced: string;
}

export interface DashboardOverview {
  kpis: {
    total_projects: number;
    total_sanctioned_funds: number;
    total_recommended_funds: number;
    total_expenditure_funds: number;
    total_disbursed_funds: number;
    utilization_rate_pct: number;
    completion_rate_pct?: number;
    completed_works: number;
    sanctioned_works: number;
    inspection_works: number;
    vendor_id_works: number;
    total_mps: number;
    total_vouchers: number;
    total_unique_vendors: number;
    source_badge: SourceBadgeType;
  };
  risk_metrics: {
    critical_count: number;
    high_count: number;
    medium_count: number;
    low_count: number;
    potential_duplicates_count: number;
    avg_risk_score: number;
    avg_confidence: number;
    source_badge: SourceBadgeType;
  };
  alerts_summary: {
    total_alerts: number;
    open_alerts: number;
    ack_alerts: number;
    resolved_alerts: number;
  };
  data_health: {
    completeness_pct: number;
    source_files_count: number;
    total_raw_rows: number;
    status: string;
    last_analysis: string;
  };
}

export interface NarrativeInsight {
  id: string;
  type: string;
  title: string;
  summary: string;
  impact: string;
  action: string;
  filter_state?: string;
  filter_district?: string;
  severity: AlertSeverity;
  badge: string;
}

export interface StateSummary {
  state: string;
  total_projects: number;
  total_districts: number;
  total_constituencies: number;
  total_mps: number;
  total_recommended: number;
  total_sanctioned: number;
  total_expenditure: number;
  completed_works: number;
  high_risk_count: number;
  avg_risk_score: number;
  utilization_pct: number;
  completion_pct: number;
}

export interface MPPortfolio {
  id: string;
  name: string;
  house: string;
  state: string;
  constituency: string;
  mp_type: string;
  allocated_limit: number;
  calamity_consent_amount: number;
  total_recommended_works: number;
  total_sanctioned_works: number;
  total_completed_works: number;
  total_sanctioned_amount: number;
  total_expenditure_amount: number;
  avg_risk_score: number;
  created_at: string;
  projects?: Project[];
  category_portfolio?: { category: string; count: number; total_sanctioned: number }[];
}

export interface AlertRecord {
  id: string;
  work_code: string;
  alert_type: string;
  title: string;
  severity: AlertSeverity;
  status: AlertStatus;
  state: string;
  district: string;
  evidence: string;
  impact: string;
  action_recommendation: string;
  assigned_to?: string | null;
  priority_score?: number;
  acknowledged_by?: string | null;
  acknowledged_at?: string | null;
  resolved_by?: string | null;
  resolved_at?: string | null;
  resolution_notes?: string | null;
  created_at: string;
  project_id?: string;
  sanctioned_amount?: number;
  expenditure_amount?: number;
  disbursed_amount?: number;
  recommended_amount?: number;
  mp_name?: string;
  category?: string;
  work_type?: string;
  financial_year?: string;
  project_description?: string;
  project_status?: string;
  overall_risk_score?: number;
  confidence?: number;
  cost_anomaly_score?: number;
  duplicate_score?: number;
  progress_gap_score?: number;
  explanation_json?: any;
}

export interface EvidenceData {
  alert: AlertRecord & Record<string, any>;
  comparables: ComparableProject[];
  vouchers: ExpenditureVoucher[];
  audit_history: AuditLogRecord[];
  peer_benchmark: {
    peer_count: number;
    peer_avg_cost: number;
    peer_min_cost: number;
    peer_max_cost: number;
    current_cost: number;
    z_score: number;
    mad_score: number;
  };
  recommended_checklist: {
    id: string;
    step: string;
    done: boolean;
  }[];
  lineage: {
    tier_1_dashboard: string;
    tier_2_api: string;
    tier_3_db_table: string;
    tier_4_normalized_id: string;
    tier_5_source_file: string;
  };
  disclaimer: string;
}

export interface RelationshipNode {
  id: string;
  title: string;
  category?: string;
  state?: string;
  district?: string;
  sanctioned_amount?: number;
  risk_level?: RiskLevel;
  risk_score?: number;
  is_target?: boolean;
}

export interface RelationshipEdge {
  source: string;
  target: string;
  relation_type: string;
  similarity: number;
  label: string;
}

export interface RelationshipGraphData {
  target_work_code: string;
  nodes: RelationshipNode[];
  edges: RelationshipEdge[];
}

export interface AuditLogRecord {
  id: number;
  user_id: string;
  username: string;
  user_role: string;
  action: string;
  target_type: string;
  target_id: string;
  previous_state: string;
  new_state: string;
  notes: string;
  created_at: string;
}

export interface DataQualityIssue {
  id: number;
  issue_type: string;
  severity: string;
  file_name: string;
  source_identifier: string;
  field_name: string;
  invalid_value: string;
  description: string;
  created_at: string;
}

export interface DataQualitySummary {
  overall_health_score: number;
  completeness_pct: number;
  validity_pct: number;
  uniqueness_pct: number;
  cross_linkage_pct: number;
  metrics: {
    total_records_monitored: number;
    missing_descriptions: number;
    missing_districts: number;
    missing_mp_names: number;
    zero_amount_records: number;
    handled_footer_totals: number;
    raw_gps_coordinates_status: string;
  };
  issues_registry: DataQualityIssue[];
}

export interface Pagination {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
}

export interface AttentionItem {
  alert_id: string;
  work_code: string;
  signal_type: string;
  raw_signal_type?: string;
  title: string;
  severity: AlertSeverity;
  state: string;
  district: string;
  category: string;
  sanctioned_amount: number;
  risk_score: number;
  confidence: number;
  priority_score: number;
  evidence_snippet: string;
  why_prioritized: string;
  status: AlertStatus;
}

export interface FundFlowStage {
  id: string;
  name: string;
  amount: number;
  records_count: number;
  percentage_of_sanctioned: number;
  description: string;
  source: string;
}

export interface FundFlowResponse {
  stages: FundFlowStage[];
  total_sanctioned: number;
  total_expenditure: number;
  utilization_rate_pct: number;
}

export interface SignalDistributionItem {
  type_key: string;
  label: string;
  count: number;
  critical_count: number;
}

export interface SignalDistributionResponse {
  signals: SignalDistributionItem[];
  total_alerts: number;
  overlap_note: string;
  risk_distribution: {
    critical?: number;
    high?: number;
    medium?: number;
    low?: number;
  };
  confidence_distribution: {
    high_confidence?: number;
    moderate_confidence?: number;
    limited_evidence?: number;
  };
}

export interface WhatChangedMetric {
  name: string;
  current: number;
  previous: number;
  diff_pct: number;
  explanation: string;
  neutral_note: string;
}

export interface WhatChangedResponse {
  historical_comparison_available: boolean;
  current_period?: string;
  previous_period?: string;
  comparison_label?: string;
  metrics?: WhatChangedMetric[];
  message?: string;
}

export interface StateIndicatorItem {
  state: string;
  total_projects: number;
  total_sanctioned: number;
  total_expenditure: number;
  utilization_rate_pct: number;
  completion_rate_pct: number;
  signal_count: number;
}

export interface StateIndicatorsResponse {
  states: StateIndicatorItem[];
}
