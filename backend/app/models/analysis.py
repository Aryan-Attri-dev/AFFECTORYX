import enum
from sqlalchemy import Column, String, Text, ForeignKey, Enum, JSON, Integer, Index
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin, generate_uuid


class ChangeSeverity(str, enum.Enum):
    BREAKING = "breaking"
    NON_BREAKING = "non_breaking"
    INFO = "info"


class BreakingCategory(str, enum.Enum):
    REMOVED_ENDPOINT = "removed_endpoint"
    CHANGED_METHOD = "changed_method"
    REQUIRED_PARAMETER_ADDED = "required_parameter_added"
    INCOMPATIBLE_TYPE = "incompatible_type"
    REMOVED_RESPONSE_FIELD = "removed_response_field"
    DROPPED_TABLE = "dropped_table"
    DROPPED_COLUMN = "dropped_column"
    INCOMPATIBLE_COLUMN_MODIFICATION = "incompatible_column_modification"
    SCHEMA_RESTRICTION = "schema_restriction"
    UNKNOWN_DEPENDENCY = "unknown_dependency"


class RiskLevel(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class DeploymentVerdict(str, enum.Enum):
    # Phase 3 Canonical Verdicts
    SAFE = "SAFE"
    SAFE_WITH_MITIGATION = "SAFE_WITH_MITIGATION"
    BLOCKED = "BLOCKED"

    # Backward Compatibility Aliases (Phase 2)
    SAFE_TO_DEPLOY = "safe_to_deploy"
    BREAKING_CHANGES_DETECTED = "breaking_changes_detected"
    CAUTION_REQUIRED = "caution_required"


class ChangeAnalysis(Base, TimestampMixin):
    __tablename__ = "change_analyses"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    author_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    analysis_type = Column(String(50), nullable=False)  # "openapi", "sql_migration", "source_diff"
    base_version = Column(String(100), default="v1.0.0", nullable=False)
    target_version = Column(String(100), default="v2.0.0", nullable=False)
    breaking_count = Column(Integer, default=0, nullable=False)
    non_breaking_count = Column(Integer, default=0, nullable=False)
    findings = Column(JSON, default=list, nullable=False)  # Detailed list of comparison findings
    metadata_info = Column(JSON, default=dict, nullable=False)

    reports = relationship("SimulationReport", back_populates="analysis", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_analysis_org_project", "organization_id", "project_id"),
    )


class SimulationReport(Base, TimestampMixin):
    __tablename__ = "simulation_reports"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    analysis_id = Column(String(36), ForeignKey("change_analyses.id", ondelete="SET NULL"), nullable=True, index=True)
    author_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    target_component_id = Column(String(255), nullable=False, index=True)
    target_component_name = Column(String(255), nullable=False)
    risk_level = Column(Enum(RiskLevel), nullable=False, index=True)
    verdict = Column(Enum(DeploymentVerdict), nullable=False, index=True)
    summary = Column(Text, nullable=False)
    directly_affected_services = Column(JSON, default=list, nullable=False)
    transitive_affected_services = Column(JSON, default=list, nullable=False)
    affected_customers = Column(JSON, default=list, nullable=False)
    spof_identified = Column(JSON, default=list, nullable=False)
    has_unknown_dependencies = Column(Integer, default=0, nullable=False)
    verification_checklist = Column(JSON, default=list, nullable=False)
    markdown_report = Column(Text, nullable=False)
    report_details = Column(JSON, default=dict, nullable=False)

    analysis = relationship("ChangeAnalysis", back_populates="reports")

    __table_args__ = (
        Index("ix_sim_org_project", "organization_id", "project_id"),
    )

    @property
    def canonical_verdict(self) -> str:
        val = self.verdict.value if hasattr(self.verdict, "value") else str(self.verdict)
        mapping = {
            "safe_to_deploy": "SAFE",
            "SAFE_TO_DEPLOY": "SAFE",
            "SAFE": "SAFE",
            "caution_required": "SAFE_WITH_MITIGATION",
            "CAUTION_REQUIRED": "SAFE_WITH_MITIGATION",
            "SAFE_WITH_MITIGATION": "SAFE_WITH_MITIGATION",
            "breaking_changes_detected": "BLOCKED",
            "BREAKING_CHANGES_DETECTED": "BLOCKED",
            "BLOCKED": "BLOCKED",
        }
        return mapping.get(val, "BLOCKED")
