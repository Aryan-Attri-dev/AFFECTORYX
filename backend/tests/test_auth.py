from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.membership import Membership, OrgRole


def test_register_success(client: TestClient, db: Session):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "carol@enterprise.io",
            "password": "SecurePassword9988!",
            "full_name": "Carol Danvers",
            "organization_name": "Carol Industries",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "carol@enterprise.io"
    assert len(data["user"]["memberships"]) == 1
    assert data["user"]["memberships"][0]["organization_name"] == "Carol Industries"
    assert data["user"]["memberships"][0]["role"] == "owner"
    assert data["active_organization_id"] is not None

    # Verify user in database
    user = db.query(User).filter(User.email == "carol@enterprise.io").first()
    assert user is not None
    assert user.full_name == "Carol Danvers"


def test_register_duplicate_email(client: TestClient, test_user_a):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "alice@company.com",
            "password": "AnotherPassword123!",
            "full_name": "Alice Duplicate",
        },
    )
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_login_success(client: TestClient, test_user_a):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "alice@company.com",
            "password": "StrongPassword123!",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "alice@company.com"


def test_login_invalid_password(client: TestClient, test_user_a):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "alice@company.com",
            "password": "WrongPassword!",
        },
    )
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]


def test_login_nonexistent_user(client: TestClient):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "nobody@nowhere.com",
            "password": "SomePassword!",
        },
    )
    assert response.status_code == 401


def test_get_current_user_profile(client: TestClient, test_user_a):
    headers = {"Authorization": f"Bearer {test_user_a.access_token}"}
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "alice@company.com"
    assert data["full_name"] == "Alice Architect"
    assert len(data["memberships"]) == 1


def test_unauthenticated_request_rejected(client: TestClient):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
