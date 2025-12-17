"""
Tests for permissions logic
"""
import pytest
from storage.db import User, Club, Group, Membership, UserRole
from permissions import (
    can_manage_club,
)

def test_admin_can_manage_any_club(db_session, test_user):
    """Test that ADMIN role can manage any club"""
    from app_config.constants import DEFAULT_CITY
    # Create club
    club = Club(name="Test Club", city=DEFAULT_CITY, creator_id=test_user.id)
    db_session.add(club)
    db_session.commit()

    # Create ADMIN membership
    membership = Membership(
        user_id=test_user.id,
        club_id=club.id,
        role=UserRole.ADMIN
    )
    db_session.add(membership)
    db_session.commit()

    # Test
    assert can_manage_club(db_session, test_user, club.id) == True

def test_member_cannot_manage_club(db_session, test_user):
    """Test that MEMBER role cannot manage club"""
    from app_config.constants import DEFAULT_CITY
    # Create club owned by someone else
    club = Club(name="Test Club", city=DEFAULT_CITY, creator_id=999) # Assuming 999 doesn't exist
    db_session.add(club)
    db_session.commit()

    # MEMBER membership
    membership = Membership(
        user_id=test_user.id,
        club_id=club.id,
        role=UserRole.MEMBER
    )
    db_session.add(membership)
    db_session.commit()

    # Test
    assert can_manage_club(db_session, test_user, club.id) == False

def test_non_member_cannot_manage_club(db_session, test_user):
    """Test that non-member cannot manage club"""
    from app_config.constants import DEFAULT_CITY
    club = Club(name="Test Club", city=DEFAULT_CITY, creator_id=999)
    db_session.add(club)
    db_session.commit()

    # No membership
    assert can_manage_club(db_session, test_user, club.id) == False
