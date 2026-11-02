from fastapi.testclient import TestClient


def test_create_and_manage_project(client: TestClient, test_user_a):
    headers = {
        "Authorization": f"Bearer {test_user_a.access_token}",
        "X-Organization-ID": test_user_a.active_organization_id,
    }

    # Initially 0 projects
    list_res = client.get("/api/v1/projects", headers=headers)
    assert list_res.status_code == 200
    assert list_res.json() == []

    # Create project
    create_res = client.post(
        "/api/v1/projects",
        headers=headers,
        json={
            "name": "Billing Service Engine",
            "description": "Core subscription and invoice settlement microservice",
            "repository_url": "https://github.com/alpha-corp/billing-service",
            "default_branch": "main",
            "environments": ["production", "staging", "qa"],
        },
    )
    assert create_res.status_code == 201
    project = create_res.json()
    assert project["name"] == "Billing Service Engine"
    assert project["slug"] == "billing-service-engine"
    assert project["organization_id"] == test_user_a.active_organization_id
    project_id = project["id"]

    # Get by ID
    get_res = client.get(f"/api/v1/projects/{project_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["slug"] == "billing-service-engine"

    # Get by Slug
    get_slug_res = client.get("/api/v1/projects/billing-service-engine", headers=headers)
    assert get_slug_res.status_code == 200

    # Update project
    update_res = client.patch(
        f"/api/v1/projects/{project_id}",
        headers=headers,
        json={"description": "Updated mission-critical billing infrastructure"},
    )
    assert update_res.status_code == 200
    assert update_res.json()["description"] == "Updated mission-critical billing infrastructure"

    # Delete project
    delete_res = client.delete(f"/api/v1/projects/{project_id}", headers=headers)
    assert delete_res.status_code == 204

    # Verify not found after deletion
    verify_res = client.get(f"/api/v1/projects/{project_id}", headers=headers)
    assert verify_res.status_code == 404
