import enum
from sqlalchemy import Column, String, Text, ForeignKey, Enum, JSON, Float, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin, generate_uuid


class NodeType(str, enum.Enum):
    SERVICE = "service"
    ENDPOINT = "endpoint"
    DATABASE_TABLE = "database_table"
    CUSTOMER_WORKFLOW = "customer_workflow"
    EXTERNAL_API = "external_api"


class EdgeType(str, enum.Enum):
    CALLS_API = "calls_api"
    READS_TABLE = "reads_table"
    WRITES_TABLE = "writes_table"
    DEPENDS_ON = "depends_on"
    SUBSCRIBES_EVENT = "subscribes_event"
    SERVES_CUSTOMER = "serves_customer"


class EvidenceConfidence(str, enum.Enum):
    CONFIRMED = "confirmed"    # Machine verified: OpenAPI schema match, typed contract, DB foreign key
    INFERRED = "inferred"      # Static callsite match, naming convention, route heuristic
    UNKNOWN = "unknown"        # Ambiguous callsite or untracked integration; NEVER assume safe


class EvidenceSourceKind(str, enum.Enum):
    OPENAPI_SPEC = "openapi_spec"
    CODE_AST = "code_ast"
    SQL_MIGRATION = "sql_migration"
    CUSTOMER_CONTRACT = "customer_contract"
    MANUAL_DECLARATION = "manual_declaration"


class GraphNode(Base, TimestampMixin):
    __tablename__ = "graph_nodes"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    node_type = Column(Enum(NodeType), nullable=False, index=True)
    identifier = Column(String(255), nullable=False)  # e.g., "GET /api/v1/payments", "payments_ledger", "EnterpriseCheckout"
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    metadata_info = Column(JSON, default=dict, nullable=False)

    outgoing_edges = relationship("GraphEdge", foreign_keys="GraphEdge.source_node_id", back_populates="source_node", cascade="all, delete-orphan")
    incoming_edges = relationship("GraphEdge", foreign_keys="GraphEdge.target_node_id", back_populates="target_node", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("project_id", "node_type", "identifier", name="uq_project_node_identifier"),
        Index("ix_node_org_project", "organization_id", "project_id"),
    )


class GraphEdge(Base, TimestampMixin):
    __tablename__ = "graph_edges"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    source_node_id = Column(String(36), ForeignKey("graph_nodes.id", ondelete="CASCADE"), nullable=False, index=True)
    target_node_id = Column(String(36), ForeignKey("graph_nodes.id", ondelete="CASCADE"), nullable=False, index=True)
    edge_type = Column(Enum(EdgeType), nullable=False, index=True)
    confidence = Column(Enum(EvidenceConfidence), default=EvidenceConfidence.INFERRED, nullable=False, index=True)
    weight = Column(Float, default=1.0, nullable=False)
    metadata_info = Column(JSON, default=dict, nullable=False)

    source_node = relationship("GraphNode", foreign_keys=[source_node_id], back_populates="outgoing_edges")
    target_node = relationship("GraphNode", foreign_keys=[target_node_id], back_populates="incoming_edges")
    evidence_records = relationship("EvidenceRecord", back_populates="edge", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("source_node_id", "target_node_id", "edge_type", name="uq_edge_source_target_type"),
        Index("ix_edge_org_project", "organization_id", "project_id"),
    )


class EvidenceRecord(Base, TimestampMixin):
    __tablename__ = "evidence_records"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    edge_id = Column(String(36), ForeignKey("graph_edges.id", ondelete="CASCADE"), nullable=True, index=True)
    source_kind = Column(Enum(EvidenceSourceKind), nullable=False, index=True)
    confidence = Column(Enum(EvidenceConfidence), nullable=False)
    summary = Column(String(512), nullable=False)
    raw_snippet = Column(Text, nullable=True)  # File path, AST line number, schema excerpt, or SQL fragment
    provenance_details = Column(JSON, default=dict, nullable=False)

    edge = relationship("GraphEdge", back_populates="evidence_records")

    __table_args__ = (
        Index("ix_evidence_org_project", "organization_id", "project_id"),
    )


class CustomerMapping(Base, TimestampMixin):
    __tablename__ = "customer_mappings"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_name = Column(String(255), nullable=False, index=True)
    tier = Column(String(50), default="standard", nullable=False)  # "tier-1", "mission-critical", "enterprise", "standard"
    contract_sla = Column(String(100), default="99.9%", nullable=False)
    workflows = Column(JSON, default=list, nullable=False)  # List of critical workflows, e.g. ["InstantPayouts", "CreditCheck"]
    consumed_endpoints = Column(JSON, default=list, nullable=False)  # Explicitly contracted APIs
    metadata_info = Column(JSON, default=dict, nullable=False)

    __table_args__ = (
        UniqueConstraint("project_id", "customer_name", name="uq_project_customer_name"),
        Index("ix_cust_org_project", "organization_id", "project_id"),
    )
