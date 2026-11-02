from typing import List
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.graph import (
    CustomerMapping,
    NodeType,
    EdgeType,
    EvidenceConfidence,
    EvidenceSourceKind,
)
from app.services.graph_engine import GraphEngine
from app.schemas.graph import CustomerMappingCreate, CustomerMappingRead


class CustomerService:
    @staticmethod
    def list_customers(db: Session, organization_id: str, project_id: str) -> List[CustomerMappingRead]:
        records = (
            db.query(CustomerMapping)
            .filter(
                CustomerMapping.organization_id == organization_id,
                CustomerMapping.project_id == project_id,
            )
            .all()
        )
        return [CustomerMappingRead.model_validate(c) for c in records]

    @staticmethod
    def add_customer_mapping(
        db: Session,
        organization_id: str,
        project_id: str,
        data: CustomerMappingCreate,
    ) -> CustomerMappingRead:
        existing = (
            db.query(CustomerMapping)
            .filter(
                CustomerMapping.project_id == project_id,
                CustomerMapping.customer_name == data.customer_name,
            )
            .first()
        )
        if existing:
            raise HTTPException(status_code=400, detail=f"Customer '{data.customer_name}' already mapped in this project")

        mapping = CustomerMapping(
            organization_id=organization_id,
            project_id=project_id,
            customer_name=data.customer_name,
            tier=data.tier,
            contract_sla=data.contract_sla,
            workflows=data.workflows,
            consumed_endpoints=data.consumed_endpoints,
            metadata_info=data.metadata_info,
        )
        db.add(mapping)
        db.flush()

        # Register Customer Workflow Nodes and link to consumed endpoints
        for wf in data.workflows:
            wf_node = GraphEngine.get_or_create_node(
                db=db,
                organization_id=organization_id,
                project_id=project_id,
                node_type=NodeType.CUSTOMER_WORKFLOW,
                identifier=f"customer:{data.customer_name}:{wf}",
                name=f"{data.customer_name} — {wf}",
                description=f"Critical contracted workflow ({data.tier}, SLA {data.contract_sla})",
                metadata_info={"customer": data.customer_name, "tier": data.tier, "sla": data.contract_sla},
            )

            for endpoint_name in data.consumed_endpoints:
                endpoint_node = GraphEngine.get_or_create_node(
                    db=db,
                    organization_id=organization_id,
                    project_id=project_id,
                    node_type=NodeType.ENDPOINT,
                    identifier=endpoint_name,
                    name=endpoint_name,
                )
                # Link Customer Workflow -> Endpoint
                GraphEngine.link_nodes(
                    db=db,
                    organization_id=organization_id,
                    project_id=project_id,
                    source_node_id=wf_node.id,
                    target_node_id=endpoint_node.id,
                    edge_type=EdgeType.SERVES_CUSTOMER,
                    confidence=EvidenceConfidence.CONFIRMED,
                    evidence_summary=f"Explicit contract SLA agreement for customer '{data.customer_name}'",
                    source_kind=EvidenceSourceKind.CUSTOMER_CONTRACT,
                    raw_snippet=f"Customer: {data.customer_name}, Workflow: {wf}, SLA: {data.contract_sla}",
                    provenance_details={"customer": data.customer_name, "tier": data.tier},
                )

        db.commit()
        db.refresh(mapping)
        return CustomerMappingRead.model_validate(mapping)
