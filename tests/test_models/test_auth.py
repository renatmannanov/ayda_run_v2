"""
Tests for authentication logic
"""
import pytest
from fastapi import HTTPException
from unittest.mock import patch
from auth import get_current_user, get_dev_user, get_current_user_optional

def test_auth_rejects_missing_header_in_production(client, db_session, monkeypatch):
    """Test that missing auth header is rejected in production"""
    # Set production mode
    monkeypatch.setenv("DEBUG", "false")

    # Reload settings to pick up env change is trickier with simple monkeypatch on loaded module.
    # We should patch the settings object found in auth.
    from auth import settings as auth_settings
    monkeypatch.setattr(auth_settings, "debug", False)

    # Try to access protected endpoint without auth
    response = client.get("/api/users/me")
    assert response.status_code == 401
    assert "Authentication required" in response.json()["detail"]

def test_auth_allows_dev_mode_in_debug(client, db_session, monkeypatch):
    """Test that dev mode works when DEBUG=true"""
    # Set debug mode
    from auth import settings as auth_settings
    monkeypatch.setattr(auth_settings, "debug", True)

    # Access endpoint without auth should work
    response = client.get("/api/users/me")
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "admin"
    assert data["telegram_id"] == "1"  # telegram_id is serialized to string for JSON safety

def test_get_dev_user_creates_user_if_not_exists(db_session):
    """Test that get_dev_user creates user on first call"""
    from storage.db import User

    # Ensure no dev user exists
    db_session.query(User).filter(User.telegram_id == 1).delete()
    db_session.commit()

    # Get dev user should create it
    dev_user = get_dev_user(db_session)
    assert dev_user.telegram_id == 1
    assert dev_user.username == "admin"

    # Verify it's in database
    user_in_db = db_session.query(User).filter(User.telegram_id == 1).first()
    assert user_in_db is not None

def test_get_dev_user_returns_existing_user(db_session, test_user):
    """Test that get_dev_user returns existing user"""
    # Modify test_user to be dev user
    test_user.telegram_id = 1
    db_session.commit()

    # Get dev user should return existing
    dev_user = get_dev_user(db_session)
    assert dev_user.id == test_user.id

def test_optional_auth_returns_none_in_production_without_header(client, monkeypatch):
    """Test that optional auth returns None in production without header"""
    from auth import settings as auth_settings
    monkeypatch.setattr(auth_settings, "debug", False)

    # Endpoint that uses get_current_user_optional
    # GET /api/activities uses optional auth
    response = client.get("/api/activities") 
    assert response.status_code == 200
    # Should return data
    assert isinstance(response.json(), list)
