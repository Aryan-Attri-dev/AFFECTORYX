import pytest
from fastapi.testclient import TestClient
from app.core.config import Settings


def test_security_headers_present(client: TestClient):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.headers.get("X-Content-Type-Options") == "nosniff"
    assert res.headers.get("X-Frame-Options") == "DENY"
    assert res.headers.get("X-XSS-Protection") == "1; mode=block"
    assert "Strict-Transport-Security" in res.headers
    assert res.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"


def test_settings_repr_masks_confidential_values():
    s = Settings(
        SECRET_KEY="placeholder-test-secret-key-not-leaked-32chars",
        FIRST_SUPERUSER_PASSWORD="ConfidentialMasterPassword123!",
    )
    repr_str = repr(s)
    assert "placeholder-test-secret-key-not-leaked-32chars" not in repr_str
    assert "ConfidentialMasterPassword123!" not in repr_str


def test_production_environment_rejects_insecure_key():
    with pytest.raises(ValueError, match="SECURITY ERROR"):
        Settings(
            ENVIRONMENT="production",
            SECRET_KEY="placeholder-dev-insecure-eval-key",
            DATABASE_URL="postgresql://placeholder_user:placeholder_pass@db:5432/test_db",
        )


def test_production_environment_rejects_sqlite():
    with pytest.raises(ValueError, match="Production environment cannot use SQLite"):
        Settings(
            ENVIRONMENT="production",
            SECRET_KEY="a" * 35,  # long enough but sqlite db
            DATABASE_URL="sqlite:///./prod.db",
        )
