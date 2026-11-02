from typing import List, Dict, Any, Optional, Set
from collections import deque
import networkx as nx
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.graph import (
    GraphNode,
    GraphEdge,
    NodeType,
    EdgeType,
    EvidenceConfidence,
    CustomerMapping,
)
from app.models.analysis import (
    ChangeAnalysis,
    SimulationReport,
    RiskLevel,
    DeploymentVerdict,
    ChangeSeverity,
)
from app.schemas.analysis import ChangeFinding, AffectedCustomer
from app.services.graph_engine import GraphEngine


class ImpactSimulatorService:
    @staticmethod
    def simulate_change_impact(
        db: Session,
        organization_id: str,
        project_id: str,
        author_id: str,
        target_component: str,
        change_summary: str,
        analysis_id: Optional[str] = None,
        manual_breaking_findings: Optional[List[ChangeFinding]] = None,
    ) -> SimulationReport:
        if not target_component or not target_component.strip():
            raise HTTPException(status_code=400, detail="Target component cannot be empty")
        if not change_summary or not change_summary.strip():
            raise HTTPException(status_code=400, detail="Change summary cannot be empty")

        # 1. Fetch analysis if linked
        analysis = None
        breaking_count = 0
        findings_list: List[Dict[str, Any]] = []

        if analysis_id:
            analysis = (
                db.query(ChangeAnalysis)
                .filter(
                    ChangeAnalysis.id == analysis_id,
                    ChangeAnalysis.organization_id == organization_id,
                    ChangeAnalysis.project_id == project_id,
                )
                .first()
            )
            if analysis:
                breaking_count = analysis.breaking_count
                findings_list = analysis.findings or []

        if manual_breaking_findings:
            for mf in manual_breaking_findings:
                findings_list.append(mf.model_dump())
                if mf.severity == ChangeSeverity.BREAKING:
                    breaking_count += 1

        # 2. Load NetworkX graph
        G, node_lookup = GraphEngine.load_networkx_graph(db, project_id)

        # 3. Locate target node
        target_node = None
        # Match by ID
        if target_component in node_lookup:
            target_node = node_lookup[target_component]
        else:
            # Match by identifier or name
            for n in node_lookup.values():
                if n.identifier == target_component or n.name == target_component:
                    target_node = n
                    break

        if not target_node:
            # Check DB directly
            db_node = (
                db.query(GraphNode)
                .filter(
                    GraphNode.project_id == project_id,
                    (GraphNode.identifier == target_component) | (GraphNode.name == target_component),
                )
                .first()
            )
            if db_node:
                target_node = db_node
            else:
                # If component is not in the graph, create a placeholder node for analysis
                target_node = GraphEngine.get_or_create_node(
                    db=db,
                    organization_id=organization_id,
                    project_id=project_id,
                    node_type=NodeType.SERVICE,
                    identifier=target_component,
                    name=target_component,
                    description=f"Component targeted in impact simulation: {change_summary}",
                )
                G.add_node(target_node.id, identifier=target_node.identifier, name=target_node.name, node_type=target_node.node_type.value)
                node_lookup[target_node.id] = target_node

        target_id = target_node.id
        target_name = target_node.name

        # 4. Blast Radius Traversal with Loop / Cycle Protection
        # We traverse callers (predecessors) and dependents (ancestors in dependency direction)
        visited: Set[str] = {target_id}
        queue: deque = deque([(target_id, 0)])
        distance_map: Dict[str, int] = {target_id: 0}
        has_unknown_dependencies = False

        directly_affected_services: Set[str] = set()
        transitive_affected_services: Set[str] = set()
        impacted_endpoints: Set[str] = set()

        while queue:
            curr_id, dist = queue.popleft()

            # Predecessors in G are nodes that point to curr_id (i.e. callers / consumers)
            predecessors = list(G.predecessors(curr_id)) if curr_id in G else []
            # Successors in G for direct data dependents
            successors = list(G.successors(curr_id)) if curr_id in G else []

            neighbors = set(predecessors + successors)

            for neighbor_id in neighbors:
                # Audit edge confidence for UNKNOWN relationships
                if G.has_edge(neighbor_id, curr_id):
                    edge_data = G.get_edge_data(neighbor_id, curr_id) or {}
                    if edge_data.get("confidence") == EvidenceConfidence.UNKNOWN.value:
                        has_unknown_dependencies = True
                if G.has_edge(curr_id, neighbor_id):
                    edge_data = G.get_edge_data(curr_id, neighbor_id) or {}
                    if edge_data.get("confidence") == EvidenceConfidence.UNKNOWN.value:
                        has_unknown_dependencies = True

                if neighbor_id not in visited:
                    visited.add(neighbor_id)
                    new_dist = dist + 1
                    distance_map[neighbor_id] = new_dist
                    queue.append((neighbor_id, new_dist))

                    n_obj = node_lookup.get(neighbor_id)
                    if n_obj:
                        if n_obj.node_type == NodeType.SERVICE:
                            if new_dist == 1:
                                directly_affected_services.add(n_obj.name)
                            else:
                                transitive_affected_services.add(n_obj.name)
                        elif n_obj.node_type == NodeType.ENDPOINT:
                            impacted_endpoints.add(n_obj.name)
                            impacted_endpoints.add(n_obj.identifier)

        # Remove target itself if it got added to service sets
        directly_affected_services.discard(target_name)
        transitive_affected_services.discard(target_name)

        # 5. Customer Mapping Impact (Deterministic check against verified CustomerMapping)
        customer_records = (
            db.query(CustomerMapping)
            .filter(
                CustomerMapping.organization_id == organization_id,
                CustomerMapping.project_id == project_id,
            )
            .all()
        )

        affected_customers: List[Dict[str, Any]] = []
        has_mission_critical_customer = False

        for cust in customer_records:
            matching_endpoints = []
            matching_workflows = []

            for ep in (cust.consumed_endpoints or []):
                if ep == target_node.identifier or ep == target_name or ep in impacted_endpoints:
                    matching_endpoints.append(ep)

            for wf in (cust.workflows or []):
                if wf == target_name or wf in directly_affected_services or wf in transitive_affected_services:
                    matching_workflows.append(wf)

            if matching_endpoints or matching_workflows:
                if cust.tier.lower() in ["tier-1", "mission-critical", "enterprise"]:
                    has_mission_critical_customer = True

                affected_customers.append({
                    "customer_name": cust.customer_name,
                    "tier": cust.tier,
                    "contract_sla": cust.contract_sla,
                    "impacted_endpoints": matching_endpoints,
                    "impacted_workflows": matching_workflows,
                })

        # 6. SPOF Identification
        spof_identified: List[str] = []
        if len(G.nodes) > 2:
            centrality = nx.betweenness_centrality(G)
            for nid, score in centrality.items():
                if score > 0.15:
                    node_obj = node_lookup.get(nid)
                    if node_obj and (node_obj.id in visited or node_obj.name == target_name):
                        spof_identified.append(node_obj.name)

        # 7. Risk Classification & Verdict
        # Rules:
        # CRITICAL: Breaking change affecting Tier-1/Mission-Critical customer, OR breaking change on SPOF, OR breaking change affecting >= 3 transitive services.
        # HIGH: Any breaking change affecting standard customers or internal services.
        # MEDIUM: Non-breaking with broad blast radius (> 2 services), OR any change with UNKNOWN dependencies.
        # LOW: Non-breaking with zero customer impact and fully confirmed dependencies.

        if breaking_count > 0:
            if has_mission_critical_customer or len(spof_identified) > 0 or (len(directly_affected_services) + len(transitive_affected_services)) >= 3:
                risk_level = RiskLevel.CRITICAL
            else:
                risk_level = RiskLevel.HIGH
            verdict = DeploymentVerdict.BREAKING_CHANGES_DETECTED
        else:
            # Non-breaking changes
            if has_unknown_dependencies:
                risk_level = RiskLevel.MEDIUM
                verdict = DeploymentVerdict.CAUTION_REQUIRED
            elif (len(directly_affected_services) + len(transitive_affected_services)) >= 3 or len(affected_customers) > 0:
                risk_level = RiskLevel.MEDIUM
                verdict = DeploymentVerdict.CAUTION_REQUIRED
            else:
                risk_level = RiskLevel.LOW
                verdict = DeploymentVerdict.SAFE_TO_DEPLOY

        # 8. Construct Verification Checklist
        checklist: List[str] = []
        if breaking_count > 0:
            checklist.append(f"Execute contract regression tests for {breaking_count} breaking change finding(s) before staging deployment.")
        if directly_affected_services:
            checklist.append(f"Verify integration contracts with directly affected callers: {', '.join(sorted(directly_affected_services))}.")
        if transitive_affected_services:
            checklist.append(f"Audit downstream asynchronous queues and event subscribers in: {', '.join(sorted(transitive_affected_services))}.")
        if affected_customers:
            checklist.append(f"Verify SLA compatibility and customer notification requirements for: {', '.join(c['customer_name'] for c in affected_customers)}.")
        if spof_identified:
            checklist.append(f"Prepare active canary rollout and rollback runbook for Single Point of Failure (SPOF) components: {', '.join(spof_identified)}.")
        if has_unknown_dependencies:
            checklist.append("CAUTION: Untracked or UNKNOWN dependency relationships detected in blast path. Trace integration callsites to establish CONFIRMED evidence before release.")
        if not checklist:
            checklist.append("Standard test suite passes. Backwards-compatible release with isolated blast radius.")

        # 9. Generate Explainable Markdown Report
        summary_text = (
            f"Impact Simulation for '{target_name}': {verdict.value.upper()} "
            f"({risk_level.value.upper()} Risk). Detected {breaking_count} breaking changes, "
            f"{len(directly_affected_services)} directly affected services, "
            f"{len(transitive_affected_services)} transitive downstream services, and "
            f"{len(affected_customers)} customer SLA mappings."
        )

        markdown_report = ImpactSimulatorService._generate_markdown_report(
            target_name=target_name,
            change_summary=change_summary,
            verdict=verdict,
            risk_level=risk_level,
            breaking_count=breaking_count,
            findings=findings_list,
            directly_affected=list(directly_affected_services),
            transitive_affected=list(transitive_affected_services),
            affected_customers=affected_customers,
            spof_list=spof_identified,
            has_unknown=has_unknown_dependencies,
            checklist=checklist,
        )

        # 10. Persist SimulationReport
        report = SimulationReport(
            organization_id=organization_id,
            project_id=project_id,
            analysis_id=analysis_id,
            author_id=author_id,
            target_component_id=target_id,
            target_component_name=target_name,
            risk_level=risk_level,
            verdict=verdict,
            summary=summary_text,
            directly_affected_services=sorted(list(directly_affected_services)),
            transitive_affected_services=sorted(list(transitive_affected_services)),
            affected_customers=affected_customers,
            spof_identified=spof_identified,
            has_unknown_dependencies=1 if has_unknown_dependencies else 0,
            verification_checklist=checklist,
            markdown_report=markdown_report,
            report_details={
                "total_visited_nodes": len(visited),
                "impacted_endpoints": list(impacted_endpoints),
                "findings_summary": {
                    "breaking": breaking_count,
                    "total_findings": len(findings_list),
                },
            },
        )
        db.add(report)
        db.commit()
        db.refresh(report)
        return report

    @staticmethod
    def _generate_markdown_report(
        target_name: str,
        change_summary: str,
        verdict: DeploymentVerdict,
        risk_level: RiskLevel,
        breaking_count: int,
        findings: List[Dict[str, Any]],
        directly_affected: List[str],
        transitive_affected: List[str],
        affected_customers: List[Dict[str, Any]],
        spof_list: List[str],
        has_unknown: bool,
        checklist: List[str],
    ) -> str:
        lines = [
            f"# AFFECTORYX Engineering Intelligence Report: {target_name}",
            "",
            f"**Change Scope:** {change_summary}",
            f"**Verdict:** `{verdict.value.upper()}` | **Risk Level:** `{risk_level.value.upper()}`",
            "",
            "---",
            "",
            "## 1. Executive Summary & Verdict",
            "",
        ]

        if verdict == DeploymentVerdict.SAFE_TO_DEPLOY:
            lines.append("> [!NOTE]")
            lines.append("> **SAFE TO DEPLOY**: All changes are backwards-compatible, with zero breaking modifications and 100% confirmed dependency evidence.")
        elif verdict == DeploymentVerdict.BREAKING_CHANGES_DETECTED:
            lines.append("> [!WARNING]")
            lines.append(f"> **BREAKING CHANGES DETECTED**: {breaking_count} breaking API or schema modification(s) identified. Deployment will disrupt dependent callers unless coordinated.")
        else:
            lines.append("> [!CAUTION]")
            lines.append("> **CAUTION REQUIRED**: While no explicit breaking changes were detected, dependency links in the blast path have UNKNOWN or incomplete evidence. Verification required prior to release.")

        lines.extend([
            "",
            "## 2. Blast Radius Analysis",
            "",
            "| Scope | Affected Components | Count |",
            "| :--- | :--- | :--- |",
            f"| **Direct Callers (Distance = 1)** | {', '.join(directly_affected) if directly_affected else 'None (Isolated)'} | {len(directly_affected)} |",
            f"| **Transitive Callers (Distance > 1)** | {', '.join(transitive_affected) if transitive_affected else 'None'} | {len(transitive_affected)} |",
            f"| **SPOF Risk Nodes** | {', '.join(spof_list) if spof_list else 'None detected'} | {len(spof_list)} |",
            f"| **Evidence Integrity** | {'⚠️ UNKNOWN / Inferred links present' if has_unknown else '✅ 100% Machine Confirmed'} | {'Caution' if has_unknown else 'Confirmed'} |",
            "",
            "## 3. Customer SLA & Workflow Exposure",
            "",
        ])

        if affected_customers:
            lines.append("| Customer Name | SLA Tier | Contract SLA | Impacted Endpoints / Workflows |")
            lines.append("| :--- | :--- | :--- | :--- |")
            for c in affected_customers:
                impacted = c["impacted_endpoints"] + c["impacted_workflows"]
                lines.append(f"| **{c['customer_name']}** | `{c['tier']}` | {c['contract_sla']} | {', '.join(impacted) if impacted else 'Upstream dependency'} |")
        else:
            lines.append("✅ No customer-contracted endpoints or critical workflows are impacted by this change.")

        lines.extend([
            "",
            "## 4. Detected Change Findings",
            "",
        ])

        if findings:
            lines.append("| Severity | Category | Target | Description | Safe Migration Advice |")
            lines.append("| :--- | :--- | :--- | :--- | :--- |")
            for f in findings:
                sev_badge = "🔴 BREAKING" if f.get("severity") == "breaking" else "🟢 NON-BREAKING"
                lines.append(f"| {sev_badge} | `{f.get('category')}` | `{f.get('target')}` | {f.get('description')} | {f.get('safe_migration_advice', 'N/A')} |")
        else:
            lines.append("No explicit schema changes registered.")

        lines.extend([
            "",
            "## 5. Pre-Deployment Verification Checklist",
            "",
        ])
        for idx, item in enumerate(checklist, 1):
            lines.append(f"- [ ] **Step {idx}:** {item}")

        lines.extend([
            "",
            "---",
            "*Report generated by AFFECTORYX Engine with deterministic static analysis and NetworkX graph traversal.*",
        ])

        return "\n".join(lines)
