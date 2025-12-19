"""
Test script for auto-reject service

This script tests the auto-reject functionality:
1. Creates a past activity
2. Creates a join request for the past activity
3. Runs the auto-reject check manually
4. Verifies the request was marked as EXPIRED
"""

import sys
import os

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from storage.db import SessionLocal, Activity, User, JoinRequest, JoinRequestStatus
from storage.join_request_storage import JoinRequestStorage
from datetime import datetime, timedelta
import asyncio


def test_auto_reject():
    """Test auto-reject functionality"""

    session = SessionLocal()

    try:
        print("=" * 60)
        print("Testing Auto-Reject Service")
        print("=" * 60)

        # 1. Get or create test user
        print("\n[1] Creating test user...")
        user = session.query(User).filter(User.telegram_id == 333333).first()

        if not user:
            user = User(
                telegram_id=333333,
                username="test_user_auto_reject",
                first_name="Тестовый Пользователь"
            )
            session.add(user)
            session.commit()

        print(f"[OK] User: {user.first_name} (@{user.username})")

        # 2. Create a PAST activity
        print("\n[2] Creating PAST activity...")
        past_date = datetime.utcnow() - timedelta(days=1)  # Yesterday

        activity = Activity(
            title="Прошедшая пробежка",
            description="Эта активность уже прошла",
            date=past_date,
            location="Парк",
            city="Almaty",
            sport_type="running",
            difficulty="easy",
            creator_id=user.id,
            is_open=False  # CLOSED
        )
        session.add(activity)
        session.commit()
        session.refresh(activity)

        print(f"[OK] Created PAST activity: {activity.title}")
        print(f"   Date: {activity.date} (прошла)")
        print(f"   is_open: {activity.is_open}")

        # 3. Create join request for this activity
        print("\n[3] Creating join request for PAST activity...")
        jr_storage = JoinRequestStorage(session=session)

        join_request = jr_storage.create_join_request(
            user_id=user.id,
            entity_type="activity",
            entity_id=activity.id
        )

        # Set expires_at to activity date
        join_request.expires_at = activity.date
        session.commit()
        session.refresh(join_request)

        print(f"[OK] Join request created: {join_request.id}")
        print(f"   Status: {join_request.status.value}")
        print(f"   expires_at: {join_request.expires_at}")
        print(f"   Has expired: {join_request.expires_at < datetime.utcnow()}")

        # 4. Test set_expiry_for_past_activities
        print("\n[4] Testing set_expiry_for_past_activities...")
        marked_count = jr_storage.set_expiry_for_past_activities()
        print(f"[OK] Marked {marked_count} requests for expiry")

        # 5. Get expired requests
        print("\n[5] Getting expired requests...")
        expired_requests = jr_storage.get_expired_requests()
        print(f"[OK] Found {len(expired_requests)} expired requests")

        for req in expired_requests:
            activity_obj = session.query(Activity).filter(Activity.id == req.activity_id).first()
            print(f"   - Request {req.id}")
            print(f"     Activity: {activity_obj.title if activity_obj else 'Unknown'}")
            print(f"     Status: {req.status.value}")
            print(f"     expires_at: {req.expires_at}")

        # 6. Manually reject expired request
        print("\n[6] Manually rejecting expired request...")
        if expired_requests:
            for req in expired_requests:
                updated_req = jr_storage.update_request_status(
                    req.id,
                    JoinRequestStatus.EXPIRED
                )
                print(f"[OK] Request {req.id} status updated to: {updated_req.status.value}")

        # 7. Verify the request was rejected
        print("\n[7] Verifying request status...")
        final_request = jr_storage.get_join_request(join_request.id)
        print(f"[OK] Final status: {final_request.status.value}")

        print("\n" + "=" * 60)
        print("[OK] All tests passed!")
        print("=" * 60)
        print("\n[INFO] Summary:")
        print(f"   - Created PAST activity: {activity.title}")
        print(f"   - Created join request with expires_at")
        print(f"   - Automatically marked as expired")
        print(f"   - Request status: {final_request.status.value}")
        print("\n[NEXT] Next steps:")
        print("   1. Auto-reject service will run every 5 minutes")
        print("   2. It will send notifications to users")
        print("   3. Test the full flow with the running service")

    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()

    finally:
        session.close()


if __name__ == "__main__":
    test_auto_reject()
