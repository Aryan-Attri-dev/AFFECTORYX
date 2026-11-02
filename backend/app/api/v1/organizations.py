from typing import List
from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.models.membership import OrgRole
from app.schemas.organization import (
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationRead,
    MemberRead,
    MemberAddRequest,
    MemberRoleUpdate,
)
from app.schemas.audit import AuditLogRead
from app.services.org_service import OrgService
from app.services.audit_service import AuditService
from app.api.deps import get_current_user, get_client_ip, require_role, get_current_organization

router = APIRouter(prefix="/organizations", tags=["Organizations"])


@router.get("", response_model=List[OrganizationRead])
def list_my_organizations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all organizations the current authenticated user has access to."""
    return OrgService.get_user_organizations(db=db, user=current_user)


@router.post("", response_model=OrganizationRead, status_code=201)
def create_organization(
    data: OrganizationCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new organization where the current user is designated as OWNER."""
    org = OrgService.create_organization(
        db=db,
        creator=current_user,
        data=data,
        ip_address=get_client_ip(request),
    )
    return OrgService.get_organization_detail(db=db, org_id=org.id, current_user=current_user)


@router.get("/{org_id}", response_model=OrganizationRead)
def get_organization(
    org_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get metadata for a specific organization."""
    return OrgService.get_organization_detail(db=db, org_id=org_id, current_user=current_user)


@router.patch("/{org_id}", response_model=OrganizationRead)
def update_organization(
    org_id: str,
    data: OrganizationUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _role=Depends(require_role(OrgRole.ADMIN)),
):
    """Update organization settings. Requires ADMIN or OWNER role."""
    org = OrgService.update_organization(
        db=db,
        org_id=org_id,
        data=data,
        actor=current_user,
        ip_address=get_client_ip(request),
    )
    return OrgService.get_organization_detail(db=db, org_id=org.id, current_user=current_user)


@router.get("/{org_id}/members", response_model=List[MemberRead])
def list_organization_members(
    org_id: str,
    db: Session = Depends(get_db),
    _role=Depends(require_role(OrgRole.VIEWER)),
):
    """List members in an organization."""
    return OrgService.list_members(db=db, org_id=org_id)


@router.post("/{org_id}/members", response_model=MemberRead, status_code=201)
def add_organization_member(
    org_id: str,
    data: MemberAddRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _role=Depends(require_role(OrgRole.ADMIN)),
):
    """Invite/add an existing user into the organization. Requires ADMIN or OWNER role."""
    return OrgService.add_member(
        db=db,
        org_id=org_id,
        email=data.email,
        role=data.role,
        actor=current_user,
        ip_address=get_client_ip(request),
    )


@router.patch("/{org_id}/members/{user_id}", response_model=MemberRead)
def update_member_role(
    org_id: str,
    user_id: str,
    data: MemberRoleUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _role=Depends(require_role(OrgRole.OWNER)),
):
    """Update a member's role. Requires OWNER role."""
    return OrgService.update_member_role(
        db=db,
        org_id=org_id,
        target_user_id=user_id,
        new_role=data.role,
        actor=current_user,
        ip_address=get_client_ip(request),
    )


@router.delete("/{org_id}/members/{user_id}", status_code=204)
def remove_member(
    org_id: str,
    user_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _role=Depends(require_role(OrgRole.ADMIN)),
):
    """Remove a member from the organization. Requires ADMIN or OWNER role."""
    OrgService.remove_member(
        db=db,
        org_id=org_id,
        target_user_id=user_id,
        actor=current_user,
        ip_address=get_client_ip(request),
    )
    return None


@router.get("/{org_id}/audit-logs", response_model=List[AuditLogRead])
def get_audit_logs(
    org_id: str,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _role=Depends(require_role(OrgRole.ADMIN)),
):
    """Retrieve security and action audit logs for the organization. Requires ADMIN or OWNER role."""
    return AuditService.get_organization_logs(
        db=db,
        organization_id=org_id,
        limit=limit,
        offset=offset,
    )
