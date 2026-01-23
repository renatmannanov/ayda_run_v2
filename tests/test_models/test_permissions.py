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
    db_session.flush()

    # Create ADMIN membership
    membership = Membership(
        user_id=test_user.id,
        club_id=club.id,
        role=UserRole.ADMIN
    )
    db_session.add(membership)
    db_session.flush()

    # Test
    assert can_manage_club(db_session, test_user, club.id) == True

def test_member_cannot_manage_club(db_session, test_user):
    """Test that MEMBER role cannot manage club"""
    from app_config.constants import DEFAULT_CITY, DEFAULT_COUNTRY

    # Create another user to be club owner
    other_user = User(
        telegram_id=999999,
        username="otheruser",
        first_name="Other",
        country=DEFAULT_COUNTRY,
        city=DEFAULT_CITY
    )
    db_session.add(other_user)
    db_session.flush()

    # Create club owned by other user
    club = Club(name="Test Club", city=DEFAULT_CITY, creator_id=other_user.id)
    db_session.add(club)
    db_session.flush()

    # MEMBER membership for test_user
    membership = Membership(
        user_id=test_user.id,
        club_id=club.id,
        role=UserRole.MEMBER
    )
    db_session.add(membership)
    db_session.flush()

    # Test
    assert can_manage_club(db_session, test_user, club.id) == False

def test_non_member_cannot_manage_club(db_session, test_user):
    """Test that non-member cannot manage club"""
    from app_config.constants import DEFAULT_CITY, DEFAULT_COUNTRY

    # Create another user to be club owner
    other_user = User(
        telegram_id=888888,
        username="anotheruser",
        first_name="Another",
        country=DEFAULT_COUNTRY,
        city=DEFAULT_CITY
    )
    db_session.add(other_user)
    db_session.flush()

    # Create club owned by other user
    club = Club(name="Test Club", city=DEFAULT_CITY, creator_id=other_user.id)
    db_session.add(club)
    db_session.flush()

    # No membership for test_user
    assert can_manage_club(db_session, test_user, club.id) == False
