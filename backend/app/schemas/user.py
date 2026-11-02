from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, ConfigDict


class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    is_active: bool = True


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None


class UserOrgMembership(BaseModel):
    organization_id: str
    organization_name: str
    organization_slug: str
    role: str

    model_config = ConfigDict(from_attributes=True)


class UserRead(UserBase):
    id: str
    is_superuser: bool
    created_at: datetime
    memberships: Optional[List[UserOrgMembership]] = None

    model_config = ConfigDict(from_attributes=True)
