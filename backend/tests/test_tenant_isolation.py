from fastapi.testclient import TestClient


def test_strict_cross_tenant_isolation(client: TestClient, test_user_a, test_user_b):
    headers_a = {
        "Authorization": f"Bearer {test_user_a.access_token}",
        "X-Organization-ID": test_user_a.active_organization_id,
    }
    headers_b = {
        "Authorization": f"Bearer {test_user_b.access_token}",
        "X-Organization-ID": test_user_b.active_organization_id,
    }

    # User B creates a project in Beta Logistics
    b_project_res = client.post(
        "/api/v1/projects",
        headers=headers_b,
        json={
            "name": "Fleet Dispatch API",
            "description": "Beta Logistics route and delivery optimization service",
        },
    )
    assert b_project_res.status_code == 201
    b_project = b_project_res.json()
    b_project_id = b_project["id"]

    # 1. User A lists projects in Alpha Corp -> must NOT see Beta's project
    a_list_res = client.get("/api/v1/projects", headers=headers_a)
    assert a_list_res.status_code == 200
    project_ids = [p["id"] for p in a_list_res.json()]
    assert b_project_id not in project_ids

    # 2. User A attempts to directly fetch Beta's project using Alpha's org context -> 404
    a_fetch_res = client.get(f"/api/v1/projects/{b_project_id}", headers=headers_a)
    assert a_fetch_res.status_code == 404

    # 3. User A attempts to forge header X-Organization-ID to Beta's org ID -> 403 Access Denied
    forged_headers = {
        "Authorization": f"Bearer {test_user_a.access_token}",
        "X-Organization-ID": test_user_b.active_organization_id,
    }
    forged_res = client.get("/api/v1/projects", headers=forged_headers)
    assert forged_res.status_code == 403
    assert "User does not have access to this organization" in forged_res.json()["detail"]

    # 4. User A attempts to update Beta's project -> 404
    update_res = client.patch(
        f"/api/v1/projects/{b_project_id}",
        headers=headers_a,
        json={"name": "Hacked Name"},
    )
    assert update_res.status_code == 404

    # 5. User A attempts to delete Beta's project -> 404
    delete_res = client.delete(f"/api/v1/projects/{b_project_id}", headers=headers_a)
    assert delete_res.status_code == 404

    # 6. User A attempts to read Beta's audit logs -> 403 Forbidden
    audit_res = client.get(
        f"/api/v1/organizations/{test_user_b.active_organization_id}/audit-logs",
        headers={
            "Authorization": f"Bearer {test_user_a.access_token}",
            "X-Organization-ID": test_user_b.active_organization_id,
        },
    )
    assert audit_res.status_code == 403
