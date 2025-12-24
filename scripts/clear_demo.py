"""
Clear Demo Data Script for Ayda Run

Removes all demo data from the database:
- Demo users (is_demo=True)
- Demo clubs (is_demo=True)
- Demo groups (is_demo=True)
- Demo activities (is_demo=True)
- All related memberships and participations (cascading delete)

Usage:
    python scripts/clear_demo.py
"""

import sys
import os

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from storage.db import (
    SessionLocal, init_db,
    User, Club, Group, Activity, Membership, Participation, RecurringTemplate
)


def clear_demo_data():
    """Remove all demo data from database"""
    print("=" * 70)
    print(" " * 20 + "CLEAR DEMO DATA")
    print("=" * 70)

    # Initialize database
    init_db()
    db = SessionLocal()

    try:
        # Check if demo data exists
        demo_users_count = db.query(User).filter(User.is_demo == True).count()
        demo_clubs_count = db.query(Club).filter(Club.is_demo == True).count()
        demo_groups_count = db.query(Group).filter(Group.is_demo == True).count()
        demo_templates_count = db.query(RecurringTemplate).filter(RecurringTemplate.is_demo == True).count()
        demo_activities_count = db.query(Activity).filter(Activity.is_demo == True).count()

        if demo_users_count == 0 and demo_clubs_count == 0 and demo_groups_count == 0 and demo_activities_count == 0 and demo_templates_count == 0:
            print("\n[INFO] No demo data found in database.")
            return

        print("\n[INFO] Found demo data:")
        print(f"   - {demo_users_count} demo users")
        print(f"   - {demo_clubs_count} demo clubs")
        print(f"   - {demo_groups_count} demo groups")
        print(f"   - {demo_templates_count} demo recurring templates")
        print(f"   - {demo_activities_count} demo activities")

        # Ask for confirmation
        print("\n[WARNING] This will permanently delete all demo data!")
        response = input("Are you sure you want to continue? (yes/no): ")

        if response.lower() not in ['yes', 'y']:
            print("[CANCELLED] Operation cancelled.")
            return

        print("\n[CLEARING] Removing demo data...")

        # Delete in correct order to respect foreign key constraints

        # 1. Delete participations for demo activities
        print("  [1/7] Deleting participations for demo activities...")
        demo_activity_ids = [a.id for a in db.query(Activity).filter(Activity.is_demo == True).all()]
        deleted_participations = 0
        if demo_activity_ids:
            deleted_participations = db.query(Participation).filter(
                Participation.activity_id.in_(demo_activity_ids)
            ).delete(synchronize_session=False)
            print(f"     - Deleted {deleted_participations} participations")
        else:
            print("     - No participations to delete")

        # 2. Delete memberships for demo users (will cascade)
        print("  [2/7] Deleting memberships for demo users...")
        demo_user_ids = [u.id for u in db.query(User).filter(User.is_demo == True).all()]
        if demo_user_ids:
            deleted_memberships = db.query(Membership).filter(
                Membership.user_id.in_(demo_user_ids)
            ).delete(synchronize_session=False)
            print(f"     - Deleted {deleted_memberships} memberships")
        else:
            print("     - No memberships to delete")

        # 3. Delete demo activities
        print("  [3/7] Deleting demo activities...")
        deleted_activities = db.query(Activity).filter(Activity.is_demo == True).delete(synchronize_session=False)
        print(f"     - Deleted {deleted_activities} activities")

        # 4. Delete demo recurring templates
        print("  [4/7] Deleting demo recurring templates...")
        deleted_templates = db.query(RecurringTemplate).filter(RecurringTemplate.is_demo == True).delete(synchronize_session=False)
        print(f"     - Deleted {deleted_templates} recurring templates")

        # 5. Delete demo groups (cascade will handle group memberships)
        print("  [5/7] Deleting demo groups...")
        deleted_groups = db.query(Group).filter(Group.is_demo == True).delete(synchronize_session=False)
        print(f"     - Deleted {deleted_groups} groups")

        # 6. Delete demo clubs (cascade will handle club memberships)
        print("  [6/7] Deleting demo clubs...")
        deleted_clubs = db.query(Club).filter(Club.is_demo == True).delete(synchronize_session=False)
        print(f"     - Deleted {deleted_clubs} clubs")

        # 7. Delete demo users (cascade will handle user relationships)
        print("  [7/7] Deleting demo users...")
        deleted_users = db.query(User).filter(User.is_demo == True).delete(synchronize_session=False)
        print(f"     - Deleted {deleted_users} users")

        # Commit all changes
        db.commit()

        print("\n" + "=" * 70)
        print(" " * 20 + "CLEARING COMPLETED!")
        print("=" * 70)

        print("\nSummary:")
        print(f"   Users deleted: {deleted_users}")
        print(f"   Clubs deleted: {deleted_clubs}")
        print(f"   Groups deleted: {deleted_groups}")
        print(f"   Recurring templates deleted: {deleted_templates}")
        print(f"   Activities deleted: {deleted_activities}")
        print(f"   Memberships deleted: {deleted_memberships}")
        print(f"   Participations deleted: {deleted_participations}")

        # Verify cleanup
        print("\n[VERIFICATION] Checking for remaining demo data...")
        remaining_users = db.query(User).filter(User.is_demo == True).count()
        remaining_clubs = db.query(Club).filter(Club.is_demo == True).count()
        remaining_groups = db.query(Group).filter(Group.is_demo == True).count()
        remaining_templates = db.query(RecurringTemplate).filter(RecurringTemplate.is_demo == True).count()
        remaining_activities = db.query(Activity).filter(Activity.is_demo == True).count()

        if remaining_users == 0 and remaining_clubs == 0 and remaining_groups == 0 and remaining_activities == 0 and remaining_templates == 0:
            print("[SUCCESS] All demo data successfully removed!")
        else:
            print(f"[WARNING] Some demo data still exists:")
            print(f"   - Users: {remaining_users}")
            print(f"   - Clubs: {remaining_clubs}")
            print(f"   - Groups: {remaining_groups}")
            print(f"   - Recurring templates: {remaining_templates}")
            print(f"   - Activities: {remaining_activities}")

    except Exception as e:
        print(f"\n[ERROR] Error during cleanup: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    clear_demo_data()
