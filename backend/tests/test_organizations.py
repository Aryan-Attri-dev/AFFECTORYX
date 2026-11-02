from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.organization import Organization
from app.models.membership import Membership, OrgRole
from app.models.audit import AuditLog


def test_create_and_list_organizations(client: TestClient, test_user_a):
    headers = {"Authorization": f"Bearer {test_user_a.access_token}"}
    
    # User A starts with 1 org ("Alpha Corp")
    res = client.get("/api/v1/organizations", headers=headers)
    assert res.status_code == 200
    orgs = res.json()
    assert len(orgs) == 1
    assert orgs[0]["name"] == "Alpha Corp"
    assert orgs[0]["user_role"] == "owner"

    # Create a second org
    create_res = client.post(
        "/api/v1/organizations",
        headers=headers,
        json={"name": "Alpha Cloud Labs", "description": "R&D division"},
    )
    assert create_res.status_code == 201
    created_org = create_res.json()
    assert created_org["name"] == "Alpha Cloud Labs"
    assert created_org["user_role"] == "owner"

    # Listing should now show 2 orgs
    list_res = client.get("/api/v1/organizations", headers=headers)
    assert list_res.status_code == 200
    assert len(list_res.json()) == 2


def test_organization_member_management(client: TestClient, test_user_a, test_user_b, db: Session):
    headers_a = {"Authorization": f"Bearer {test_user_a.access_token}"}
    org_id = test_user_a.active_organization_id

    # List members - initially only Alice
    members_res = client.get(
        f"/api/v1/organizations/{org_id}/members",
        headers={**headers_a, "X-Organization-ID": org_id},
    )
    assert members_res.status_code == 200
    members = members_res.json()
    assert len(members) == 1
    assert members[0]["email"] == "alice@company.com"

    # Alice adds Bob to Alpha Corp
    add_res = client.post(
        f"/api/v1/organizations/{org_id}/members",
        headers={**headers_a, "X-Organization-ID": org_id},
        json={"email": "bob@company.com", "role": "member"},
    )
    assert add_res.status_code == 201
    assert add_res.json()["email"] == "bob@company.com"
    assert add_res.json()["role"] == "member"

    # Bob updates his profile and now sees 2 orgs
    headers_b = {"Authorization": f"Bearer {test_user_b.access_token}"}
    bob_orgs = client.get("/api/v1/organizations", headers=headers_b).json()
    assert len(bob_orgs) == 2

    # Promote Bob to Admin
    update_role_res = client.patch(
        f"/api/v1/organizations/{org_id}/members/{test_user_b.user.id}",
        headers={**headers_a, "X-Organization-ID": org_id},
        json={"role": "admin"},
    )
    assert update_role_res.status_code == 200
    assert update_role_res.json()["role"] == "admin"

    # Verify audit logs generated for member addition and role change
    audit_res = client.get(
        f"/api/v1/organizations/{org_id}/audit-logs",
        headers={**headers_a, "X-Organization-ID": org_id},
    )
    assert audit_res.status_code == 200
    actions = [log["action"] for log in audit_res.json()]
    assert "member.add" in actions
    assert "member.role_update" in actions
