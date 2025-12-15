"""
Tests for rate limiting
"""
import pytest
import time
from fastapi.testclient import TestClient
from api_server import app

def test_rate_limit_on_create_activity(client, monkeypatch):
    """Test that creating too many activities triggers rate limit"""
    # 1. Enable DEBUG mode to allow bypassing Telegram auth
    from auth import settings as auth_settings
    monkeypatch.setattr(auth_settings, "debug", True)

    from datetime import datetime, timedelta
    activity_data = {
        "title": "Test Activity",
        "date": (datetime.now() + timedelta(days=1)).isoformat(),
        "sport_type": "running", 
        "location": "Test Location",
        "difficulty": "easy"
    }

    # 2. Don't send auth headers (triggers dev mode)
    # Make requests up to limit (10/min)
    for i in range(10):
        response = client.post(
            "/api/activities",
            json=activity_data,
            # No headers
        )
        if response.status_code == 429:
             pytest.fail(f"Rate limited excessively early at request {i+1}")
        if response.status_code != 201:
             print(f"Request {i+1} failed: {response.status_code} {response.text}")
             
    # 11th request should be rate limited
    response = client.post(
        "/api/activities",
        json=activity_data
        # No headers
    )
    if response.status_code != 429:
        print(f"FAILED: Status {response.status_code}, Body: {response.json()}")
    assert response.status_code == 429
    data = response.json()
    assert "Too Many Requests" in data["error"]

def test_rate_limit_different_for_read_endpoints(client):
    """Test that read endpoints have different limits"""
    # Read endpoints have 100/min.
    # We just check we can do more than 10.
    for i in range(15):
        response = client.get("/api/activities")
        assert response.status_code != 429, f"Rate limited at request {i+1}"
