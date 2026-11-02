from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User
from app.models.membership import Membership
from app.schemas.auth import RegisterRequest, LoginRequest, Token
from app.schemas.user import UserRead, UserOrgMembership
from app.schemas.organization import OrganizationCreate
from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.config import settings
from app.services.org_service import OrgService
from app.services.audit_service import AuditService


class AuthService:
    @staticmethod
    def get_user_read(db: Session, user: User) -> UserRead:
        memberships = (
            db.query(Membership)
            .filter(Membership.user_id == user.id)
            .all()
        )
        membership_schemas = [
            UserOrgMembership(
                organization_id=m.organization.id,
                organization_name=m.organization.name,
                organization_slug=m.organization.slug,
                role=m.role.value if hasattr(m.role, "value") else str(m.role),
            )
            for m in memberships
        ]
        return UserRead(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            created_at=user.created_at,
            memberships=membership_schemas,
        )

    @staticmethod
    def register(
        db: Session,
        data: RegisterRequest,
        ip_address: Optional[str] = None,
    ) -> Token:
        email = data.email.strip().lower()
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An account with this email already exists",
            )

        user = User(
            email=email,
            full_name=data.full_name.strip(),
            hashed_password=get_password_hash(data.password),
            is_active=True,
            is_superuser=False,
        )
        db.add(user)
        db.flush()

        # Create primary organization
        org_name = data.organization_name.strip() if data.organization_name else f"{user.full_name}'s Org"
        org = OrgService.create_organization(
            db=db,
            creator=user,
            data=OrganizationCreate(name=org_name),
            ip_address=ip_address,
        )

        AuditService.log(
            db=db,
            organization_id=org.id,
            user_id=user.id,
            action="auth.register",
            target_type="user",
            target_id=user.id,
            details={"email": user.email},
            ip_address=ip_address,
        )
        db.commit()
        db.refresh(user)

        user_read = AuthService.get_user_read(db, user)
        token = create_access_token(
            subject=user.id,
            extra_claims={"org_id": org.id},
        )

        return Token(
            access_token=token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=user_read,
            active_organization_id=org.id,
        )

    @staticmethod
    def login(
        db: Session,
        data: LoginRequest,
        ip_address: Optional[str] = None,
    ) -> Token:
        email = data.email.strip().lower()
        user = db.query(User).filter(User.email == email).first()
        if not user or not verify_password(data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is deactivated",
            )

        memberships = db.query(Membership).filter(Membership.user_id == user.id).all()
        active_org_id = None
        if data.organization_id:
            valid_org = any(m.organization_id == data.organization_id for m in memberships)
            if not valid_org and not user.is_superuser:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User does not have access to the specified organization",
                )
            active_org_id = data.organization_id
        elif memberships:
            active_org_id = memberships[0].organization_id

        if active_org_id:
            AuditService.log(
                db=db,
                organization_id=active_org_id,
                user_id=user.id,
                action="auth.login",
                target_type="user",
                target_id=user.id,
                details={"email": user.email},
                ip_address=ip_address,
            )
            db.commit()

        user_read = AuthService.get_user_read(db, user)
        token = create_access_token(
            subject=user.id,
            extra_claims={"org_id": active_org_id} if active_org_id else {},
        )

        return Token(
            access_token=token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=user_read,
            active_organization_id=active_org_id,
        )
