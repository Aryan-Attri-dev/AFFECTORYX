from sqlalchemy import Column, String, Text, ForeignKey, UniqueConstraint, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin, generate_uuid


class Project(Base, TimestampMixin):
    __tablename__ = "projects"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    repository_url = Column(String(512), nullable=True)
    default_branch = Column(String(100), default="main", nullable=False)
    environments = Column(JSON, default=lambda: ["production", "staging"], nullable=False)
    metadata_info = Column(JSON, default=dict, nullable=False)

    organization = relationship("Organization", back_populates="projects")

    __table_args__ = (
        UniqueConstraint("organization_id", "slug", name="uq_org_project_slug"),
    )
