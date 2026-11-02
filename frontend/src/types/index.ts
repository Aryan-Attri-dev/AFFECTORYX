export interface UserOrgMembership {
  organization_id: string;
  organization_name: string;
  organization_slug: string;
  role: "owner" | "admin" | "member" | "viewer";
}

export interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
  memberships: UserOrgMembership[];
}

export interface Organization {
  id: string;
  name: string;
  slug: string;
  description?: string;
  created_at: string;
  updated_at: string;
  user_role?: string;
  member_count: number;
  project_count: number;
}

export interface Member {
  membership_id: string;
  user_id: string;
  email: string;
  full_name: string;
  role: "owner" | "admin" | "member" | "viewer";
  joined_at: string;
}

export interface Project {
  id: string;
  organization_id: string;
  name: string;
  slug: string;
  description?: string;
  repository_url?: string;
  default_branch: string;
  environments: string[];
  metadata_info: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface AuditLog {
  id: string;
  organization_id: string;
  user_id?: string;
  user_email?: string;
  user_name?: string;
  action: string;
  target_type?: string;
  target_id?: string;
  details: Record<string, unknown>;
  ip_address?: string;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
  active_organization_id?: string;
}

// Phase 2: Dependency Graph & Evidence Registry Types
export type NodeType = "service" | "endpoint" | "database_table" | "customer_workflow" | "external_api";
export type EdgeType = "calls_api" | "reads_table" | "writes_table" | "depends_on" | "subscribes_event" | "serves_customer";
export type EvidenceConfidence = "confirmed" | "inferred" | "unknown";
export type EvidenceSourceKind = "openapi_spec" | "code_ast" | "sql_migration" | "customer_contract" | "manual_declaration";

export interface EvidenceRecord {
  id: string;
  organization_id: string;
  project_id: string;
  edge_id?: string;
  source_kind: EvidenceSourceKind;
  confidence: EvidenceConfidence;
  summary: string;
  raw_snippet?: string;
  provenance_details: Record<string, unknown>;
  created_at: string;
}

export interface GraphNode {
  id: string;
  organization_id: string;
  project_id: string;
  node_type: NodeType;
  identifier: string;
  name: string;
  description?: string;
  metadata_info: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface GraphEdge {
  id: string;
  organization_id: string;
  project_id: string;
  source_node_id: string;
  target_node_id: string;
  edge_type: EdgeType;
  confidence: EvidenceConfidence;
  weight: number;
  metadata_info: Record<string, unknown>;
  created_at: string;
  evidence_records: EvidenceRecord[];
}

export interface GraphMetrics {
  total_nodes: number;
  total_edges: number;
  services_count: number;
  endpoints_count: number;
  tables_count: number;
  customers_count: number;
  confirmed_edges: number;
  inferred_edges: number;
  unknown_edges: number;
  spof_candidates: string[];
}

export interface TopologyGraphResponse {
  nodes: GraphNode[];
  edges: GraphEdge[];
  metrics: GraphMetrics;
}

export interface DownstreamImpactResult {
  root_node_id: string;
  root_node_name: string;
  total_impacted_nodes: number;
  impacted_services: string[];
  impacted_endpoints: string[];
  impacted_customers: string[];
  has_unknown_dependencies: boolean;
  safety_verdict: "CONFIRMED_IMPACT_SET" | "CAUTION_REQUIRED";
}

export interface CustomerMapping {
  id: string;
  organization_id: string;
  project_id: string;
  customer_name: string;
  tier: string;
  contract_sla: string;
  workflows: string[];
  consumed_endpoints: string[];
  metadata_info: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

// Phase 3: Change Analyzer & Impact Simulator Types
export type ChangeSeverity = "NON_BREAKING" | "POTENTIALLY_BREAKING" | "BREAKING";

export type BreakingCategory =
  | "REMOVED_ENDPOINT"
  | "REMOVED_METHOD"
  | "CHANGED_REQUEST_SCHEMA"
  | "CHANGED_RESPONSE_SCHEMA"
  | "REMOVED_REQUIRED_FIELD"
  | "ADDED_REQUIRED_FIELD"
  | "CHANGED_TYPE"
  | "CHANGED_STATUS_CODE"
  | "SQL_COLUMN_DROPPED"
  | "SQL_TABLE_DROPPED"
  | "SQL_TYPE_ALTERED"
  | "SQL_NOT_NULL_ADDED"
  | "UNKNOWN";

export type RiskLevel = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

export type DeploymentVerdict = "SAFE" | "SAFE_WITH_MITIGATION" | "BLOCKED";

export interface ChangeFinding {
  severity: ChangeSeverity;
  category: BreakingCategory;
  target: string;
  description: string;
  evidence: string;
  safe_migration_advice?: string;
  provenance: string;
}

export interface ChangeAnalysisResponse {
  id: string;
  organization_id: string;
  project_id: string;
  title: string;
  analysis_type: string;
  base_version: string;
  target_version: string;
  breaking_count: number;
  non_breaking_count: number;
  findings: ChangeFinding[];
  metadata_info: Record<string, unknown>;
  created_at: string;
}

export interface AffectedCustomer {
  customer_name: string;
  tier: string;
  contract_sla: string;
  impacted_endpoints: string[];
  impacted_workflows: string[];
}

export interface SimulationReportResponse {
  id: string;
  organization_id: string;
  project_id: string;
  analysis_id?: string;
  target_component_id: string;
  target_component_name: string;
  risk_level: RiskLevel;
  verdict: DeploymentVerdict;
  canonical_verdict?: string;
  summary: string;
  directly_affected_services: string[];
  transitive_affected_services: string[];
  affected_customers: AffectedCustomer[];
  spof_identified: string[];
  has_unknown_dependencies: boolean;
  verification_checklist: string[];
  markdown_report: string;
  report_details: Record<string, unknown>;
  created_at: string;
}

