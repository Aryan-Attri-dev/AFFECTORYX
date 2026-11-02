from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.models.organization import Organization
from app.models.user import User
from app.models.analysis import ChangeAnalysis
from app.schemas.analysis import (
    OpenAPIComparisonRequest,
    SQLComparisonRequest,
    ChangeAnalysisResponse,
)
from app.services.change_analyzer import ChangeAnalyzerService
from app.services.project_service import ProjectService
from app.services.audit_service import AuditService
from app.api.deps import get_current_organization, get_current_user, get_client_ip

router = APIRouter(prefix="/projects/{project_id}/analyzer", tags=["Change Analyzer"])


@router.post("/compare-openapi", response_model=ChangeAnalysisResponse)
def compare_openapi(
    project_id: str,
    payload: OpenAPIComparisonRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_org: Organization = Depends(get_current_organization),
    current_user: User = Depends(get_current_user),
):
    project = ProjectService.get_project(db, current_org.id, project_id)

    analysis = ChangeAnalyzerService.compare_openapi_specs(
        db=db,
        organization_id=current_org.id,
        project_id=project.id,
        author_id=current_user.id,
        title=payload.title,
        base_spec_str=payload.base_spec,
        target_spec_str=payload.target_spec,
        base_version=payload.base_version,
        target_version=payload.target_version,
    )

    AuditService.log(
        db=db,
        organization_id=current_org.id,
        user_id=current_user.id,
        action="OPENAPI_CHANGE_ANALYZED",
        target_type="change_analysis",
        target_id=analysis.id,
        details={
            "breaking_count": analysis.breaking_count,
            "non_breaking_count": analysis.non_breaking_count,
            "project_id": project.id,
        },
        ip_address=get_client_ip(request),
    )

    return analysis


@router.post("/compare-sql", response_model=ChangeAnalysisResponse)
def compare_sql(
    project_id: str,
    payload: SQLComparisonRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_org: Organization = Depends(get_current_organization),
    current_user: User = Depends(get_current_user),
):
    project = ProjectService.get_project(db, current_org.id, project_id)

    analysis = ChangeAnalyzerService.compare_sql_migration(
        db=db,
        organization_id=current_org.id,
        project_id=project.id,
        author_id=current_user.id,
        title=payload.title,
        migration_filename=payload.migration_filename,
        sql_content=payload.sql_content,
        base_version=payload.base_version,
        target_version=payload.target_version,
    )

    AuditService.log(
        db=db,
        organization_id=current_org.id,
        user_id=current_user.id,
        action="SQL_MIGRATION_ANALYZED",
        target_type="change_analysis",
        target_id=analysis.id,
        details={
            "breaking_count": analysis.breaking_count,
            "non_breaking_count": analysis.non_breaking_count,
            "project_id": project.id,
        },
        ip_address=get_client_ip(request),
    )

    return analysis


@router.get("/analyses", response_model=List[ChangeAnalysisResponse])
def list_analyses(
    project_id: str,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_org: Organization = Depends(get_current_organization),
    current_user: User = Depends(get_current_user),
):
    project = ProjectService.get_project(db, current_org.id, project_id)
    analyses = (
        db.query(ChangeAnalysis)
        .filter(
            ChangeAnalysis.organization_id == current_org.id,
            ChangeAnalysis.project_id == project.id,
        )
        .order_by(ChangeAnalysis.created_at.desc())
        .limit(limit)
        .all()
    )
    return analyses


@router.get("/analyses/{analysis_id}", response_model=ChangeAnalysisResponse)
def get_analysis(
    project_id: str,
    analysis_id: str,
    db: Session = Depends(get_db),
    current_org: Organization = Depends(get_current_organization),
    current_user: User = Depends(get_current_user),
):
    project = ProjectService.get_project(db, current_org.id, project_id)
    analysis = (
        db.query(ChangeAnalysis)
        .filter(
            ChangeAnalysis.id == analysis_id,
            ChangeAnalysis.organization_id == current_org.id,
            ChangeAnalysis.project_id == project.id,
        )
        .first()
    )
    if not analysis:
        raise HTTPException(status_code=404, detail="Change analysis not found")
    return analysis
