from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field
from app.models.graph import (
    NodeType,
    EdgeType,
    EvidenceConfidence,
    EvidenceSourceKind,
)


class GraphNodeBase(BaseModel):
    node_type: NodeType
    identifier: str
    name: str
    description: Optional[str] = None
    metadata_info: Dict[str, Any] = Field(default_factory=dict)


class GraphNodeCreate(GraphNodeBase):
    pass


class GraphNodeRead(GraphNodeBase):
    id: str
    organization_id: str
    project_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EvidenceRecordBase(BaseModel):
    source_kind: EvidenceSourceKind
    confidence: EvidenceConfidence
    summary: str
    raw_snippet: Optional[str] = None
    provenance_details: Dict[str, Any] = Field(default_factory=dict)


class EvidenceRecordCreate(EvidenceRecordBase):
    edge_id: Optional[str] = None


class EvidenceRecordRead(EvidenceRecordBase):
    id: str
    organization_id: str
    project_id: str
    edge_id: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GraphEdgeBase(BaseModel):
    source_node_id: str
    target_node_id: str
    edge_type: EdgeType
    confidence: EvidenceConfidence = EvidenceConfidence.INFERRED
    weight: float = 1.0
    metadata_info: Dict[str, Any] = Field(default_factory=dict)


class GraphEdgeCreate(GraphEdgeBase):
    evidence: Optional[EvidenceRecordBase] = None


class GraphEdgeRead(GraphEdgeBase):
    id: str
    organization_id: str
    project_id: str
    created_at: datetime
    evidence_records: List[EvidenceRecordRead] = []

    model_config = ConfigDict(from_attributes=True)


class CustomerMappingBase(BaseModel):
    customer_name: str
    tier: str = "standard"
    contract_sla: str = "99.9%"
    workflows: List[str] = []
    consumed_endpoints: List[str] = []
    metadata_info: Dict[str, Any] = Field(default_factory=dict)


class CustomerMappingCreate(CustomerMappingBase):
    pass


class CustomerMappingRead(CustomerMappingBase):
    id: str
    organization_id: str
    project_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GraphMetrics(BaseModel):
    total_nodes: int
    total_edges: int
    services_count: int
    endpoints_count: int
    tables_count: int
    customers_count: int
    confirmed_edges: int
    inferred_edges: int
    unknown_edges: int
    spof_candidates: List[str] = []  # Single points of failure / high-centrality nodes


class TopologyGraphResponse(BaseModel):
    nodes: List[GraphNodeRead]
    edges: List[GraphEdgeRead]
    metrics: GraphMetrics


class OpenAPIIngestionSummary(BaseModel):
    title: str
    version: str
    endpoints_discovered: int
    schemas_discovered: int
    edges_created: int
    evidence_records_created: int


class CodeASTIngestionSummary(BaseModel):
    files_analyzed: int
    callsites_discovered: int
    service_dependencies_discovered: int
    edges_created: int
    unknown_routes_flagged: int


class SQLMigrationIngestionSummary(BaseModel):
    tables_created: int
    tables_modified: int
    destructive_operations: List[str] = []  # Dropped tables, dropped columns, altered constraints
    edges_created: int
