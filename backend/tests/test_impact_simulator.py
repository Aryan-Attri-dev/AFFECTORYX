import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.graph import (
    NodeType,
    EdgeType,
    EvidenceConfidence,
    EvidenceSourceKind,
    CustomerMapping,
)
from app.models.analysis import RiskLevel, DeploymentVerdict, ChangeSeverity, BreakingCategory
from app.schemas.analysis import ChangeFinding
from app.services.graph_engine import GraphEngine
from app.services.impact_simulator import ImpactSimulatorService
from app.services.project_service import ProjectService
from app.schemas.project import ProjectCreate


@pytest.fixture
def topology_fixture(db: Session, test_user_a):
    user_id = test_user_a.user.id
    org_id = test_user_a.active_organization_id
    token = test_user_a.access_token
    actor = db.query(User).filter_by(id=user_id).first()

    project = ProjectService.create_project(
        db=db,
        organization_id=org_id,
        data=ProjectCreate(name="E-Commerce Architecture", key="ECOM"),
        actor=actor,
    )

    # Services
    checkout_svc = GraphEngine.get_or_create_node(
        db, org_id, project.id, NodeType.SERVICE, "service:checkout", "Checkout Service"
    )
    order_svc = GraphEngine.get_or_create_node(
        db, org_id, project.id, NodeType.SERVICE, "service:order", "Order Management"
    )
    payment_svc = GraphEngine.get_or_create_node(
        db, org_id, project.id, NodeType.SERVICE, "service:payment", "Payment Service"
    )
    fraud_svc = GraphEngine.get_or_create_node(
        db, org_id, project.id, NodeType.SERVICE, "service:fraud", "Fraud Detection"
    )
    notification_svc = GraphEngine.get_or_create_node(
        db, org_id, project.id, NodeType.SERVICE, "service:notification", "Notification Service"
    )

    # Endpoints
    pay_endpoint = GraphEngine.get_or_create_node(
        db, org_id, project.id, NodeType.ENDPOINT, "POST /api/v1/payments", "POST /api/v1/payments"
    )

    # Edges:
    # Checkout -> Order (Confirmed)
    # Order -> Payment (Confirmed)
    # Payment -> pay_endpoint (Confirmed)
    # Order -> Fraud (Confirmed)
    # Fraud -> Order (Mutual / Cycle edge! Testing loop handling)
    # Notification -> Order (Inferred)

    GraphEngine.link_nodes(
        db, org_id, project.id, checkout_svc.id, order_svc.id, EdgeType.DEPENDS_ON,
        EvidenceConfidence.CONFIRMED, "HTTP Checkout -> Order", EvidenceSourceKind.CODE_AST
    )
    GraphEngine.link_nodes(
        db, org_id, project.id, order_svc.id, payment_svc.id, EdgeType.DEPENDS_ON,
        EvidenceConfidence.CONFIRMED, "HTTP Order -> Payment", EvidenceSourceKind.CODE_AST
    )
    GraphEngine.link_nodes(
        db, org_id, project.id, payment_svc.id, pay_endpoint.id, EdgeType.DEPENDS_ON,
        EvidenceConfidence.CONFIRMED, "Payment exposes POST /api/v1/payments", EvidenceSourceKind.OPENAPI_SPEC
    )
    GraphEngine.link_nodes(
        db, org_id, project.id, order_svc.id, fraud_svc.id, EdgeType.DEPENDS_ON,
        EvidenceConfidence.CONFIRMED, "Order checks Fraud", EvidenceSourceKind.CODE_AST
    )
    # Mutual dependency cycle: Fraud -> Order
    GraphEngine.link_nodes(
        db, org_id, project.id, fraud_svc.id, order_svc.id, EdgeType.DEPENDS_ON,
        EvidenceConfidence.CONFIRMED, "Fraud queries Order history (Cycle)", EvidenceSourceKind.CODE_AST
    )

    # Customer Mappings
    cust_enterprise = CustomerMapping(
        organization_id=org_id,
        project_id=project.id,
        customer_name="Acme Global Retail",
        tier="mission-critical",
        contract_sla="99.99%",
        consumed_endpoints=["POST /api/v1/payments"],
        workflows=["Checkout Service"],
    )
    cust_standard = CustomerMapping(
        organization_id=org_id,
        project_id=project.id,
        customer_name="Local Artisan Co",
        tier="standard",
        contract_sla="99.5%",
        consumed_endpoints=["GET /api/v1/catalog"],
        workflows=[],
    )
    db.add(cust_enterprise)
    db.add(cust_standard)
    db.commit()

    return user_id, org_id, project, token, {
        "checkout": checkout_svc,
        "order": order_svc,
        "payment": payment_svc,
        "fraud": fraud_svc,
        "notification": notification_svc,
        "pay_endpoint": pay_endpoint,
    }


def test_blast_radius_and_cycle_handling(db: Session, topology_fixture):
    user_id, org_id, project, token, nodes = topology_fixture

    # Test simulating change on Payment Service
    # Directly affected: Order Management (dist = 1)
    # Transitive: Checkout Service (dist = 2), Fraud Detection (via Order)
    # Cycle between Fraud & Order MUST NOT cause infinite loop
    report = ImpactSimulatorService.simulate_change_impact(
        db=db,
        organization_id=org_id,
        project_id=project.id,
        author_id=user_id,
        target_component="service:payment",
        change_summary="Payment Gateway driver migration",
        manual_breaking_findings=[
            ChangeFinding(
                severity=ChangeSeverity.BREAKING,
                category=BreakingCategory.INCOMPATIBLE_TYPE,
                target="POST /api/v1/payments",
                description="Amount type changed",
                evidence="Float to string",
            )
        ],
    )

    assert "Order Management" in report.directly_affected_services
    assert "Checkout Service" in report.transitive_affected_services or "Fraud Detection" in report.transitive_affected_services
    # Customer impact verified
    customer_names = [c["customer_name"] for c in report.affected_customers]
    assert "Acme Global Retail" in customer_names
    assert "Local Artisan Co" not in customer_names  # Never manufacture false customer impact

    # Because Acme Global Retail is mission-critical and breaking change exists -> CRITICAL
    assert report.risk_level == RiskLevel.CRITICAL
    assert report.verdict == DeploymentVerdict.BREAKING_CHANGES_DETECTED
    assert len(report.verification_checklist) >= 3


def test_safe_to_deploy_verdict_when_non_breaking(db: Session, topology_fixture):
    user_id, org_id, project, token, nodes = topology_fixture

    # Non-breaking change on notification service (isolated)
    report = ImpactSimulatorService.simulate_change_impact(
        db=db,
        organization_id=org_id,
        project_id=project.id,
        author_id=user_id,
        target_component="service:notification",
        change_summary="Update email template header",
        manual_breaking_findings=[
            ChangeFinding(
                severity=ChangeSeverity.NON_BREAKING,
                category=BreakingCategory.SCHEMA_RESTRICTION,
                target="email_templates",
                description="New optional field banner_url",
                evidence="Added banner_url",
            )
        ],
    )

    assert report.risk_level == RiskLevel.LOW
    assert report.verdict == DeploymentVerdict.SAFE_TO_DEPLOY
    assert report.has_unknown_dependencies == 0


def test_unknown_dependency_triggers_caution_required(db: Session, topology_fixture):
    user_id, org_id, project, token, nodes = topology_fixture

    # Link an UNKNOWN edge into notification service
    GraphEngine.link_nodes(
        db, org_id, project.id, nodes["notification"].id, nodes["order"].id, EdgeType.DEPENDS_ON,
        EvidenceConfidence.UNKNOWN, "Ambiguous legacy webhook call", EvidenceSourceKind.CODE_AST
    )

    report = ImpactSimulatorService.simulate_change_impact(
        db=db,
        organization_id=org_id,
        project_id=project.id,
        author_id=user_id,
        target_component="service:notification",
        change_summary="Non-breaking webhook refactor",
        manual_breaking_findings=[],  # Zero breaking changes!
    )

    # Despite zero breaking changes, UNKNOWN dependency MUST trigger CAUTION_REQUIRED
    assert report.has_unknown_dependencies == 1
    assert report.verdict == DeploymentVerdict.CAUTION_REQUIRED
    assert report.risk_level == RiskLevel.MEDIUM


def test_simulator_api_and_markdown_export(client: TestClient, db: Session, topology_fixture):
    user_id, org_id, project, token, nodes = topology_fixture
    headers = {"Authorization": f"Bearer {token}", "X-Organization-ID": org_id}

    # 1. Trigger simulation via API
    res = client.post(
        f"/api/v1/projects/{project.id}/simulator/simulate",
        headers=headers,
        json={
            "project_id": project.id,
            "target_component": "POST /api/v1/payments",
            "change_summary": "Update Payment Endpoint signature",
        },
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert "verdict" in data
    assert "risk_level" in data
    report_id = data["id"]

    # 2. Fetch report list
    list_res = client.get(
        f"/api/v1/projects/{project.id}/simulator/reports",
        headers=headers,
    )
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1

    # 3. Export markdown
    export_res = client.get(
        f"/api/v1/projects/{project.id}/simulator/reports/{report_id}/export-markdown",
        headers=headers,
    )
    assert export_res.status_code == 200
    assert "# AFFECTORYX Engineering Intelligence Report" in export_res.text
    assert "Blast Radius Analysis" in export_res.text


def test_cyclical_graph_dependencies_termination(db: Session, topology_fixture):
    user_id, org_id, project, token, nodes = topology_fixture

    # Construct circular dependency: Service A -> Service B -> Service C -> Service A
    node_a = GraphEngine.get_or_create_node(db, org_id, project.id, NodeType.SERVICE, "cycle:service-a", "Cycle A")
    node_b = GraphEngine.get_or_create_node(db, org_id, project.id, NodeType.SERVICE, "cycle:service-b", "Cycle B")
    node_c = GraphEngine.get_or_create_node(db, org_id, project.id, NodeType.SERVICE, "cycle:service-c", "Cycle C")

    GraphEngine.link_nodes(db, org_id, project.id, node_a.id, node_b.id, EdgeType.DEPENDS_ON, EvidenceConfidence.CONFIRMED, "A->B", EvidenceSourceKind.CODE_AST)
    GraphEngine.link_nodes(db, org_id, project.id, node_b.id, node_c.id, EdgeType.DEPENDS_ON, EvidenceConfidence.CONFIRMED, "B->C", EvidenceSourceKind.CODE_AST)
    GraphEngine.link_nodes(db, org_id, project.id, node_c.id, node_a.id, EdgeType.DEPENDS_ON, EvidenceConfidence.CONFIRMED, "C->A", EvidenceSourceKind.CODE_AST)

    # Simulation must terminate cleanly without recursion or loop errors
    report = ImpactSimulatorService.simulate_change_impact(
        db=db,
        organization_id=org_id,
        project_id=project.id,
        author_id=user_id,
        target_component="cycle:service-a",
        change_summary="Refactor in circular graph",
        manual_breaking_findings=[],
    )

    assert "Cycle B" in report.directly_affected_services or "Cycle C" in report.directly_affected_services
    assert report.risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM]


def test_cross_tenant_simulation_and_export_blocked(client: TestClient, db: Session, topology_fixture, test_user_b):
    user_id_a, org_id_a, project_a, token_a, nodes = topology_fixture
    org_id_b = test_user_b.active_organization_id
    token_b = test_user_b.access_token

    headers_a = {"Authorization": f"Bearer {token_a}", "X-Organization-ID": org_id_a}
    headers_b = {"Authorization": f"Bearer {token_b}", "X-Organization-ID": org_id_b}

    # 1. User A runs simulation in Org A
    res = client.post(
        f"/api/v1/projects/{project_a.id}/simulator/simulate",
        headers=headers_a,
        json={
            "project_id": project_a.id,
            "target_component": "service:checkout",
            "change_summary": "Checkout update",
        },
    )
    assert res.status_code == 200
    report_id = res.json()["id"]

    # 2. User B in Org B attempts to access Org A's simulation report -> 404 forbidden
    cross_get = client.get(
        f"/api/v1/projects/{project_a.id}/simulator/reports/{report_id}",
        headers=headers_b,
    )
    assert cross_get.status_code == 404

    # 3. User B in Org B attempts to export Org A's simulation report markdown -> 404 forbidden
    cross_export = client.get(
        f"/api/v1/projects/{project_a.id}/simulator/reports/{report_id}/export-markdown",
        headers=headers_b,
    )
    assert cross_export.status_code == 404


def test_unauthorized_simulation_access(client: TestClient, topology_fixture):
    user_id, org_id, project, token, nodes = topology_fixture

    # Unauthenticated request -> 401
    res = client.post(
        f"/api/v1/projects/{project.id}/simulator/simulate",
        json={
            "project_id": project.id,
            "target_component": "service:checkout",
            "change_summary": "No auth header",
        },
    )
    assert res.status_code == 401


def test_empty_simulation_parameters_rejected(client: TestClient, topology_fixture):
    user_id, org_id, project, token, nodes = topology_fixture
    headers = {"Authorization": f"Bearer {token}", "X-Organization-ID": org_id}

    # Empty target component
    res_empty_target = client.post(
        f"/api/v1/projects/{project.id}/simulator/simulate",
        headers=headers,
        json={
            "project_id": project.id,
            "target_component": "   ",
            "change_summary": "Valid summary",
        },
    )
    assert res_empty_target.status_code == 400
    assert "cannot be empty" in res_empty_target.json()["detail"]

    # Empty change summary
    res_empty_summary = client.post(
        f"/api/v1/projects/{project.id}/simulator/simulate",
        headers=headers,
        json={
            "project_id": project.id,
            "target_component": "service:checkout",
            "change_summary": "   ",
        },
    )
    assert res_empty_summary.status_code == 400
    assert "cannot be empty" in res_empty_summary.json()["detail"]

