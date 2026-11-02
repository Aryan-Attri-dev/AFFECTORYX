from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field
from app.models.membership import OrgRole


class OrganizationBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None


class OrganizationCreate(OrganizationBase):
    slug: Optional[str] = None


class OrganizationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = None


class OrganizationRead(OrganizationBase):
    id: str
    slug: str
    created_at: datetime
    updated_at: datetime
    user_role: Optional[str] = None
    member_count: Optional[int] = 0
    project_count: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)


class MemberRead(BaseModel):
    membership_id: str
    user_id: str
    email: str
    full_name: str
    role: str
    joined_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MemberAddRequest(BaseModel):
    email: str
    role: OrgRole = OrgRole.MEMBER


class MemberRoleUpdate(BaseModel):
    role: OrgRole
