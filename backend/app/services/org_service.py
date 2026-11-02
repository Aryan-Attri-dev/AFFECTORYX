import re
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.organization import Organization
from app.models.membership import Membership, OrgRole
from app.models.user import User
from app.models.project import Project
from app.schemas.organization import (
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationRead,
    MemberRead,
)
from app.services.audit_service import AuditService


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    text = re.sub(r"^-+|-+$", "", text)
    return text or "org"


class OrgService:
    @staticmethod
    def get_by_id(db: Session, org_id: str) -> Optional[Organization]:
        return db.query(Organization).filter(Organization.id == org_id).first()

    @staticmethod
    def get_by_slug(db: Session, slug: str) -> Optional[Organization]:
        return db.query(Organization).filter(Organization.slug == slug).first()

    @staticmethod
    def create_organization(
        db: Session,
        creator: User,
        data: OrganizationCreate,
        ip_address: Optional[str] = None,
    ) -> Organization:
        base_slug = slugify(data.slug or data.name)
        slug = base_slug
        counter = 1
        while db.query(Organization).filter(Organization.slug == slug).first():
            slug = f"{base_slug}-{counter}"
            counter += 1

        org = Organization(
            name=data.name,
            slug=slug,
            description=data.description,
        )
        db.add(org)
        db.flush()

        # Add creator as OWNER
        membership = Membership(
            user_id=creator.id,
            organization_id=org.id,
            role=OrgRole.OWNER,
        )
        db.add(membership)
        db.flush()

        AuditService.log(
            db=db,
            organization_id=org.id,
            user_id=creator.id,
            action="organization.create",
            target_type="organization",
            target_id=org.id,
            details={"name": org.name, "slug": org.slug},
            ip_address=ip_address,
        )
        db.commit()
        db.refresh(org)
        return org

    @staticmethod
    def get_user_organizations(db: Session, user: User) -> List[OrganizationRead]:
        memberships = (
            db.query(Membership)
            .filter(Membership.user_id == user.id)
            .all()
        )
        results = []
        for m in memberships:
            org = m.organization
            member_count = db.query(Membership).filter(Membership.organization_id == org.id).count()
            project_count = db.query(Project).filter(Project.organization_id == org.id).count()
            results.append(
                OrganizationRead(
                    id=org.id,
                    name=org.name,
                    slug=org.slug,
                    description=org.description,
                    created_at=org.created_at,
                    updated_at=org.updated_at,
                    user_role=m.role.value if hasattr(m.role, "value") else str(m.role),
                    member_count=member_count,
                    project_count=project_count,
                )
            )
        return results

    @staticmethod
    def get_organization_detail(db: Session, org_id: str, current_user: User) -> OrganizationRead:
        org = OrgService.get_by_id(db, org_id)
        if not org:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

        membership = (
            db.query(Membership)
            .filter(Membership.organization_id == org_id, Membership.user_id == current_user.id)
            .first()
        )
        if not membership and not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You are not a member of this organization",
            )

        member_count = db.query(Membership).filter(Membership.organization_id == org.id).count()
        project_count = db.query(Project).filter(Project.organization_id == org.id).count()

        role_str = (
            membership.role.value if membership and hasattr(membership.role, "value")
            else str(membership.role) if membership
            else "superuser"
        )

        return OrganizationRead(
            id=org.id,
            name=org.name,
            slug=org.slug,
            description=org.description,
            created_at=org.created_at,
            updated_at=org.updated_at,
            user_role=role_str,
            member_count=member_count,
            project_count=project_count,
        )

    @staticmethod
    def update_organization(
        db: Session,
        org_id: str,
        data: OrganizationUpdate,
        actor: User,
        ip_address: Optional[str] = None,
    ) -> Organization:
        org = OrgService.get_by_id(db, org_id)
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")

        if data.name is not None:
            org.name = data.name
        if data.description is not None:
            org.description = data.description

        AuditService.log(
            db=db,
            organization_id=org.id,
            user_id=actor.id,
            action="organization.update",
            target_type="organization",
            target_id=org.id,
            details={"updated_fields": [k for k, v in data.model_dump(exclude_unset=True).items()]},
            ip_address=ip_address,
        )
        db.commit()
        db.refresh(org)
        return org

    @staticmethod
    def list_members(db: Session, org_id: str) -> List[MemberRead]:
        memberships = (
            db.query(Membership)
            .filter(Membership.organization_id == org_id)
            .join(User)
            .order_by(Membership.created_at.asc())
            .all()
        )
        return [
            MemberRead(
                membership_id=m.id,
                user_id=m.user.id,
                email=m.user.email,
                full_name=m.user.full_name,
                role=m.role.value if hasattr(m.role, "value") else str(m.role),
                joined_at=m.created_at,
            )
            for m in memberships
        ]

    @staticmethod
    def add_member(
        db: Session,
        org_id: str,
        email: str,
        role: OrgRole,
        actor: User,
        ip_address: Optional[str] = None,
    ) -> MemberRead:
        user = db.query(User).filter(User.email == email.strip().lower()).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with email '{email}' does not exist in AFFECTORYX",
            )

        existing = (
            db.query(Membership)
            .filter(Membership.organization_id == org_id, Membership.user_id == user.id)
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already a member of this organization",
            )

        membership = Membership(
            user_id=user.id,
            organization_id=org_id,
            role=role,
        )
        db.add(membership)
        db.flush()

        AuditService.log(
            db=db,
            organization_id=org_id,
            user_id=actor.id,
            action="member.add",
            target_type="user",
            target_id=user.id,
            details={"email": user.email, "role": role.value},
            ip_address=ip_address,
        )
        db.commit()
        db.refresh(membership)

        return MemberRead(
            membership_id=membership.id,
            user_id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=membership.role.value if hasattr(membership.role, "value") else str(membership.role),
            joined_at=membership.created_at,
        )

    @staticmethod
    def update_member_role(
        db: Session,
        org_id: str,
        target_user_id: str,
        new_role: OrgRole,
        actor: User,
        ip_address: Optional[str] = None,
    ) -> MemberRead:
        membership = (
            db.query(Membership)
            .filter(Membership.organization_id == org_id, Membership.user_id == target_user_id)
            .first()
        )
        if not membership:
            raise HTTPException(status_code=404, detail="Member not found in organization")

        # If changing an owner, make sure there is at least one other owner
        if membership.role == OrgRole.OWNER and new_role != OrgRole.OWNER:
            owner_count = (
                db.query(Membership)
                .filter(Membership.organization_id == org_id, Membership.role == OrgRole.OWNER)
                .count()
            )
            if owner_count <= 1:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot downgrade the sole owner of the organization",
                )

        old_role = membership.role
        membership.role = new_role
        
        AuditService.log(
            db=db,
            organization_id=org_id,
            user_id=actor.id,
            action="member.role_update",
            target_type="user",
            target_id=target_user_id,
            details={"old_role": str(old_role), "new_role": new_role.value},
            ip_address=ip_address,
        )
        db.commit()
        db.refresh(membership)

        return MemberRead(
            membership_id=membership.id,
            user_id=membership.user.id,
            email=membership.user.email,
            full_name=membership.user.full_name,
            role=membership.role.value if hasattr(membership.role, "value") else str(membership.role),
            joined_at=membership.created_at,
        )

    @staticmethod
    def remove_member(
        db: Session,
        org_id: str,
        target_user_id: str,
        actor: User,
        ip_address: Optional[str] = None,
    ) -> None:
        membership = (
            db.query(Membership)
            .filter(Membership.organization_id == org_id, Membership.user_id == target_user_id)
            .first()
        )
        if not membership:
            raise HTTPException(status_code=404, detail="Member not found in organization")

        if membership.role == OrgRole.OWNER:
            owner_count = (
                db.query(Membership)
                .filter(Membership.organization_id == org_id, Membership.role == OrgRole.OWNER)
                .count()
            )
            if owner_count <= 1:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot remove the sole owner of the organization",
                )

        db.delete(membership)
        AuditService.log(
            db=db,
            organization_id=org_id,
            user_id=actor.id,
            action="member.remove",
            target_type="user",
            target_id=target_user_id,
            details={"removed_user_id": target_user_id},
            ip_address=ip_address,
        )
        db.commit()
