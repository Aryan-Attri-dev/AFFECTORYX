from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from app.models.analysis import ChangeSeverity, BreakingCategory, RiskLevel, DeploymentVerdict


class ChangeFinding(BaseModel):
    severity: ChangeSeverity
    category: BreakingCategory
    target: str
    description: str
    evidence: str
    safe_migration_advice: Optional[str] = None
    provenance: str = "CONFIRMED"


class OpenAPIComparisonRequest(BaseModel):
    project_id: str
    title: str = "API Change Analysis"
    base_spec: str
    target_spec: str
    base_version: str = "v1.0.0"
    target_version: str = "v2.0.0"


class SQLComparisonRequest(BaseModel):
    project_id: str
    title: str = "SQL Migration Analysis"
    migration_filename: str = "migration.sql"
    sql_content: str
    base_version: str = "current_schema"
    target_version: str = "proposed_migration"


class ChangeAnalysisResponse(BaseModel):
    id: str
    organization_id: str
    project_id: str
    title: str
    analysis_type: str
    base_version: str
    target_version: str
    breaking_count: int
    non_breaking_count: int
    findings: List[ChangeFinding]
    metadata_info: Dict[str, Any]
    created_at: datetime


class SimulationRequest(BaseModel):
    project_id: str
    target_component: str  # Node identifier or name, e.g. "service:billing-service" or "GET /api/v1/payments"
    change_summary: str
    analysis_id: Optional[str] = None
    manual_breaking_findings: Optional[List[ChangeFinding]] = None


class AffectedCustomer(BaseModel):
    customer_name: str
    tier: str
    contract_sla: str
    impacted_endpoints: List[str]
    impacted_workflows: List[str]


class SimulationReportResponse(BaseModel):
    id: str
    organization_id: str
    project_id: str
    analysis_id: Optional[str]
    target_component_id: str
    target_component_name: str
    risk_level: RiskLevel
    verdict: DeploymentVerdict
    canonical_verdict: Optional[str] = None
    summary: str
    directly_affected_services: List[str]
    transitive_affected_services: List[str]
    affected_customers: List[AffectedCustomer]
    spof_identified: List[str]
    has_unknown_dependencies: bool
    verification_checklist: List[str]
    markdown_report: str
    report_details: Dict[str, Any]
    created_at: datetime
