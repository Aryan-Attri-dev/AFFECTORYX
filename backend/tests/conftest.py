import os
import pytest
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

os.environ["ENVIRONMENT"] = "test"
os.environ["SECRET_KEY"] = "test-encryption-key-for-testing-affactoryx-long-32chars"

from app.core.database import Base, get_db
from app.main import app
from app.services.auth_service import AuthService
from app.schemas.auth import RegisterRequest

TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db: Session) -> Generator[TestClient, None, None]:
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def test_user_a(db: Session):
    return AuthService.register(
        db=db,
        data=RegisterRequest(
            email="alice@company.com",
            full_name="Alice Architect",
            password="StrongPassword123!",
            organization_name="Alpha Corp",
        ),
    )


@pytest.fixture
def test_user_b(db: Session):
    return AuthService.register(
        db=db,
        data=RegisterRequest(
            email="bob@company.com",
            full_name="Bob Builder",
            password="StrongPassword123!",
            organization_name="Beta Logistics",
        ),
    )
