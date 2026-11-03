import {
  AuthResponse,
  Organization,
  Project,
  Member,
  AuditLog,
  User,
  TopologyGraphResponse,
  DownstreamImpactResult,
  CustomerMapping,
  EvidenceRecord,
  EvidenceConfidence,
  EvidenceSourceKind,
  ChangeAnalysisResponse,
  SimulationReportResponse,
  ChangeFinding,
  OpenAPIIngestionSummary,
  CodeASTIngestionSummary,
  SQLMigrationIngestionSummary,
} from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

class ApiClient {
  private token: string | null = null;
  private organizationId: string | null = null;

  constructor() {
    if (typeof window !== "undefined") {
      this.token = localStorage.getItem("affactoryx_token");
      this.organizationId = localStorage.getItem("affactoryx_org_id");
    }
  }

  setToken(token: string | null) {
    this.token = token;
    if (typeof window !== "undefined") {
      if (token) localStorage.setItem("affactoryx_token", token);
      else localStorage.removeItem("affactoryx_token");
    }
  }

  setOrganizationId(orgId: string | null) {
    this.organizationId = orgId;
    if (typeof window !== "undefined") {
      if (orgId) localStorage.setItem("affactoryx_org_id", orgId);
      else localStorage.removeItem("affactoryx_org_id");
    }
  }

  getToken(): string | null {
    return this.token;
  }

  getOrganizationId(): string | null {
    return this.organizationId;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${API_BASE}${endpoint}`;
    const headers = new Headers(options.headers || {});

    if (!headers.has("Content-Type") && !(options.body instanceof FormData)) {
      headers.set("Content-Type", "application/json");
    }

    if (this.token) {
      headers.set("Authorization", `Bearer ${this.token}`);
    }

    if (this.organizationId) {
      headers.set("X-Organization-ID", this.organizationId);
    }

    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (response.status === 204) {
      return {} as T;
    }

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      const errorMessage = data.detail || response.statusText || "Request failed";
      throw new Error(errorMessage);
    }

    return data as T;
  }

  // Auth Endpoints
  async register(data: { email: string; full_name: string; password: string; organization_name?: string }): Promise<AuthResponse> {
    const res = await this.request<AuthResponse>("/auth/register", {
      method: "POST",
      body: JSON.stringify(data),
    });
    this.setToken(res.access_token);
    if (res.active_organization_id) {
      this.setOrganizationId(res.active_organization_id);
    }
    return res;
  }

  async login(data: { email: string; password: string; organization_id?: string }): Promise<AuthResponse> {
    const res = await this.request<AuthResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify(data),
    });
    this.setToken(res.access_token);
    if (res.active_organization_id) {
      this.setOrganizationId(res.active_organization_id);
    }
    return res;
  }

  async getCurrentUser(): Promise<User> {
    return this.request<User>("/auth/me");
  }

  // Organizations
  async listOrganizations(): Promise<Organization[]> {
    return this.request<Organization[]>("/organizations");
  }

  async createOrganization(data: { name: string; description?: string }): Promise<Organization> {
    return this.request<Organization>("/organizations", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async getOrganization(id: string): Promise<Organization> {
    return this.request<Organization>(`/organizations/${id}`);
  }

  async listMembers(orgId: string): Promise<Member[]> {
    return this.request<Member[]>(`/organizations/${orgId}/members`);
  }

  async addMember(orgId: string, email: string, role: string): Promise<Member> {
    return this.request<Member>(`/organizations/${orgId}/members`, {
      method: "POST",
      body: JSON.stringify({ email, role }),
    });
  }

  async updateMemberRole(orgId: string, userId: string, role: string): Promise<Member> {
    return this.request<Member>(`/organizations/${orgId}/members/${userId}`, {
      method: "PATCH",
      body: JSON.stringify({ role }),
    });
  }

  async removeMember(orgId: string, userId: string): Promise<void> {
    await this.request<void>(`/organizations/${orgId}/members/${userId}`, {
      method: "DELETE",
    });
  }

  async getAuditLogs(orgId: string, limit = 50): Promise<AuditLog[]> {
    return this.request<AuditLog[]>(`/organizations/${orgId}/audit-logs?limit=${limit}`);
  }

  // Projects
  async listProjects(): Promise<Project[]> {
    return this.request<Project[]>("/projects");
  }

  async createProject(data: {
    name: string;
    description?: string;
    repository_url?: string;
    default_branch?: string;
    environments?: string[];
  }): Promise<Project> {
    return this.request<Project>("/projects", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async getProject(idOrSlug: string): Promise<Project> {
    return this.request<Project>(`/projects/${idOrSlug}`);
  }

  async updateProject(idOrSlug: string, data: Partial<Project>): Promise<Project> {
    return this.request<Project>(`/projects/${idOrSlug}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  }

  async deleteProject(idOrSlug: string): Promise<void> {
    await this.request<void>(`/projects/${idOrSlug}`, {
      method: "DELETE",
    });
  }

  // Phase 2: Dependency Graph & Evidence Registry
  async getTopology(projectId: string): Promise<TopologyGraphResponse> {
    return this.request<TopologyGraphResponse>(`/projects/${projectId}/graph`);
  }

  async getDownstreamImpact(projectId: string, startNodeId: string): Promise<DownstreamImpactResult> {
    return this.request<DownstreamImpactResult>(`/projects/${projectId}/graph/impact?start_node_id=${startNodeId}`);
  }

  async ingestOpenAPI(projectId: string, specContent: string, specSourceName = "openapi.json"): Promise<OpenAPIIngestionSummary> {
    return this.request<OpenAPIIngestionSummary>(`/projects/${projectId}/ingest/openapi`, {
      method: "POST",
      body: JSON.stringify({ spec_content: specContent, spec_source_name: specSourceName }),
    });
  }

  async ingestCodeAST(projectId: string, callerServiceName: string, filePath: string, codeContent: string): Promise<CodeASTIngestionSummary> {
    return this.request<CodeASTIngestionSummary>(`/projects/${projectId}/ingest/code`, {
      method: "POST",
      body: JSON.stringify({ caller_service_name: callerServiceName, file_path: filePath, code_content: codeContent }),
    });
  }

  async ingestSQLMigration(projectId: string, migrationFilename: string, sqlContent: string): Promise<SQLMigrationIngestionSummary> {
    return this.request<SQLMigrationIngestionSummary>(`/projects/${projectId}/ingest/migration`, {
      method: "POST",
      body: JSON.stringify({ migration_filename: migrationFilename, sql_content: sqlContent }),
    });
  }

  async listCustomers(projectId: string): Promise<CustomerMapping[]> {
    return this.request<CustomerMapping[]>(`/projects/${projectId}/customers`);
  }

  async addCustomer(projectId: string, data: Partial<CustomerMapping>): Promise<CustomerMapping> {
    return this.request<CustomerMapping>(`/projects/${projectId}/customers`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async listEvidence(projectId: string, confidence?: EvidenceConfidence, sourceKind?: EvidenceSourceKind): Promise<EvidenceRecord[]> {
    let url = `/projects/${projectId}/evidence`;
    const params = new URLSearchParams();
    if (confidence) params.append("confidence", confidence);
    if (sourceKind) params.append("source_kind", sourceKind);
    const queryString = params.toString();
    if (queryString) url += `?${queryString}`;
    return this.request<EvidenceRecord[]>(url);
  }

  // Phase 3: Change Analyzer & Impact Simulator
  async compareOpenAPI(
    projectId: string,
    data: {
      title: string;
      base_spec: string;
      target_spec: string;
      base_version?: string;
      target_version?: string;
    }
  ): Promise<ChangeAnalysisResponse> {
    return this.request<ChangeAnalysisResponse>(`/projects/${projectId}/analyzer/compare-openapi`, {
      method: "POST",
      body: JSON.stringify({
        project_id: projectId,
        base_version: "v1.0.0",
        target_version: "v2.0.0",
        ...data,
      }),
    });
  }

  async compareSQL(
    projectId: string,
    data: {
      title: string;
      sql_content: string;
      migration_filename?: string;
      base_version?: string;
      target_version?: string;
    }
  ): Promise<ChangeAnalysisResponse> {
    return this.request<ChangeAnalysisResponse>(`/projects/${projectId}/analyzer/compare-sql`, {
      method: "POST",
      body: JSON.stringify({
        project_id: projectId,
        migration_filename: "migration.sql",
        base_version: "current_schema",
        target_version: "proposed_migration",
        ...data,
      }),
    });
  }

  async listAnalyses(projectId: string, limit = 20): Promise<ChangeAnalysisResponse[]> {
    return this.request<ChangeAnalysisResponse[]>(`/projects/${projectId}/analyzer/analyses?limit=${limit}`);
  }

  async getAnalysis(projectId: string, analysisId: string): Promise<ChangeAnalysisResponse> {
    return this.request<ChangeAnalysisResponse>(`/projects/${projectId}/analyzer/analyses/${analysisId}`);
  }

  async simulateImpact(
    projectId: string,
    data: {
      target_component: string;
      change_summary: string;
      analysis_id?: string;
      manual_breaking_findings?: ChangeFinding[];
    }
  ): Promise<SimulationReportResponse> {
    return this.request<SimulationReportResponse>(`/projects/${projectId}/simulator/simulate`, {
      method: "POST",
      body: JSON.stringify({
        project_id: projectId,
        ...data,
      }),
    });
  }

  async listSimulationReports(projectId: string, limit = 20): Promise<SimulationReportResponse[]> {
    return this.request<SimulationReportResponse[]>(`/projects/${projectId}/simulator/reports?limit=${limit}`);
  }

  async getSimulationReport(projectId: string, reportId: string): Promise<SimulationReportResponse> {
    return this.request<SimulationReportResponse>(`/projects/${projectId}/simulator/reports/${reportId}`);
  }

  async getSimulationMarkdownExport(projectId: string, reportId: string): Promise<string> {
    const url = `${API_BASE}/projects/${projectId}/simulator/reports/${reportId}/export-markdown`;
    const headers: Record<string, string> = {};
    if (this.token) headers["Authorization"] = `Bearer ${this.token}`;
    if (this.organizationId) headers["X-Organization-ID"] = this.organizationId;
    const res = await fetch(url, { headers });
    return res.text();
  }
}

export const api = new ApiClient();
