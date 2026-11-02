from fastapi import APIRouter, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.auth import RegisterRequest, LoginRequest, Token
from app.schemas.user import UserRead
from app.models.user import User
from app.services.auth_service import AuthService
from app.api.deps import get_current_user, get_client_ip

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=Token, status_code=201)
def register(
    data: RegisterRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Register a new user and create their initial organization."""
    return AuthService.register(
        db=db,
        data=data,
        ip_address=get_client_ip(request),
    )


@router.post("/login", response_model=Token)
def login(
    data: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Authenticate a user and return access token with org context."""
    return AuthService.login(
        db=db,
        data=data,
        ip_address=get_client_ip(request),
    )


@router.post("/token", response_model=Token)
def login_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """OAuth2 compatible token login for Swagger UI and CLI tools."""
    login_req = LoginRequest(
        email=form_data.username,
        password=form_data.password,
    )
    return AuthService.login(
        db=db,
        data=login_req,
        ip_address=get_client_ip(request),
    )


@router.get("/me", response_model=UserRead)
def get_me(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the profile and organization memberships of current authenticated user."""
    return AuthService.get_user_read(db=db, user=current_user)
