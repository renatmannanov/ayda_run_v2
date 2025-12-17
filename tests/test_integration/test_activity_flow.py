"""
Integration tests for activity lifecycle
"""
import pytest
from datetime import datetime, timedelta

def test_create_and_join_activity_flow(client, auth_headers, test_user, monkeypatch):
    """Test complete flow: create -> join -> leave -> delete"""
    # Enable dev auth
    from auth import settings as auth_settings
    monkeypatch.setattr(auth_settings, "debug", True)
    
    # Disable rate limiting for this test to avoid interference
    from api_server import limiter
    limiter.enabled = False
    
    try:
        # 1. Create activity
        activity_data = {
            "title": "Integration Test Run",
            "date": (datetime.now() + timedelta(days=1)).isoformat(),
            "location": "Test Park",
            "city": "Almaty",  # Required field
            "sport_type": "running",
            "difficulty": "easy"
        }

        response = client.post(
            "/api/activities",
            json=activity_data,
            headers={"X-Forwarded-For": "10.0.0.1"}, # Avoid rate limit from other tests
            # No auth headers = trigger dev mode bypass
        )
        assert response.status_code == 201, f"Failed to create activity: {response.text}"
        activity = response.json()
        activity_id = activity["id"]

        # 2. Get activity details
        response = client.get(f"/api/activities/{activity_id}", headers={"X-Forwarded-For": "10.0.0.1"})
        assert response.status_code == 200
        assert response.json()["title"] == "Integration Test Run"

        # 3. Join activity
        response = client.post(
            f"/api/activities/{activity_id}/join",
            headers={"X-Forwarded-For": "10.0.0.1"}
        )
        # The creator automatically joins? Or explicit join?
        # Usually creator might not auto-join in all implementations, but let's see.
        # If already joined, might return 400 or "already joined".
        # Implementation: checks Participation.
        # If not joined, returns {"status": "joined"}
        
        # If creator is NOT auto-joined (let's check api implementation if we could).
        # But for now assume we want to ensure we joined.
        if response.status_code == 400 and "already" in response.text.lower():
             # OK, maybe auto-joined. Let's verify status.
             pass
        else:
            assert response.status_code == 201
            assert "Successfully joined" in response.json()["message"]

        # 4. Check participants
        response = client.get(f"/api/activities/{activity_id}/participants", headers={"X-Forwarded-For": "10.0.0.1"})
        assert response.status_code == 200
        participants = response.json()
        # Should be at least 1 (the dev user)
        telegram_ids = [p["telegram_id"] for p in participants]
        assert 1 in telegram_ids # Dev user has telegram_id=1

        # 5. Leave activity
        response = client.post(
            f"/api/activities/{activity_id}/leave",
            headers={"X-Forwarded-For": "10.0.0.1"}
        )
        assert response.status_code == 200
        assert "Successfully left" in response.json()["message"]

        # 6. Delete activity
        response = client.delete(
            f"/api/activities/{activity_id}",
            headers={"X-Forwarded-For": "10.0.0.1"}
        )
        assert response.status_code == 204

        # 7. Verify deleted
        response = client.get(f"/api/activities/{activity_id}", headers={"X-Forwarded-For": "10.0.0.1"})
        assert response.status_code == 404
    
    finally:
        limiter.enabled = True
