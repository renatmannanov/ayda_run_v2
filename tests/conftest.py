"""
Test fixtures for pytest
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from storage.db import Base, User, Activity, Club, Group, Membership, get_db
from api_server import app

# Test database (in-memory SQLite)
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="function")
def db_engine():
    """Create test database engine"""
    engine = create_engine(
        SQLALCHEMY_TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()

@pytest.fixture(scope="function")
def db_session(db_engine):
    """Create test database session"""
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=db_engine
    )
    session = TestingSessionLocal()
    yield session
    session.close()

@pytest.fixture
def client(db_session):
    """FastAPI test client with database override"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def test_user(db_session):
    """Create a test user"""
    from app_config.constants import DEFAULT_COUNTRY, DEFAULT_CITY
    user = User(
        telegram_id=12345,
        username="testuser",
        first_name="Test",
        country=DEFAULT_COUNTRY,
        city=DEFAULT_CITY,
        has_completed_onboarding=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def auth_headers():
    """Mock authentication headers for dev mode"""
    # Note: This assumes dev mode auth relies on this header or logic.
    # In Phase 1.2 we'll look at fixing auth bypass, but for now we follow the plan.
    return {"X-Telegram-Init-Data": "mock_dev_mode"}
