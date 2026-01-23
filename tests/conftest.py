"""
Test fixtures for pytest

Uses the same PostgreSQL database as the application with transaction rollback
for test isolation. Each test runs in a transaction that is rolled back after
the test completes, ensuring no test data persists.
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session

import storage.db as db_module
from storage.db import Base, User, Activity, Club, Group, Membership, get_db, engine
from api_server import app


@pytest.fixture(scope="function")
def db_connection():
    """
    Create a database connection with a transaction for test isolation.

    Uses the application's PostgreSQL database but wraps each test in a
    transaction that gets rolled back, so no test data persists.
    """
    connection = engine.connect()
    transaction = connection.begin()

    yield connection

    # Rollback the transaction after test
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def db_session(db_connection):
    """
    Create a test database session bound to the transaction.

    All operations in this session will be rolled back after the test.
    """
    # Create a session bound to the connection (within the transaction)
    session = Session(bind=db_connection)

    yield session

    session.close()


@pytest.fixture(scope="function")
def db_engine(db_connection):
    """
    Provide db_engine fixture for backward compatibility.

    Returns the connection which can be used as a bind for sessionmaker.
    """
    yield db_connection


@pytest.fixture
def client(db_session):
    """
    FastAPI test client with database override.

    Overrides get_db dependency to use the test session (within transaction).
    Also patches SessionLocal for Storage classes that create their own sessions.
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    # Override FastAPI dependency
    app.dependency_overrides[get_db] = override_get_db

    # Store original SessionLocal
    original_session_local = db_module.SessionLocal

    # Create a mock that returns our test session
    def mock_session_local():
        return db_session

    # Patch at module level
    db_module.SessionLocal = mock_session_local

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        # Restore original
        db_module.SessionLocal = original_session_local
        app.dependency_overrides.clear()


@pytest.fixture
def db_session_bot(db_session):
    """
    Alias for db_session, used by bot tests.

    Provides the same transactional session for bot handler tests.
    """
    return db_session


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
    db_session.flush()  # Use flush instead of commit to stay in transaction
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers():
    """Mock authentication headers for dev mode"""
    return {"X-Telegram-Init-Data": "mock_dev_mode"}
