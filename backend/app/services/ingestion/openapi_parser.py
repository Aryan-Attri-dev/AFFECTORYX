import json
from typing import Dict, Any, Tuple
import yaml
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.graph import (
    NodeType,
    EdgeType,
    EvidenceConfidence,
    EvidenceSourceKind,
)
from app.services.graph_engine import GraphEngine
from app.schemas.graph import OpenAPIIngestionSummary


class OpenAPIParser:
    @staticmethod
    def parse_content(content_str: str) -> Dict[str, Any]:
        """Safely parse OpenAPI spec in JSON or YAML format without executing code."""
        content_str = content_str.strip()
        if content_str.startswith("{"):
            try:
                return json.loads(content_str)
            except json.JSONDecodeError as e:
                raise HTTPException(status_code=400, detail=f"Invalid JSON OpenAPI specification: {str(e)}")
        try:
            return yaml.safe_load(content_str)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid YAML OpenAPI specification: {str(e)}")

    @staticmethod
    def ingest_spec(
        db: Session,
        organization_id: str,
        project_id: str,
        spec_content: str,
        spec_source_name: str = "openapi_spec.json",
    ) -> OpenAPIIngestionSummary:
        spec = OpenAPIParser.parse_content(spec_content)

        info = spec.get("info", {})
        title = info.get("title", "Unknown Service API")
        version = info.get("version", "1.0.0")

        # 1. Register or get Service node
        service_node = GraphEngine.get_or_create_node(
            db=db,
            organization_id=organization_id,
            project_id=project_id,
            node_type=NodeType.SERVICE,
            identifier=f"service:{title.lower().replace(' ', '-')}",
            name=title,
            description=info.get("description", f"OpenAPI Service {title}"),
            metadata_info={"version": version, "spec_source": spec_source_name},
        )

        paths = spec.get("paths", {})
        endpoints_count = 0
        edges_count = 0
        evidence_count = 0

        # 2. Iterate endpoints and operations
        valid_methods = {"get", "post", "put", "patch", "delete", "options", "head"}
        for path_key, path_item in paths.items():
            if not isinstance(path_item, dict):
                continue

            for method, operation in path_item.items():
                if method.lower() not in valid_methods or not isinstance(operation, dict):
                    continue

                method_upper = method.upper()
                op_id = operation.get("operationId", f"{method_upper}_{path_key}")
                summary = operation.get("summary", f"{method_upper} {path_key}")

                # Extract request/response schema metadata
                req_body = operation.get("requestBody", {})
                responses = operation.get("responses", {})
                status_codes = list(responses.keys())

                endpoint_identifier = f"{method_upper} {path_key}"
                endpoint_node = GraphEngine.get_or_create_node(
                    db=db,
                    organization_id=organization_id,
                    project_id=project_id,
                    node_type=NodeType.ENDPOINT,
                    identifier=endpoint_identifier,
                    name=endpoint_identifier,
                    description=summary,
                    metadata_info={
                        "operationId": op_id,
                        "status_codes": status_codes,
                        "parameters": [p.get("name") for p in operation.get("parameters", []) if isinstance(p, dict)],
                        "has_request_body": bool(req_body),
                    },
                )
                endpoints_count += 1

                # Link Service -> Endpoint (Service exposes this endpoint)
                evidence_snippet = f"{method_upper} {path_key} -> operationId: {op_id}"
                GraphEngine.link_nodes(
                    db=db,
                    organization_id=organization_id,
                    project_id=project_id,
                    source_node_id=service_node.id,
                    target_node_id=endpoint_node.id,
                    edge_type=EdgeType.DEPENDS_ON,
                    confidence=EvidenceConfidence.CONFIRMED,
                    evidence_summary=f"Declared in OpenAPI specification '{spec_source_name}'",
                    source_kind=EvidenceSourceKind.OPENAPI_SPEC,
                    raw_snippet=evidence_snippet,
                    provenance_details={"spec_file": spec_source_name, "path": path_key, "method": method_upper},
                )
                edges_count += 1
                evidence_count += 1

        schemas = spec.get("components", {}).get("schemas", {})
        schemas_count = len(schemas)

        db.commit()

        return OpenAPIIngestionSummary(
            title=title,
            version=version,
            endpoints_discovered=endpoints_count,
            schemas_discovered=schemas_count,
            edges_created=edges_count,
            evidence_records_created=evidence_count,
        )
