from typing import List, Optional
from fastapi import APIRouter, Depends, Query, UploadFile, File, Form, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.models.organization import Organization
from app.models.project import Project
from app.models.graph import EvidenceRecord, EvidenceConfidence, EvidenceSourceKind
from app.models.membership import OrgRole
from app.schemas.graph import (
    TopologyGraphResponse,
    OpenAPIIngestionSummary,
    CodeASTIngestionSummary,
    SQLMigrationIngestionSummary,
    CustomerMappingRead,
    CustomerMappingCreate,
    EvidenceRecordRead,
)
from app.services.graph_engine import GraphEngine
from app.services.project_service import ProjectService
from app.services.ingestion.openapi_parser import OpenAPIParser
from app.services.ingestion.code_ast_parser import CodeASTScanner
from app.services.ingestion.migration_parser import SQLMigrationAnalyzer
from app.services.ingestion.customer_mapper import CustomerService
from app.api.deps import get_current_organization, require_role, get_client_ip, get_current_user

router = APIRouter(prefix="/projects/{project_id}", tags=["Dependency Graph & Evidence"])


class RawCodeIngestRequest(BaseModel):
    caller_service_name: str
    file_path: str
    code_content: str


class RawSQLIngestRequest(BaseModel):
    migration_filename: str
    sql_content: str


class RawOpenAPIIngestRequest(BaseModel):
    spec_source_name: str = "openapi_spec.json"
    spec_content: str


@router.get("/graph", response_model=TopologyGraphResponse)
def get_dependency_graph(
    project_id: str,
    db: Session = Depends(get_db),
    current_org: Organization = Depends(get_current_organization),
    _role=Depends(require_role(OrgRole.VIEWER)),
):
    """Retrieve full evidence-based dependency graph and topology metrics for a project."""
    ProjectService.get_project(db, current_org.id, project_id)
    return GraphEngine.get_topology(db, current_org.id, project_id)


@router.get("/graph/impact")
def get_node_downstream_impact(
    project_id: str,
    start_node_id: str = Query(..., description="ID of the component or endpoint to analyze"),
    db: Session = Depends(get_db),
    current_org: Organization = Depends(get_current_organization),
    _role=Depends(require_role(OrgRole.VIEWER)),
):
    """Calculate the downstream transitive blast radius and customer impacts from a component change."""
    ProjectService.get_project(db, current_org.id, project_id)
    return GraphEngine.compute_downstream_impact(db, project_id, start_node_id)


@router.post("/ingest/openapi", response_model=OpenAPIIngestionSummary)
def ingest_openapi_spec(
    project_id: str,
    data: RawOpenAPIIngestRequest,
    db: Session = Depends(get_db),
    current_org: Organization = Depends(get_current_organization),
    _role=Depends(require_role(OrgRole.MEMBER)),
):
    """Parse an OpenAPI v3 specification and register verified services, endpoints, and schemas."""
    ProjectService.get_project(db, current_org.id, project_id)
    return OpenAPIParser.ingest_spec(
        db=db,
        organization_id=current_org.id,
        project_id=project_id,
        spec_content=data.spec_content,
        spec_source_name=data.spec_source_name,
    )


@router.post("/ingest/code", response_model=CodeASTIngestionSummary)
def ingest_code_ast(
    project_id: str,
    data: RawCodeIngestRequest,
    db: Session = Depends(get_db),
    current_org: Organization = Depends(get_current_organization),
    _role=Depends(require_role(OrgRole.MEMBER)),
):
    """Statically parse source code AST to discover service-to-service callsites without executing code."""
    ProjectService.get_project(db, current_org.id, project_id)
    return CodeASTScanner.scan_python_code(
        db=db,
        organization_id=current_org.id,
        project_id=project_id,
        caller_service_name=data.caller_service_name,
        file_path=data.file_path,
        code_content=data.code_content,
    )


@router.post("/ingest/migration", response_model=SQLMigrationIngestionSummary)
def ingest_sql_migration(
    project_id: str,
    data: RawSQLIngestRequest,
    db: Session = Depends(get_db),
    current_org: Organization = Depends(get_current_organization),
    _role=Depends(require_role(OrgRole.MEMBER)),
):
    """Analyze database migration DDL for schema changes, table creation, and destructive column/table drops."""
    ProjectService.get_project(db, current_org.id, project_id)
    return SQLMigrationAnalyzer.analyze_sql_migration(
        db=db,
        organization_id=current_org.id,
        project_id=project_id,
        migration_filename=data.migration_filename,
        sql_content=data.sql_content,
    )


@router.get("/customers", response_model=List[CustomerMappingRead])
def list_customer_mappings(
    project_id: str,
    db: Session = Depends(get_db),
    current_org: Organization = Depends(get_current_organization),
    _role=Depends(require_role(OrgRole.VIEWER)),
):
    """List explicitly mapped customers and their contracted workflows."""
    ProjectService.get_project(db, current_org.id, project_id)
    return CustomerService.list_customers(db, current_org.id, project_id)


@router.post("/customers", response_model=CustomerMappingRead, status_code=201)
def add_customer_mapping(
    project_id: str,
    data: CustomerMappingCreate,
    db: Session = Depends(get_db),
    current_org: Organization = Depends(get_current_organization),
    _role=Depends(require_role(OrgRole.MEMBER)),
):
    """Register an explicit customer contract with critical workflows and consumed endpoints."""
    ProjectService.get_project(db, current_org.id, project_id)
    return CustomerService.add_customer_mapping(db, current_org.id, project_id, data)


@router.get("/evidence", response_model=List[EvidenceRecordRead])
def list_evidence_registry(
    project_id: str,
    confidence: Optional[EvidenceConfidence] = None,
    source_kind: Optional[EvidenceSourceKind] = None,
    db: Session = Depends(get_db),
    current_org: Organization = Depends(get_current_organization),
    _role=Depends(require_role(OrgRole.VIEWER)),
):
    """Inspect the immutable Evidence Registry for provenance records backing dependency relationships."""
    ProjectService.get_project(db, current_org.id, project_id)
    query = (
        db.query(EvidenceRecord)
        .filter(
            EvidenceRecord.organization_id == current_org.id,
            EvidenceRecord.project_id == project_id,
        )
    )
    if confidence:
        query = query.filter(EvidenceRecord.confidence == confidence)
    if source_kind:
        query = query.filter(EvidenceRecord.source_kind == source_kind)

    records = query.order_by(EvidenceRecord.created_at.desc()).limit(100).all()
    return [EvidenceRecordRead.model_validate(r) for r in records]
