from typing import List
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.models.organization import Organization
from app.models.membership import OrgRole
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectRead
from app.services.project_service import ProjectService
from app.api.deps import (
    get_current_user,
    get_current_organization,
    require_role,
    get_client_ip,
)

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get("", response_model=List[ProjectRead])
def list_projects(
    db: Session = Depends(get_db),
    current_org: Organization = Depends(get_current_organization),
    _role=Depends(require_role(OrgRole.VIEWER)),
):
    """List all projects belonging to the active organization."""
    return ProjectService.list_projects(db=db, organization_id=current_org.id)


@router.post("", response_model=ProjectRead, status_code=201)
def create_project(
    data: ProjectCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    _role=Depends(require_role(OrgRole.MEMBER)),
):
    """Create a new project workspace in the active organization. Requires MEMBER role or higher."""
    project = ProjectService.create_project(
        db=db,
        organization_id=current_org.id,
        data=data,
        actor=current_user,
        ip_address=get_client_ip(request),
    )
    return ProjectRead.model_validate(project)


@router.get("/{project_id_or_slug}", response_model=ProjectRead)
def get_project(
    project_id_or_slug: str,
    db: Session = Depends(get_db),
    current_org: Organization = Depends(get_current_organization),
    _role=Depends(require_role(OrgRole.VIEWER)),
):
    """Get project details scoped strictly to the current organization."""
    project = ProjectService.get_project(
        db=db,
        organization_id=current_org.id,
        project_id_or_slug=project_id_or_slug,
    )
    return ProjectRead.model_validate(project)


@router.patch("/{project_id_or_slug}", response_model=ProjectRead)
def update_project(
    project_id_or_slug: str,
    data: ProjectUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    _role=Depends(require_role(OrgRole.MEMBER)),
):
    """Update project configuration and repository linkage. Requires MEMBER role or higher."""
    project = ProjectService.update_project(
        db=db,
        organization_id=current_org.id,
        project_id=project_id_or_slug,
        data=data,
        actor=current_user,
        ip_address=get_client_ip(request),
    )
    return ProjectRead.model_validate(project)


@router.delete("/{project_id_or_slug}", status_code=204)
def delete_project(
    project_id_or_slug: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_organization),
    _role=Depends(require_role(OrgRole.ADMIN)),
):
    """Delete a project workspace and all attached intelligence. Requires ADMIN role or higher."""
    ProjectService.delete_project(
        db=db,
        organization_id=current_org.id,
        project_id=project_id_or_slug,
        actor=current_user,
        ip_address=get_client_ip(request),
    )
    return None
