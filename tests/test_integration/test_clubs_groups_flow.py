import pytest
from auth import settings as auth_settings
from api_server import limiter

def test_club_flow(client, monkeypatch):
    """
    Test the full lifecycle of a Club:
    1. Create Club
    2. Verify initial state (groups_count=0)
    3. Create Group in Club
    4. Verify updated state (groups_count=1)
    5. List Clubs
    """
    # Enable dev auth
    monkeypatch.setattr(auth_settings, "debug", True)
    limiter.enabled = False

    try:
        # 1. Create Club
        club_data = {
            "name": "Integration Test Club",
            "description": "A club for testing integration flow",
            "is_paid": False
        }
        # No headers = trigger dev mode
        response = client.post("/api/clubs", json=club_data)
        assert response.status_code == 201, f"Create Club failed: {response.text}"
        club = response.json()
        club_id = club["id"]
        
        # Verify fields that were missing before correction
        assert "groups_count" in club
        assert club["groups_count"] == 0
        assert club["members_count"] == 1  # Creator is autocommitted as member

        # 2. List Clubs and find our club
        response = client.get("/api/clubs")
        assert response.status_code == 200
        clubs = response.json()
        assert any(c["id"] == club_id for c in clubs)
        
        # 3. Create Group linked to Club
        group_data = {
            "name": "Club Runner Group",
            "description": "Group inside club",
            "club_id": club_id
        }
        response = client.post("/api/groups", json=group_data)
        assert response.status_code == 201, f"Create Group failed: {response.text}"
        group = response.json()
        group_id = group["id"]
        
        # Verify linking
        assert group["club_id"] == club_id

        # 4. Get Club Details - verify groups_count updated
        response = client.get(f"/api/clubs/{club_id}")
        assert response.status_code == 200
        updated_club = response.json()
        assert updated_club["groups_count"] == 1
    
    finally:
        limiter.enabled = True

def test_standalone_group_flow(client, monkeypatch):
    """
    Test standalone Group lifecycle:
    1. Create Group (no club)
    2. List Groups
    3. Verify fields (club_name, user_role) that caused 500s
    """
    # Enable dev auth
    monkeypatch.setattr(auth_settings, "debug", True)
    limiter.enabled = False

    try:
        # 1. Create Standalone Group
        group_data = {
            "name": "Standalone Runners",
            "description": "Just running, no club"
        }
        response = client.post("/api/groups", json=group_data)
        assert response.status_code == 201
        group = response.json()
        group_id = group["id"]
        
        assert group["club_id"] is None
        # Verify this field exists (was missing)
        assert "user_role" in group
        assert group["user_role"] == "admin" # Standalone creator should be admin

        # 2. List Groups
        response = client.get("/api/groups")
        assert response.status_code == 200
        groups = response.json()
        target_group = next((g for g in groups if g["id"] == group_id), None)
        
        assert target_group is not None
        assert target_group["club_name"] is None
        assert target_group["user_role"] == "admin"
    
    finally:
        limiter.enabled = True
