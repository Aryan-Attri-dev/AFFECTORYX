import json
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.graph import NodeType, EdgeType, EvidenceConfidence, EvidenceSourceKind
from app.models.project import Project
from app.services.project_service import ProjectService
from app.schemas.project import ProjectCreate

SAMPLE_OPENAPI_SPEC = {
    "openapi": "3.0.0",
    "info": {
        "title": "Payment Settlement API",
        "version": "2.4.0",
        "description": "Core payment settlement and ledger orchestration"
    },
    "paths": {
        "/api/v1/settlements": {
            "post": {
                "operationId": "create_settlement",
                "summary": "Initiate ledger settlement",
                "requestBody": {"content": {"application/json": {"schema": {"type": "object"}}}},
                "responses": {"201": {"description": "Settled successfully"}, "400": {"description": "Invalid"}}
            },
            "get": {
                "operationId": "list_settlements",
                "summary": "Query settlement ledger history",
                "responses": {"200": {"description": "List of settlements"}}
            }
        },
        "/api/v1/settlements/{id}": {
            "get": {
                "operationId": "get_settlement_by_id",
                "summary": "Fetch single settlement record",
                "parameters": [{"name": "id", "in": "path", "required": True}],
                "responses": {"200": {"description": "Record found"}}
            }
        }
    },
    "components": {
        "schemas": {
            "SettlementRequest": {"type": "object", "properties": {"amount": {"type": "number"}}},
            "SettlementResponse": {"type": "object", "properties": {"id": {"type": "string"}}}
        }
    }
}

SAMPLE_PYTHON_CODE = """
import requests
import httpx

def process_checkout(user_id, amount):
    # Confirmed static callsite
    resp = requests.post("http://billing-service/api/v1/settlements", json={"amount": amount})
    
    # Inferred template callsite
    audit_resp = requests.get(f"/api/v1/audit/users/{user_id}")
    
    # Dynamic unknown callsite - cannot determine target safely
    dynamic_url = get_custom_endpoint()
    httpx.get(dynamic_url)
    
    return resp.json()
"""

SAMPLE_SQL_MIGRATION = """
-- Migration V24: Schema updates for payments
CREATE TABLE accounts_ledger (
    id VARCHAR(36) PRIMARY KEY,
    balance NUMERIC(18, 4) NOT NULL
);

CREATE TABLE settlement_batches (
    batch_id VARCHAR(36) PRIMARY KEY,
    total_amount NUMERIC(18, 4) NOT NULL
);

-- Destructive breaking operations
ALTER TABLE legacy_transactions DROP COLUMN routing_code;
DROP TABLE deprecated_cache_entries;
"""


@pytest.fixture
def test_project(db: Session, test_user_a) -> Project:
    return ProjectService.create_project(
        db=db,
        organization_id=test_user_a.active_organization_id,
        data=ProjectCreate(
            name="Payments Platform",
            description="Enterprise payment orchestration",
            environments=["production", "staging"],
        ),
        actor=test_user_a.user,
    )


def test_openapi_ingestion_and_graph_topology(client: TestClient, test_user_a, test_project: Project):
    headers = {
        "Authorization": f"Bearer {test_user_a.access_token}",
        "X-Organization-ID": test_user_a.active_organization_id,
    }

    # 1. Ingest OpenAPI spec
    ingest_res = client.post(
        f"/api/v1/projects/{test_project.id}/ingest/openapi",
        headers=headers,
        json={
            "spec_source_name": "payments_v2.json",
            "spec_content": json.dumps(SAMPLE_OPENAPI_SPEC),
        },
    )
    assert ingest_res.status_code == 200
    summary = ingest_res.json()
    assert summary["title"] == "Payment Settlement API"
    assert summary["endpoints_discovered"] == 3
    assert summary["schemas_discovered"] == 2
    assert summary["edges_created"] == 3
    assert summary["evidence_records_created"] == 3

    # 2. Query Topology Graph
    graph_res = client.get(f"/api/v1/projects/{test_project.id}/graph", headers=headers)
    assert graph_res.status_code == 200
    topology = graph_res.json()

    assert topology["metrics"]["total_nodes"] == 4  # 1 service + 3 endpoints
    assert topology["metrics"]["services_count"] == 1
    assert topology["metrics"]["endpoints_count"] == 3
    assert topology["metrics"]["confirmed_edges"] == 3
    assert topology["metrics"]["unknown_edges"] == 0

    # 3. Query Evidence Registry
    evidence_res = client.get(
        f"/api/v1/projects/{test_project.id}/evidence?confidence=confirmed",
        headers=headers,
    )
    assert evidence_res.status_code == 200
    ev_records = evidence_res.json()
    assert len(ev_records) == 3
    assert ev_records[0]["source_kind"] == "openapi_spec"
    assert ev_records[0]["confidence"] == "confirmed"


def test_code_ast_scanner_and_unknown_safety(client: TestClient, test_user_a, test_project: Project):
    headers = {
        "Authorization": f"Bearer {test_user_a.access_token}",
        "X-Organization-ID": test_user_a.active_organization_id,
    }

    ast_res = client.post(
        f"/api/v1/projects/{test_project.id}/ingest/code",
        headers=headers,
        json={
            "caller_service_name": "CheckoutFrontend",
            "file_path": "services/checkout/orchestrator.py",
            "code_content": SAMPLE_PYTHON_CODE,
        },
    )
    assert ast_res.status_code == 200
    summary = ast_res.json()
    assert summary["callsites_discovered"] == 3
    assert summary["unknown_routes_flagged"] == 1  # Dynamic callsite flagged as unknown

    # Verify graph metrics show unknown edge
    graph_res = client.get(f"/api/v1/projects/{test_project.id}/graph", headers=headers)
    assert graph_res.status_code == 200
    metrics = graph_res.json()["metrics"]
    assert metrics["unknown_edges"] >= 1
    assert metrics["confirmed_edges"] >= 1


def test_sql_migration_ingestion(client: TestClient, test_user_a, test_project: Project):
    headers = {
        "Authorization": f"Bearer {test_user_a.access_token}",
        "X-Organization-ID": test_user_a.active_organization_id,
    }

    migration_res = client.post(
        f"/api/v1/projects/{test_project.id}/ingest/migration",
        headers=headers,
        json={
            "migration_filename": "V24__payments_tables.sql",
            "sql_content": SAMPLE_SQL_MIGRATION,
        },
    )
    assert migration_res.status_code == 200
    summary = migration_res.json()
    assert summary["tables_created"] == 2
    assert len(summary["destructive_operations"]) == 2
    assert any("DROP COLUMN routing_code" in op for op in summary["destructive_operations"])
    assert any("DROP TABLE deprecated_cache_entries" in op for op in summary["destructive_operations"])


def test_customer_mapping_and_impact_simulation(client: TestClient, test_user_a, test_project: Project):
    headers = {
        "Authorization": f"Bearer {test_user_a.access_token}",
        "X-Organization-ID": test_user_a.active_organization_id,
    }

    # Ingest OpenAPI spec first so endpoints exist
    client.post(
        f"/api/v1/projects/{test_project.id}/ingest/openapi",
        headers=headers,
        json={"spec_source_name": "spec.json", "spec_content": json.dumps(SAMPLE_OPENAPI_SPEC)},
    )

    # Ingest Customer Mapping
    cust_res = client.post(
        f"/api/v1/projects/{test_project.id}/customers",
        headers=headers,
        json={
            "customer_name": "Titan Global Bank",
            "tier": "tier-1",
            "contract_sla": "99.999%",
            "workflows": ["HighVolumePayouts", "DisputeSettlement"],
            "consumed_endpoints": ["POST /api/v1/settlements"],
        },
    )
    assert cust_res.status_code == 201
    cust_data = cust_res.json()
    assert cust_data["customer_name"] == "Titan Global Bank"
    assert cust_data["contract_sla"] == "99.999%"

    # Fetch topology to get node ID of POST /api/v1/settlements
    graph_res = client.get(f"/api/v1/projects/{test_project.id}/graph", headers=headers).json()
    endpoint_node = next(n for n in graph_res["nodes"] if n["identifier"] == "POST /api/v1/settlements")

    # Run Downstream Impact Simulation on that endpoint
    impact_res = client.get(
        f"/api/v1/projects/{test_project.id}/graph/impact?start_node_id={endpoint_node['id']}",
        headers=headers,
    )
    assert impact_res.status_code == 200
    impact = impact_res.json()
    assert impact["root_node_name"] == "POST /api/v1/settlements"
    # Verify that Titan Global Bank's customer workflows are in the blast radius!
    assert any("Titan Global Bank" in cust for cust in impact["impacted_customers"])
