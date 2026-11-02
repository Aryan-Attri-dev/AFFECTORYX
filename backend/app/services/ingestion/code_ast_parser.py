import ast
import re
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.graph import (
    NodeType,
    EdgeType,
    EvidenceConfidence,
    EvidenceSourceKind,
)
from app.services.graph_engine import GraphEngine
from app.schemas.graph import CodeASTIngestionSummary


class CodeASTScanner:
    @staticmethod
    def scan_python_code(
        db: Session,
        organization_id: str,
        project_id: str,
        caller_service_name: str,
        file_path: str,
        code_content: str,
    ) -> CodeASTIngestionSummary:
        """Statically inspect Python source code AST for HTTP client callsites without executing code."""
        callsites_found = 0
        dependencies_found = 0
        edges_created = 0
        unknown_flagged = 0

        # Ensure caller service node exists
        caller_node = GraphEngine.get_or_create_node(
            db=db,
            organization_id=organization_id,
            project_id=project_id,
            node_type=NodeType.SERVICE,
            identifier=f"service:{caller_service_name.lower().replace(' ', '-')}",
            name=caller_service_name,
            description=f"Service {caller_service_name}",
        )

        try:
            tree = ast.parse(code_content, filename=file_path)
        except SyntaxError:
            # Fall back to regex scanning if file has syntax variations
            return CodeASTScanner.scan_generic_code(
                db=db,
                organization_id=organization_id,
                project_id=project_id,
                caller_service_name=caller_service_name,
                file_path=file_path,
                code_content=code_content,
            )

        http_methods = {"get", "post", "put", "delete", "patch", "request"}

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                method_name = None
                caller_lib = None

                if isinstance(node.func, ast.Attribute):
                    method_name = node.func.attr.lower()
                    if isinstance(node.func.value, ast.Name):
                        caller_lib = node.func.value.id.lower()

                # Detect requests.<method>, httpx.<method>, client.<method>, api.<method>
                if method_name in http_methods or caller_lib in {"requests", "httpx", "client", "session", "api"}:
                    callsites_found += 1
                    target_endpoint = None
                    confidence = EvidenceConfidence.INFERRED
                    line_no = getattr(node, "lineno", 1)

                    # Inspect first argument (target URL)
                    if node.args:
                        first_arg = node.args[0]
                        if isinstance(first_arg, ast.Constant) and isinstance(first_arg.value, str):
                            target_endpoint = first_arg.value
                            confidence = EvidenceConfidence.CONFIRMED
                        elif isinstance(first_arg, ast.JoinedStr):
                            # f-string: extract literal parts
                            parts = [p.value for p in first_arg.values if isinstance(p, ast.Constant)]
                            target_endpoint = "".join(parts) or "dynamic_route"
                            confidence = EvidenceConfidence.INFERRED
                        else:
                            target_endpoint = "dynamic_unresolved_callsite"
                            confidence = EvidenceConfidence.UNKNOWN
                            unknown_flagged += 1
                    else:
                        target_endpoint = "unspecified_endpoint"
                        confidence = EvidenceConfidence.UNKNOWN
                        unknown_flagged += 1

                    # Extract relative path if full URL
                    clean_endpoint = target_endpoint
                    if "://" in clean_endpoint:
                        clean_endpoint = "/" + clean_endpoint.split("://", 1)[1].split("/", 1)[-1]

                    target_identifier = f"HTTP {clean_endpoint}"
                    target_node = GraphEngine.get_or_create_node(
                        db=db,
                        organization_id=organization_id,
                        project_id=project_id,
                        node_type=NodeType.ENDPOINT if "/" in clean_endpoint else NodeType.EXTERNAL_API,
                        identifier=target_identifier,
                        name=target_identifier,
                        description=f"Inferred dependency target at {file_path}:{line_no}",
                    )
                    dependencies_found += 1

                    snippet = f"{file_path}:{line_no} -> {caller_lib or 'http'}.{method_name}('{target_endpoint}')"
                    GraphEngine.link_nodes(
                        db=db,
                        organization_id=organization_id,
                        project_id=project_id,
                        source_node_id=caller_node.id,
                        target_node_id=target_node.id,
                        edge_type=EdgeType.CALLS_API,
                        confidence=confidence,
                        evidence_summary=f"Static AST callsite located in '{file_path}' line {line_no}",
                        source_kind=EvidenceSourceKind.CODE_AST,
                        raw_snippet=snippet,
                        provenance_details={"file": file_path, "line": line_no, "confidence": confidence.value},
                    )
                    edges_created += 1

        db.commit()

        return CodeASTIngestionSummary(
            files_analyzed=1,
            callsites_discovered=callsites_found,
            service_dependencies_discovered=dependencies_found,
            edges_created=edges_created,
            unknown_routes_flagged=unknown_flagged,
        )

    @staticmethod
    def scan_generic_code(
        db: Session,
        organization_id: str,
        project_id: str,
        caller_service_name: str,
        file_path: str,
        code_content: str,
    ) -> CodeASTIngestionSummary:
        """Regex-based static scanning for TypeScript, JavaScript, Go, or Ruby files."""
        caller_node = GraphEngine.get_or_create_node(
            db=db,
            organization_id=organization_id,
            project_id=project_id,
            node_type=NodeType.SERVICE,
            identifier=f"service:{caller_service_name.lower().replace(' ', '-')}",
            name=caller_service_name,
        )

        callsites_found = 0
        edges_created = 0
        unknown_flagged = 0

        # Pattern: fetch('/api/...'), axios.get('/api/...'), http.Get("http://...")
        pattern = re.compile(
            r"""(?:fetch|axios\.(?:get|post|put|delete|patch)|\.request)\s*\(\s*['"`]([^'"`]+)['"`]""",
            re.IGNORECASE,
        )

        lines = code_content.splitlines()
        for i, line in enumerate(lines, 1):
            matches = pattern.finditer(line)
            for m in matches:
                callsites_found += 1
                raw_url = m.group(1)
                is_dynamic = "${" in raw_url or "%s" in raw_url
                confidence = EvidenceConfidence.UNKNOWN if is_dynamic else EvidenceConfidence.INFERRED
                if is_dynamic:
                    unknown_flagged += 1

                clean_endpoint = raw_url
                if "://" in clean_endpoint:
                    clean_endpoint = "/" + clean_endpoint.split("://", 1)[1].split("/", 1)[-1]

                target_node = GraphEngine.get_or_create_node(
                    db=db,
                    organization_id=organization_id,
                    project_id=project_id,
                    node_type=NodeType.ENDPOINT,
                    identifier=f"HTTP {clean_endpoint}",
                    name=f"HTTP {clean_endpoint}",
                )

                snippet = f"{file_path}:{i} -> {line.strip()}"
                GraphEngine.link_nodes(
                    db=db,
                    organization_id=organization_id,
                    project_id=project_id,
                    source_node_id=caller_node.id,
                    target_node_id=target_node.id,
                    edge_type=EdgeType.CALLS_API,
                    confidence=confidence,
                    evidence_summary=f"Static callsite match in '{file_path}' line {i}",
                    source_kind=EvidenceSourceKind.CODE_AST,
                    raw_snippet=snippet,
                    provenance_details={"file": file_path, "line": i, "confidence": confidence.value},
                )
                edges_created += 1

        db.commit()

        return CodeASTIngestionSummary(
            files_analyzed=1,
            callsites_discovered=callsites_found,
            service_dependencies_discovered=callsites_found,
            edges_created=edges_created,
            unknown_routes_flagged=unknown_flagged,
        )
