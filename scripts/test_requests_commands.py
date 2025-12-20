"""
Test script for /requests and /my_requests commands

This script tests the join request management commands.
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from storage.db import SessionLocal, User, Club, Group, JoinRequest, JoinRequestStatus, Membership, UserRole
from storage.join_request_storage import JoinRequestStorage
from datetime import datetime, timezone


def create_test_data():
    """Create test data for requests commands"""
    session = SessionLocal()

    try:
        # Create test users
        admin_user = User(
            id="admin-test-001",
            telegram_id=123456789,
            first_name="Admin",
            last_name="Testov",
            username="admin_test",
            preferred_sports='["running"]',
            has_completed_onboarding=True
        )

        requester_user = User(
            id="requester-test-001",
            telegram_id=987654321,
            first_name="Ivan",
            last_name="Petrov",
            username="ivan_p",
            preferred_sports='["running", "trail"]',
            has_completed_onboarding=True
        )

        requester_user2 = User(
            id="requester-test-002",
            telegram_id=555555555,
            first_name="Maria",
            last_name="Sidorova",
            username="maria_s",
            preferred_sports='["cycling"]',
            has_completed_onboarding=True
        )

        session.add(admin_user)
        session.add(requester_user)
        session.add(requester_user2)
        session.commit()

        print("[OK] Created test users:")
        print(f"   - Admin: {admin_user.first_name} (@{admin_user.username}) - telegram_id: {admin_user.telegram_id}")
        print(f"   - Requester 1: {requester_user.first_name} (@{requester_user.username}) - telegram_id: {requester_user.telegram_id}")
        print(f"   - Requester 2: {requester_user2.first_name} (@{requester_user2.username}) - telegram_id: {requester_user2.telegram_id}")

        # Create test club
        club = Club(
            id="club-test-001",
            name="Almaty Runners Test",
            description="Test club for requests",
            creator_id=admin_user.id,
            city="Almaty",
            country="Kazakhstan",
            is_open=False  # Closed club
        )

        session.add(club)
        session.commit()

        print(f"\n[OK] Created test club: {club.name} (is_open: {club.is_open})")

        # Create admin membership
        membership = Membership(
            user_id=admin_user.id,
            club_id=club.id,
            role=UserRole.ADMIN
        )

        session.add(membership)
        session.commit()

        print(f"[OK] Created admin membership for {admin_user.first_name}")

        # Create pending join requests
        jr_storage = JoinRequestStorage(session=session)

        request1 = jr_storage.create_join_request(
            user_id=requester_user.id,
            entity_type="club",
            entity_id=club.id
        )

        request2 = jr_storage.create_join_request(
            user_id=requester_user2.id,
            entity_type="club",
            entity_id=club.id
        )

        print(f"\n[OK] Created pending join requests:")
        print(f"   - Request 1: {requester_user.first_name} -> {club.name}")
        print(f"   - Request 2: {requester_user2.first_name} -> {club.name}")

        # Create approved request (for /my_requests testing)
        approved_request = JoinRequest(
            id="approved-test-001",
            user_id=requester_user.id,
            club_id=club.id,
            status=JoinRequestStatus.APPROVED,
            created_at=datetime.now(timezone.utc)
        )
        session.add(approved_request)
        session.commit()

        print(f"[OK] Created approved request for testing /my_requests")

        print("\n" + "="*60)
        print("TEST DATA CREATED SUCCESSFULLY!")
        print("="*60)
        print("\nTo test /requests command:")
        print(f"   Send /requests from telegram_id: {admin_user.telegram_id} (@{admin_user.username})")
        print(f"   Expected: 2 pending requests shown")

        print("\nTo test /my_requests command:")
        print(f"   Send /my_requests from telegram_id: {requester_user.telegram_id} (@{requester_user.username})")
        print(f"   Expected: 1 pending + 1 approved request shown")

        print("\nTo clean up test data:")
        print(f"   python scripts/test_requests_commands.py cleanup")

    except Exception as e:
        print(f"[ERROR] Error creating test data: {e}")
        session.rollback()
        raise

    finally:
        session.close()


def cleanup_test_data():
    """Remove test data"""
    session = SessionLocal()

    try:
        # Delete join requests
        session.query(JoinRequest).filter(
            JoinRequest.id.in_([
                "approved-test-001"
            ])
        ).delete(synchronize_session=False)

        # Delete memberships
        session.query(Membership).filter(
            Membership.club_id == "club-test-001"
        ).delete(synchronize_session=False)

        # Delete club
        session.query(Club).filter(Club.id == "club-test-001").delete()

        # Delete users
        session.query(User).filter(
            User.id.in_([
                "admin-test-001",
                "requester-test-001",
                "requester-test-002"
            ])
        ).delete(synchronize_session=False)

        session.commit()
        print("[OK] Test data cleaned up successfully!")

    except Exception as e:
        print(f"[ERROR] Error cleaning up: {e}")
        session.rollback()

    finally:
        session.close()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "cleanup":
        cleanup_test_data()
    else:
        create_test_data()
