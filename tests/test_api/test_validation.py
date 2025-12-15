"""
Tests for input validation defined in schemas
"""
import pytest
from datetime import datetime, timedelta
from api_server import app

def test_activity_validation_rejects_past_date(client, monkeypatch):
    """Test that past date is rejected"""
    # Enable debug auth
    from auth import settings as auth_settings
    monkeypatch.setattr(auth_settings, "debug", True)

    data = {
        "title": "Test",
        "date": (datetime.now() - timedelta(days=1)).isoformat(),
        "location": "Test",
        "sport_type": "running",
        "difficulty": "easy"
    }

    response = client.post("/api/activities", json=data)
    # Pydantic validation error is 422
    assert response.status_code == 422
    assert "future" in str(response.json())

def test_activity_validation_rejects_invalid_sport_type(client, monkeypatch):
    """Test that invalid sport type is rejected"""
    from auth import settings as auth_settings
    monkeypatch.setattr(auth_settings, "debug", True)

    data = {
        "title": "Test",
        "date": (datetime.now() + timedelta(days=1)).isoformat(),
        "location": "Test",
        "sport_type": "invalid_sport",
        "difficulty": "easy"
    }

    response = client.post("/api/activities", json=data)
    assert response.status_code == 422
    assert "Input should be" in str(response.json()) # Pydantic v2 error message usually

def test_activity_validation_title_too_short(client, monkeypatch):
    """Test that short title is rejected"""
    from auth import settings as auth_settings
    monkeypatch.setattr(auth_settings, "debug", True)

    data = {
        "title": "AB", # too short
        "date": (datetime.now() + timedelta(days=1)).isoformat(),
        "location": "Test",
        "sport_type": "running",
        "difficulty": "easy"
    }

    response = client.post("/api/activities", json=data)
    assert response.status_code == 422
    assert "String should have at least 3 characters" in str(response.json())

def test_club_validation_rejects_negative_price(client, monkeypatch):
    """Test that negative price is rejected"""
    from auth import settings as auth_settings
    monkeypatch.setattr(auth_settings, "debug", True)

    data = {
        "name": "Test Club",
        "is_paid": True,
        "price_per_activity": -100
    }

    response = client.post("/api/clubs", json=data)
    assert response.status_code == 422
    assert "Input should be greater than or equal to 0" in str(response.json())
