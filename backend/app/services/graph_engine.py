from typing import List, Dict, Any, Set, Tuple
import networkx as nx
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.graph import (
    GraphNode,
    GraphEdge,
    NodeType,
    EdgeType,
    EvidenceConfidence,
    EvidenceRecord,
)
from app.schemas.graph import (
    TopologyGraphResponse,
    GraphNodeRead,
    GraphEdgeRead,
    EvidenceRecordRead,
    GraphMetrics,
)


class GraphEngine:
    @staticmethod
    def load_networkx_graph(db: Session, project_id: str) -> Tuple[nx.DiGraph, Dict[str, GraphNode]]:
        """Construct an in-memory NetworkX directed graph from persisted project nodes and edges."""
        nodes = db.query(GraphNode).filter(GraphNode.project_id == project_id).all()
        edges = db.query(GraphEdge).filter(GraphEdge.project_id == project_id).all()

        G = nx.DiGraph()
        node_lookup = {n.id: n for n in nodes}

        for n in nodes:
            G.add_node(
                n.id,
                identifier=n.identifier,
                name=n.name,
                node_type=n.node_type.value,
                description=n.description,
            )

        for e in edges:
            G.add_edge(
                e.source_node_id,
                e.target_node_id,
                edge_id=e.id,
                edge_type=e.edge_type.value,
                confidence=e.confidence.value,
                weight=e.weight,
            )

        return G, node_lookup

    @staticmethod
    def get_topology(db: Session, organization_id: str, project_id: str) -> TopologyGraphResponse:
        nodes = (
            db.query(GraphNode)
            .filter(GraphNode.organization_id == organization_id, GraphNode.project_id == project_id)
            .all()
        )
        edges = (
            db.query(GraphEdge)
            .filter(GraphEdge.organization_id == organization_id, GraphEdge.project_id == project_id)
            .all()
        )

        node_schemas = [GraphNodeRead.model_validate(n) for n in nodes]
        edge_schemas = []
        for e in edges:
            ev_schemas = [EvidenceRecordRead.model_validate(ev) for ev in e.evidence_records]
            edge_data = GraphEdgeRead(
                id=e.id,
                organization_id=e.organization_id,
                project_id=e.project_id,
                source_node_id=e.source_node_id,
                target_node_id=e.target_node_id,
                edge_type=e.edge_type,
                confidence=e.confidence,
                weight=e.weight,
                metadata_info=e.metadata_info,
                created_at=e.created_at,
                evidence_records=ev_schemas,
            )
            edge_schemas.append(edge_data)

        # Build in-memory NetworkX graph for topology metrics
        G, _ = GraphEngine.load_networkx_graph(db, project_id)

        # Detect High Centrality / Potential Single Point of Failure (SPOF)
        spof_candidates = []
        if len(G.nodes) > 2:
            centrality = nx.betweenness_centrality(G)
            sorted_by_centrality = sorted(centrality.items(), key=lambda x: x[1], reverse=True)
            node_map = {n.id: n.name for n in nodes}
            for nid, score in sorted_by_centrality[:3]:
                if score > 0.15:
                    spof_candidates.append(node_map.get(nid, nid))

        metrics = GraphMetrics(
            total_nodes=len(nodes),
            total_edges=len(edges),
            services_count=sum(1 for n in nodes if n.node_type == NodeType.SERVICE),
            endpoints_count=sum(1 for n in nodes if n.node_type == NodeType.ENDPOINT),
            tables_count=sum(1 for n in nodes if n.node_type == NodeType.DATABASE_TABLE),
            customers_count=sum(1 for n in nodes if n.node_type == NodeType.CUSTOMER_WORKFLOW),
            confirmed_edges=sum(1 for e in edges if e.confidence == EvidenceConfidence.CONFIRMED),
            inferred_edges=sum(1 for e in edges if e.confidence == EvidenceConfidence.INFERRED),
            unknown_edges=sum(1 for e in edges if e.confidence == EvidenceConfidence.UNKNOWN),
            spof_candidates=spof_candidates,
        )

        return TopologyGraphResponse(
            nodes=node_schemas,
            edges=edge_schemas,
            metrics=metrics,
        )

    @staticmethod
    def get_or_create_node(
        db: Session,
        organization_id: str,
        project_id: str,
        node_type: NodeType,
        identifier: str,
        name: str,
        description: str = None,
        metadata_info: dict = None,
    ) -> GraphNode:
        node = (
            db.query(GraphNode)
            .filter(
                GraphNode.project_id == project_id,
                GraphNode.node_type == node_type,
                GraphNode.identifier == identifier,
            )
            .first()
        )
        if not node:
            node = GraphNode(
                organization_id=organization_id,
                project_id=project_id,
                node_type=node_type,
                identifier=identifier,
                name=name,
                description=description,
                metadata_info=metadata_info or {},
            )
            db.add(node)
            db.flush()
        return node

    @staticmethod
    def link_nodes(
        db: Session,
        organization_id: str,
        project_id: str,
        source_node_id: str,
        target_node_id: str,
        edge_type: EdgeType,
        confidence: EvidenceConfidence,
        evidence_summary: str,
        source_kind: Any,
        raw_snippet: str = None,
        provenance_details: dict = None,
    ) -> GraphEdge:
        edge = (
            db.query(GraphEdge)
            .filter(
                GraphEdge.source_node_id == source_node_id,
                GraphEdge.target_node_id == target_node_id,
                GraphEdge.edge_type == edge_type,
            )
            .first()
        )
        if not edge:
            edge = GraphEdge(
                organization_id=organization_id,
                project_id=project_id,
                source_node_id=source_node_id,
                target_node_id=target_node_id,
                edge_type=edge_type,
                confidence=confidence,
                metadata_info={},
            )
            db.add(edge)
            db.flush()
        else:
            # Upgrade confidence if new evidence is CONFIRMED
            if confidence == EvidenceConfidence.CONFIRMED and edge.confidence != EvidenceConfidence.CONFIRMED:
                edge.confidence = EvidenceConfidence.CONFIRMED

        # Add Evidence record
        evidence = EvidenceRecord(
            organization_id=organization_id,
            project_id=project_id,
            edge_id=edge.id,
            source_kind=source_kind,
            confidence=confidence,
            summary=evidence_summary,
            raw_snippet=raw_snippet,
            provenance_details=provenance_details or {},
        )
        db.add(evidence)
        db.flush()

        return edge

    @staticmethod
    def compute_downstream_impact(
        db: Session,
        project_id: str,
        start_node_id: str,
    ) -> Dict[str, Any]:
        """Compute the downstream transitive blast radius using NetworkX forward traversal."""
        G, node_lookup = GraphEngine.load_networkx_graph(db, project_id)

        if start_node_id not in G:
            raise HTTPException(status_code=404, detail="Target node not found in topology graph")

        # In a dependency graph: If A calls B, and B changes, A is impacted.
        # So we look at callers / ancestors of the changed component in the directed graph.
        impacted_nodes_ids = nx.ancestors(G, start_node_id) | {start_node_id}
        subgraph = G.subgraph(impacted_nodes_ids)

        impacted_services = []
        impacted_endpoints = []
        impacted_customers = []
        has_unknown_dependencies = False

        for nid in impacted_nodes_ids:
            node = node_lookup.get(nid)
            if not node:
                continue
            if node.node_type == NodeType.SERVICE:
                impacted_services.append(node.name)
            elif node.node_type == NodeType.ENDPOINT:
                impacted_endpoints.append(node.name)
            elif node.node_type == NodeType.CUSTOMER_WORKFLOW:
                impacted_customers.append(node.name)

        # Check if any incoming or outgoing edge in the blast radius has UNKNOWN confidence
        for u, v, data in subgraph.edges(data=True):
            if data.get("confidence") == EvidenceConfidence.UNKNOWN.value:
                has_unknown_dependencies = True
                break

        return {
            "root_node_id": start_node_id,
            "root_node_name": node_lookup[start_node_id].name if start_node_id in node_lookup else start_node_id,
            "total_impacted_nodes": len(impacted_nodes_ids),
            "impacted_services": list(set(impacted_services)),
            "impacted_endpoints": list(set(impacted_endpoints)),
            "impacted_customers": list(set(impacted_customers)),
            "has_unknown_dependencies": has_unknown_dependencies,
            "safety_verdict": "CAUTION_REQUIRED" if has_unknown_dependencies else "CONFIRMED_IMPACT_SET",
        }
