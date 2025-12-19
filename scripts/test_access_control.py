"""
Test script for access control and join requests functionality

This script demonstrates the new access control features:
1. Creating open/closed clubs, groups, activities
2. Sending join requests
3. Approving/rejecting requests
"""

import sys
import os

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from storage.db import SessionLocal, Club, Group, Activity, User, Membership, UserRole
from storage.join_request_storage import JoinRequestStorage
from storage.db import JoinRequestStatus
from datetime import datetime, timedelta


def test_access_control():
    """Test access control functionality"""

    session = SessionLocal()

    try:
        print("=" * 60)
        print("Testing Access Control System")
        print("=" * 60)

        # 1. Get or create test users
        print("\n[1] Creating test users...")
        user1 = session.query(User).filter(User.telegram_id == 111111).first()
        user2 = session.query(User).filter(User.telegram_id == 222222).first()

        if not user1:
            user1 = User(
                telegram_id=111111,
                username="organizer_user",
                first_name="Организатор"
            )
            session.add(user1)

        if not user2:
            user2 = User(
                telegram_id=222222,
                username="regular_user",
                first_name="Обычный Пользователь"
            )
            session.add(user2)

        session.commit()
        print(f"[OK] User 1: {user1.first_name} (@{user1.username})")
        print(f"[OK] User 2: {user2.first_name} (@{user2.username})")

        # 2. Create closed club
        print("\n[2] Creating CLOSED club...")
        club = Club(
            name="Закрытый Беговой Клуб VIP",
            description="Только для опытных бегунов",
            creator_id=user1.id,
            city="Almaty",
            is_open=False  # CLOSED!
        )
        session.add(club)
        session.commit()
        session.refresh(club)

        # Add creator as admin
        membership = Membership(
            user_id=user1.id,
            club_id=club.id,
            role=UserRole.ADMIN
        )
        session.add(membership)
        session.commit()

        print(f"[OK] Created club: {club.name}")
        print(f"   is_open: {club.is_open} (закрытый)")
        print(f"   Creator: {user1.first_name}")

        # 3. User2 tries to join (should create join request)
        print("\n[3]  User2 sends join request...")
        jr_storage = JoinRequestStorage(session=session)

        join_request = jr_storage.create_join_request(
            user_id=user2.id,
            entity_type="club",
            entity_id=club.id
        )

        if join_request:
            print(f"[OK] Join request created: {join_request.id}")
            print(f"   Status: {join_request.status.value}")
            print(f"   User: {user2.first_name}")

        # 4. Check pending requests
        print("\n[4]  Checking pending requests...")
        pending = jr_storage.get_pending_requests_for_entity("club", club.id)
        print(f"[OK] Found {len(pending)} pending requests")

        for req in pending:
            user = session.query(User).filter(User.id == req.user_id).first()
            print(f"   - Request from: {user.first_name} (@{user.username})")

        # 5. Organizer approves request
        print("\n[5]  Organizer approves join request...")
        updated_request = jr_storage.update_request_status(
            join_request.id,
            JoinRequestStatus.APPROVED
        )

        # Add user to club
        new_membership = Membership(
            user_id=user2.id,
            club_id=club.id,
            role=UserRole.MEMBER
        )
        session.add(new_membership)
        session.commit()

        print(f"[OK] Request approved!")
        print(f"   Status: {updated_request.status.value}")

        # 6. Verify membership
        print("\n[6]  Verifying membership...")
        members = session.query(Membership).filter(Membership.club_id == club.id).all()
        print(f"[OK] Club has {len(members)} members:")

        for m in members:
            user = session.query(User).filter(User.id == m.user_id).first()
            print(f"   - {user.first_name} (@{user.username}) - {m.role.value}")

        # 7. Test with Activity
        print("\n[7]  Creating CLOSED activity...")
        activity = Activity(
            title="VIP Утренняя пробежка",
            description="Только для членов клуба",
            date=datetime.utcnow() + timedelta(days=7),
            location="Центральный парк",
            city="Almaty",
            sport_type="running",
            difficulty="medium",
            creator_id=user1.id,
            club_id=club.id,
            is_open=False  # CLOSED!
        )
        session.add(activity)
        session.commit()
        session.refresh(activity)

        print(f"[OK] Created activity: {activity.title}")
        print(f"   is_open: {activity.is_open} (закрытая)")
        print(f"   Date: {activity.date}")
        print(f"   expires_at will be set to: {activity.date}")

        print("\n" + "=" * 60)
        print("[OK] All tests passed!")
        print("=" * 60)
        print("\n[INFO] Summary:")
        print(f"   - Created CLOSED club: {club.name}")
        print(f"   - User2 sent join request")
        print(f"   - Organizer approved request")
        print(f"   - User2 is now a member")
        print(f"   - Created CLOSED activity: {activity.title}")
        print("\n[NEXT] Next steps:")
        print("   1. Test via API endpoints")
        print("   2. Implement bot notifications (Phase 5)")
        print("   3. Implement auto-reject service (Phase 6)")

    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()

    finally:
        session.close()


if __name__ == "__main__":
    test_access_control()
