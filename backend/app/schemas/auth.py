from typing import Optional, List
from pydantic import BaseModel, EmailStr


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: "UserRead"
    active_organization_id: Optional[str] = None


class TokenPayload(BaseModel):
    sub: Optional[str] = None
    exp: Optional[int] = None
    org_id: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    organization_id: Optional[str] = None


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    organization_name: Optional[str] = None


from app.schemas.user import UserRead  # noqa: E402
Token.model_rebuild()
