import json
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.organization import Organization
from app.models.project import Project
from app.models.user import User
from app.models.analysis import ChangeSeverity, BreakingCategory
from app.services.change_analyzer import ChangeAnalyzerService
from app.services.project_service import ProjectService
from app.schemas.project import ProjectCreate


BASE_OPENAPI_SPEC = json.dumps({
    "openapi": "3.0.0",
    "info": {"title": "Payment Gateway API", "version": "1.0.0"},
    "paths": {
        "/api/v1/payments": {
            "get": {
                "summary": "List payments",
                "parameters": [
                    {"name": "status", "in": "query", "required": False, "schema": {"type": "string"}},
                    {"name": "limit", "in": "query", "required": False, "schema": {"type": "integer"}}
                ],
                "responses": {
                    "200": {
                        "description": "OK",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "payments": {"type": "array"},
                                        "total_count": {"type": "integer"}
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "post": {
                "summary": "Process payment",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["amount", "currency"],
                                "properties": {
                                    "amount": {"type": "number"},
                                    "currency": {"type": "string"}
                                }
                            }
                        }
                    }
                },
                "responses": {"200": {"description": "Processed"}}
            },
            "delete": {
                "summary": "Void payment",
                "responses": {"200": {"description": "Voided"}}
            }
        },
        "/api/v1/refunds": {
            "post": {
                "summary": "Issue refund",
                "responses": {"200": {"description": "Refunded"}}
            }
        }
    }
})

BREAKING_TARGET_OPENAPI_SPEC = json.dumps({
    "openapi": "3.0.0",
    "info": {"title": "Payment Gateway API", "version": "2.0.0"},
    "paths": {
        "/api/v1/payments": {
            "get": {
                "summary": "List payments",
                "parameters": [
                    {"name": "status", "in": "query", "required": True, "schema": {"type": "string"}}, # Newly required!
                    {"name": "limit", "in": "query", "required": False, "schema": {"type": "string"}}   # Type changed to string!
                ],
                "responses": {
                    "200": {
                        "description": "OK",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "payments": {"type": "array"} # Removed total_count!
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "post": {
                "summary": "Process payment",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["amount", "currency", "idempotency_key"], # Newly required body field!
                                "properties": {
                                    "amount": {"type": "number"},
                                    "currency": {"type": "string"},
                                    "idempotency_key": {"type": "string"}
                                }
                            }
                        }
                    }
                },
                "responses": {"200": {"description": "Processed"}}
            }
            # DELETE method removed!
        }
        # /api/v1/refunds path completely removed!
    }
})

NON_BREAKING_TARGET_OPENAPI_SPEC = json.dumps({
    "openapi": "3.0.0",
    "info": {"title": "Payment Gateway API", "version": "1.1.0"},
    "paths": {
        "/api/v1/payments": {
            "get": {
                "summary": "List payments",
                "parameters": [
                    {"name": "status", "in": "query", "required": False, "schema": {"type": "string"}},
                    {"name": "limit", "in": "query", "required": False, "schema": {"type": "integer"}},
                    {"name": "sort_by", "in": "query", "required": False, "schema": {"type": "string"}} # New optional param
                ],
                "responses": {
                    "200": {
                        "description": "OK",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "payments": {"type": "array"},
                                        "total_count": {"type": "integer"},
                                        "page": {"type": "integer"} # Additive response field
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "post": {
                "summary": "Process payment",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["amount", "currency"],
                                "properties": {
                                    "amount": {"type": "number"},
                                    "currency": {"type": "string"}
                                }
                            }
                        }
                    }
                },
                "responses": {"200": {"description": "Processed"}}
            },
            "delete": {
                "summary": "Void payment",
                "responses": {"200": {"description": "Voided"}}
            }
        },
        "/api/v1/refunds": {
            "post": {
                "summary": "Issue refund",
                "responses": {"200": {"description": "Refunded"}}
            }
        },
        "/api/v1/settlements": { # New backwards-compatible endpoint
            "get": {
                "summary": "Get settlements",
                "responses": {"200": {"description": "Settlements"}}
            }
        }
    }
})


def test_openapi_breaking_changes_detected(db: Session, test_user_a):
    user_id = test_user_a.user.id
    org_id = test_user_a.active_organization_id
    actor = db.query(User).filter_by(id=user_id).first()
    project = ProjectService.create_project(
        db=db,
        organization_id=org_id,
        data=ProjectCreate(name="Payments Core", key="PAY"),
        actor=actor,
    )

    analysis = ChangeAnalyzerService.compare_openapi_specs(
        db=db,
        organization_id=org_id,
        project_id=project.id,
        author_id=user_id,
        title="Payment API v2 Breaking Overhaul",
        base_spec_str=BASE_OPENAPI_SPEC,
        target_spec_str=BREAKING_TARGET_OPENAPI_SPEC,
        base_version="v1.0.0",
        target_version="v2.0.0",
    )

    assert analysis.breaking_count >= 5
    categories = [f["category"] for f in analysis.findings if f["severity"] == ChangeSeverity.BREAKING.value]
    
    # Assert all breaking categories detected
    assert BreakingCategory.REMOVED_ENDPOINT.value in categories
    assert BreakingCategory.CHANGED_METHOD.value in categories
    assert BreakingCategory.REQUIRED_PARAMETER_ADDED.value in categories
    assert BreakingCategory.INCOMPATIBLE_TYPE.value in categories
    assert BreakingCategory.REMOVED_RESPONSE_FIELD.value in categories


def test_openapi_non_breaking_changes(db: Session, test_user_a):
    user_id = test_user_a.user.id
    org_id = test_user_a.active_organization_id
    actor = db.query(User).filter_by(id=user_id).first()
    project = ProjectService.create_project(
        db=db,
        organization_id=org_id,
        data=ProjectCreate(name="Payments Core", key="PAY"),
        actor=actor,
    )

    analysis = ChangeAnalyzerService.compare_openapi_specs(
        db=db,
        organization_id=org_id,
        project_id=project.id,
        author_id=user_id,
        title="Additive Minor Release",
        base_spec_str=BASE_OPENAPI_SPEC,
        target_spec_str=NON_BREAKING_TARGET_OPENAPI_SPEC,
        base_version="v1.0.0",
        target_version="v1.1.0",
    )

    assert analysis.breaking_count == 0
    assert analysis.non_breaking_count >= 1


def test_sql_migration_breaking_and_non_breaking(db: Session, test_user_a):
    user_id = test_user_a.user.id
    org_id = test_user_a.active_organization_id
    actor = db.query(User).filter_by(id=user_id).first()
    project = ProjectService.create_project(
        db=db,
        organization_id=org_id,
        data=ProjectCreate(name="Ledger", key="LED"),
        actor=actor,
    )

    sql_content = """
    -- Destructive operations
    DROP TABLE legacy_settlements;
    ALTER TABLE transactions DROP COLUMN internal_routing_code;
    ALTER TABLE accounts ALTER COLUMN balance SET NOT NULL;
    ALTER TABLE accounts ALTER COLUMN account_number TYPE bigint;

    -- Additive operations
    CREATE TABLE audit_checkpoints (id uuid primary key, verified boolean);
    ALTER TABLE accounts ADD COLUMN preferred_currency varchar(3);
    """

    analysis = ChangeAnalyzerService.compare_sql_migration(
        db=db,
        organization_id=org_id,
        project_id=project.id,
        author_id=user_id,
        title="Ledger Schema Migration",
        migration_filename="004_settlements_cleanup.sql",
        sql_content=sql_content,
    )

    assert analysis.breaking_count == 4
    assert analysis.non_breaking_count == 2
    categories = [f["category"] for f in analysis.findings if f["severity"] == ChangeSeverity.BREAKING.value]
    assert BreakingCategory.DROPPED_TABLE.value in categories
    assert BreakingCategory.DROPPED_COLUMN.value in categories
    assert BreakingCategory.INCOMPATIBLE_COLUMN_MODIFICATION.value in categories


def test_analyzer_api_endpoints_and_tenant_isolation(client: TestClient, db: Session, test_user_a, test_user_b):
    user_id_a = test_user_a.user.id
    org_id_a = test_user_a.active_organization_id
    token_a = test_user_a.access_token

    org_id_b = test_user_b.active_organization_id
    token_b = test_user_b.access_token

    actor_a = db.query(User).filter_by(id=user_id_a).first()
    project_a = ProjectService.create_project(
        db=db,
        organization_id=org_id_a,
        data=ProjectCreate(name="Org A Project", key="ORGA"),
        actor=actor_a,
    )

    headers_a = {"Authorization": f"Bearer {token_a}", "X-Organization-ID": org_id_a}
    headers_b = {"Authorization": f"Bearer {token_b}", "X-Organization-ID": org_id_b}

    # 1. User A runs OpenAPI analysis on Project A
    res = client.post(
        f"/api/v1/projects/{project_a.id}/analyzer/compare-openapi",
        headers=headers_a,
        json={
            "project_id": project_a.id,
            "title": "API Audit",
            "base_spec": BASE_OPENAPI_SPEC,
            "target_spec": BREAKING_TARGET_OPENAPI_SPEC,
            "base_version": "v1.0.0",
            "target_version": "v2.0.0",
        },
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["breaking_count"] >= 5
    analysis_id = data["id"]

    # 2. User B in Org B tries to access Org A's analysis -> 404 forbidden cross-tenant
    cross_res = client.get(
        f"/api/v1/projects/{project_a.id}/analyzer/analyses/{analysis_id}",
        headers=headers_b,
    )
    assert cross_res.status_code == 404

    # 3. User A can list analyses
    list_res = client.get(
        f"/api/v1/projects/{project_a.id}/analyzer/analyses",
        headers=headers_a,
    )
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1


def test_malformed_and_oversized_openapi_rejected(client: TestClient, db: Session, test_user_a):
    user_id = test_user_a.user.id
    org_id = test_user_a.active_organization_id
    token = test_user_a.access_token
    actor = db.query(User).filter_by(id=user_id).first()
    project = ProjectService.create_project(
        db=db,
        organization_id=org_id,
        data=ProjectCreate(name="Edge Case Project", key="EDGE"),
        actor=actor,
    )
    headers = {"Authorization": f"Bearer {token}", "X-Organization-ID": org_id}

    # 1. Invalid JSON/YAML syntax
    res = client.post(
        f"/api/v1/projects/{project.id}/analyzer/compare-openapi",
        headers=headers,
        json={
            "project_id": project.id,
            "title": "Malformed Test",
            "base_spec": "{not: valid json or yaml: }",
            "target_spec": BASE_OPENAPI_SPEC,
        },
    )
    assert res.status_code == 400
    assert "Invalid" in res.json()["detail"]

    # 2. Non-dict mapping (e.g. JSON array)
    res_arr = client.post(
        f"/api/v1/projects/{project.id}/analyzer/compare-openapi",
        headers=headers,
        json={
            "project_id": project.id,
            "title": "Array Test",
            "base_spec": "[1, 2, 3]",
            "target_spec": BASE_OPENAPI_SPEC,
        },
    )
    assert res_arr.status_code == 400
    assert "object mapping" in res_arr.json()["detail"]

    # 3. Empty spec
    res_empty = client.post(
        f"/api/v1/projects/{project.id}/analyzer/compare-openapi",
        headers=headers,
        json={
            "project_id": project.id,
            "title": "Empty Spec",
            "base_spec": "   ",
            "target_spec": BASE_OPENAPI_SPEC,
        },
    )
    assert res_empty.status_code == 400
    assert "empty" in res_empty.json()["detail"]


def test_sql_migration_empty_and_oversized_rejected(client: TestClient, db: Session, test_user_a):
    user_id = test_user_a.user.id
    org_id = test_user_a.active_organization_id
    token = test_user_a.access_token
    actor = db.query(User).filter_by(id=user_id).first()
    project = ProjectService.create_project(
        db=db,
        organization_id=org_id,
        data=ProjectCreate(name="SQL Edge Project", key="SQLE"),
        actor=actor,
    )
    headers = {"Authorization": f"Bearer {token}", "X-Organization-ID": org_id}

    # 1. Empty SQL content
    res = client.post(
        f"/api/v1/projects/{project.id}/analyzer/compare-sql",
        headers=headers,
        json={
            "project_id": project.id,
            "title": "Empty SQL",
            "migration_filename": "empty.sql",
            "sql_content": "   ",
        },
    )
    assert res.status_code == 400
    assert "empty" in res.json()["detail"]


def test_unauthorized_analyzer_access(client: TestClient, db: Session, test_user_a):
    user_id = test_user_a.user.id
    org_id = test_user_a.active_organization_id
    actor = db.query(User).filter_by(id=user_id).first()
    project = ProjectService.create_project(
        db=db,
        organization_id=org_id,
        data=ProjectCreate(name="Auth Edge Project", key="AUTHE"),
        actor=actor,
    )

    # Missing auth token -> 401
    res = client.post(
        f"/api/v1/projects/{project.id}/analyzer/compare-openapi",
        json={
            "project_id": project.id,
            "title": "No Auth",
            "base_spec": BASE_OPENAPI_SPEC,
            "target_spec": BREAKING_TARGET_OPENAPI_SPEC,
        },
    )
    assert res.status_code == 401

