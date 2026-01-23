"""
LEGACY Migration: Add membership sync fields

NOTE: This migration script is DEPRECATED. It only works with SQLite.
For PostgreSQL, use Alembic migrations instead:
    alembic upgrade head

This migration adds new columns for Telegram group member synchronization:
- Club: bot_is_admin, last_sync_at, telegram_member_count, sync_completed
- Membership: status, source, last_seen, left_at

Run with: python migrations/001_add_membership_sync_fields.py
"""

import sqlite3
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from storage.db import DATABASE_URL


def get_db_path():
    """Extract SQLite database path from DATABASE_URL."""
    if DATABASE_URL.startswith("sqlite:///"):
        return DATABASE_URL.replace("sqlite:///", "")
    raise ValueError(f"This migration only supports SQLite. Got: {DATABASE_URL}")


def migrate():
    """Run the migration."""
    db_path = get_db_path()
    print(f"Migrating database: {db_path}")

    if not os.path.exists(db_path):
        print("Database file not found. Run init_db() first.")
        return False

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Add new columns to clubs table
    print("\nAdding columns to clubs table...")
    club_columns = [
        ("bot_is_admin", "BOOLEAN DEFAULT 0 NOT NULL"),
        ("last_sync_at", "DATETIME"),
        ("telegram_member_count", "INTEGER"),
        ("sync_completed", "BOOLEAN DEFAULT 0 NOT NULL"),
    ]

    for col_name, col_def in club_columns:
        try:
            cursor.execute(f"ALTER TABLE clubs ADD COLUMN {col_name} {col_def}")
            print(f"  + {col_name}")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print(f"  = {col_name} (already exists)")
            else:
                print(f"  ! {col_name}: {e}")

    # Add new columns to memberships table
    print("\nAdding columns to memberships table...")
    membership_columns = [
        ("status", "VARCHAR(20) DEFAULT 'active' NOT NULL"),
        ("source", "VARCHAR(30) DEFAULT 'manual' NOT NULL"),
        ("last_seen", "DATETIME"),
        ("left_at", "DATETIME"),
    ]

    for col_name, col_def in membership_columns:
        try:
            cursor.execute(f"ALTER TABLE memberships ADD COLUMN {col_name} {col_def}")
            print(f"  + {col_name}")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print(f"  = {col_name} (already exists)")
            else:
                print(f"  ! {col_name}: {e}")

    conn.commit()
    conn.close()

    print("\nMigration completed successfully!")
    return True


def verify():
    """Verify the migration was applied correctly."""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("\nVerifying migration...")

    cursor.execute("PRAGMA table_info(clubs)")
    club_columns = [row[1] for row in cursor.fetchall()]
    expected_club = ["bot_is_admin", "last_sync_at", "telegram_member_count", "sync_completed"]
    missing_club = [c for c in expected_club if c not in club_columns]

    cursor.execute("PRAGMA table_info(memberships)")
    membership_columns = [row[1] for row in cursor.fetchall()]
    expected_membership = ["status", "source", "last_seen", "left_at"]
    missing_membership = [c for c in expected_membership if c not in membership_columns]

    conn.close()

    if missing_club or missing_membership:
        print(f"  Missing in clubs: {missing_club}")
        print(f"  Missing in memberships: {missing_membership}")
        return False

    print("  All columns present!")
    return True


if __name__ == "__main__":
    success = migrate()
    if success:
        verify()
