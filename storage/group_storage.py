"""
Group Storage Layer

Provides high-level interface for group-related database operations.
Used by both Telegram bot and FastAPI endpoints.
"""

from typing import Optional, Dict, Any
import logging

from sqlalchemy.orm import Session
from sqlalchemy import func
from storage.db import SessionLocal, Group, Membership

logger = logging.getLogger(__name__)


class GroupStorage:
    """
    Storage class for Group operations with context manager support.

    Usage:
        # Bot usage (creates own session)
        with GroupStorage() as group_storage:
            group = group_storage.get_group_by_id(group_id)

        # FastAPI usage (uses provided session)
        group_storage = GroupStorage(session=db)
        preview = group_storage.get_group_preview(group_id)
    """

    def __init__(self, session: Optional[Session] = None):
        """
        Initialize GroupStorage.

        Args:
            session: Optional SQLAlchemy session. If not provided, creates own session.
        """
        self.session = session
        self._own_session = session is None
        if self._own_session:
            self.session = SessionLocal()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close session if we created it."""
        if self._own_session and self.session:
            self.session.close()

    def get_group_by_id(self, group_id: str) -> Optional[Group]:
        """
        Get group by UUID.

        Args:
            group_id: Group UUID

        Returns:
            Group object or None if not found
        """
        try:
            return self.session.query(Group).filter(Group.id == group_id).first()
        except Exception as e:
            logger.error(f"Error in get_group_by_id: {e}")
            return None

    def get_group_preview(self, group_id: str) -> Optional[Dict[str, Any]]:
        """
        Get group preview data for invitation messages.

        Args:
            group_id: Group UUID

        Returns:
            Dictionary with group preview data or None if not found
            {
                'id': 'uuid',
                'name': 'Group Name',
                'description': 'Group description',
                'member_count': 25,
                'club_id': 'uuid' or None,
                'club_name': 'Club Name' or None,
                'is_independent': True/False
            }
        """
        try:
            group = self.session.query(Group).filter(Group.id == group_id).first()
            if not group:
                return None

            # Count members
            member_count = self.session.query(func.count(Membership.id)).filter(
                Membership.group_id == group_id
            ).scalar() or 0

            # Get club info if group belongs to a club
            club_name = None
            if group.club_id:
                from storage.db import Club
                club = self.session.query(Club).filter(Club.id == group.club_id).first()
                if club:
                    club_name = club.name

            return {
                'id': group.id,
                'name': group.name,
                'description': group.description or '',
                'member_count': member_count,
                'club_id': group.club_id,
                'club_name': club_name,
                'is_independent': group.club_id is None,
                'city': group.city,
                'photo': group.photo
            }

        except Exception as e:
            logger.error(f"Error in get_group_preview: {e}")
            return None
