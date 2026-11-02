from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, Request, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.organization import Organization
from app.models.user import User
from app.models.analysis import SimulationReport
from app.schemas.analysis import (
    SimulationRequest,
    SimulationReportResponse,
)
from app.services.impact_simulator import ImpactSimulatorService
from app.services.project_service import ProjectService
from app.services.audit_service import AuditService
from app.api.deps import get_current_organization, get_current_user, get_client_ip

router = APIRouter(prefix="/projects/{project_id}/simulator", tags=["Impact Simulator"])


@router.post("/simulate", response_model=SimulationReportResponse)
def run_simulation(
    project_id: str,
    payload: SimulationRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_org: Organization = Depends(get_current_organization),
    current_user: User = Depends(get_current_user),
):
    project = ProjectService.get_project(db, current_org.id, project_id)

    report = ImpactSimulatorService.simulate_change_impact(
        db=db,
        organization_id=current_org.id,
        project_id=project.id,
        author_id=current_user.id,
        target_component=payload.target_component,
        change_summary=payload.change_summary,
        analysis_id=payload.analysis_id,
        manual_breaking_findings=payload.manual_breaking_findings,
    )

    AuditService.log(
        db=db,
        organization_id=current_org.id,
        user_id=current_user.id,
        action="IMPACT_SIMULATION_EXECUTED",
        target_type="simulation_report",
        target_id=report.id,
        details={
            "target_component": payload.target_component,
            "verdict": report.verdict.value,
            "risk_level": report.risk_level.value,
            "project_id": project.id,
        },
        ip_address=get_client_ip(request),
    )

    return report


@router.get("/reports", response_model=List[SimulationReportResponse])
def list_reports(
    project_id: str,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_org: Organization = Depends(get_current_organization),
    current_user: User = Depends(get_current_user),
):
    project = ProjectService.get_project(db, current_org.id, project_id)
    reports = (
        db.query(SimulationReport)
        .filter(
            SimulationReport.organization_id == current_org.id,
            SimulationReport.project_id == project.id,
        )
        .order_by(SimulationReport.created_at.desc())
        .limit(limit)
        .all()
    )
    return reports


@router.get("/reports/{report_id}", response_model=SimulationReportResponse)
def get_report(
    project_id: str,
    report_id: str,
    db: Session = Depends(get_db),
    current_org: Organization = Depends(get_current_organization),
    current_user: User = Depends(get_current_user),
):
    project = ProjectService.get_project(db, current_org.id, project_id)
    report = (
        db.query(SimulationReport)
        .filter(
            SimulationReport.id == report_id,
            SimulationReport.organization_id == current_org.id,
            SimulationReport.project_id == project.id,
        )
        .first()
    )
    if not report:
        raise HTTPException(status_code=404, detail="Simulation report not found")
    return report


@router.get("/reports/{report_id}/export-markdown")
def export_markdown(
    project_id: str,
    report_id: str,
    db: Session = Depends(get_db),
    current_org: Organization = Depends(get_current_organization),
    current_user: User = Depends(get_current_user),
):
    project = ProjectService.get_project(db, current_org.id, project_id)
    report = (
        db.query(SimulationReport)
        .filter(
            SimulationReport.id == report_id,
            SimulationReport.organization_id == current_org.id,
            SimulationReport.project_id == project.id,
        )
        .first()
    )
    if not report:
        raise HTTPException(status_code=404, detail="Simulation report not found")
    
    return Response(
        content=report.markdown_report,
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="affactoryx_report_{report.id}.md"'},
    )
