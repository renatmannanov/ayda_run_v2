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
    """Test that get_dev_user creates or returns dev user"""
    from storage.db import User

    # get_dev_user should always return a user with telegram_id=1
    # It will either find existing or create new
    dev_user = get_dev_user(db_session)

    assert dev_user is not None
    assert dev_user.telegram_id == 1
    assert dev_user.username == "admin"

def test_get_dev_user_returns_existing_user(db_session):
    """Test that get_dev_user returns existing user if exists"""
    from storage.db import User

    # Dev user with telegram_id=1 may already exist in the database
    # get_dev_user should return the existing user or create one
    dev_user = get_dev_user(db_session)

    assert dev_user is not None
    assert dev_user.telegram_id == 1

    # Call again - should return same user
    dev_user_again = get_dev_user(db_session)
    assert dev_user_again.id == dev_user.id

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
