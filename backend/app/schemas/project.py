from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


class ProjectBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    repository_url: Optional[str] = None
    default_branch: str = "main"
    environments: List[str] = ["production", "staging"]
    metadata_info: Dict[str, Any] = Field(default_factory=dict)


class ProjectCreate(ProjectBase):
    slug: Optional[str] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = None
    repository_url: Optional[str] = None
    default_branch: Optional[str] = None
    environments: Optional[List[str]] = None
    metadata_info: Optional[Dict[str, Any]] = None


class ProjectRead(ProjectBase):
    id: str
    organization_id: str
    slug: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
