"""
Membership Storage Layer

Provides high-level interface for membership-related database operations.
Handles adding users to clubs and groups.
"""

from typing import Optional, List
import logging

from sqlalchemy.orm import Session
from storage.db import SessionLocal, Membership, UserRole

logger = logging.getLogger(__name__)


class MembershipStorage:
    """
    Storage class for Membership operations with context manager support.

    Usage:
        # Bot usage (creates own session)
        with MembershipStorage() as membership_storage:
            membership_storage.add_member_to_club(user_id, club_id)

        # FastAPI usage (uses provided session)
        membership_storage = MembershipStorage(session=db)
        is_member = membership_storage.is_member_of_club(user_id, club_id)
    """

    def __init__(self, session: Optional[Session] = None):
        """
        Initialize MembershipStorage.

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

    def add_member_to_club(
        self,
        user_id: str,
        club_id: str,
        role: UserRole = UserRole.MEMBER
    ) -> Optional[Membership]:
        """
        Add user to club as member.

        Args:
            user_id: User UUID
            club_id: Club UUID
            role: User role in the club (default: MEMBER)

        Returns:
            Membership object or None if already exists
        """
        try:
            # Check if membership already exists
            existing = self.session.query(Membership).filter(
                Membership.user_id == user_id,
                Membership.club_id == club_id
            ).first()

            if existing:
                logger.info(f"User {user_id} already member of club {club_id}")
                return existing

            # Create new membership
            membership = Membership(
                user_id=user_id,
                club_id=club_id,
                role=role
            )
            self.session.add(membership)
            self.session.commit()
            self.session.refresh(membership)
            logger.info(f"Added user {user_id} to club {club_id} as {role}")
            return membership

        except Exception as e:
            self.session.rollback()
            logger.error(f"Error in add_member_to_club: {e}")
            raise

    def add_member_to_group(
        self,
        user_id: str,
        group_id: str,
        role: UserRole = UserRole.MEMBER
    ) -> Optional[Membership]:
        """
        Add user to group as member.

        Args:
            user_id: User UUID
            group_id: Group UUID
            role: User role in the group (default: MEMBER)

        Returns:
            Membership object or None if already exists
        """
        try:
            # Check if membership already exists
            existing = self.session.query(Membership).filter(
                Membership.user_id == user_id,
                Membership.group_id == group_id
            ).first()

            if existing:
                logger.info(f"User {user_id} already member of group {group_id}")
                return existing

            # Create new membership
            membership = Membership(
                user_id=user_id,
                group_id=group_id,
                role=role
            )
            self.session.add(membership)
            self.session.commit()
            self.session.refresh(membership)
            logger.info(f"Added user {user_id} to group {group_id} as {role}")
            return membership

        except Exception as e:
            self.session.rollback()
            logger.error(f"Error in add_member_to_group: {e}")
            raise

    def is_member_of_club(self, user_id: str, club_id: str) -> bool:
        """
        Check if user is member of club.

        Args:
            user_id: User UUID
            club_id: Club UUID

        Returns:
            True if user is member, False otherwise
        """
        try:
            membership = self.session.query(Membership).filter(
                Membership.user_id == user_id,
                Membership.club_id == club_id
            ).first()
            return membership is not None
        except Exception as e:
            logger.error(f"Error in is_member_of_club: {e}")
            return False

    def is_member_of_group(self, user_id: str, group_id: str) -> bool:
        """
        Check if user is member of group.

        Args:
            user_id: User UUID
            group_id: Group UUID

        Returns:
            True if user is member, False otherwise
        """
        try:
            membership = self.session.query(Membership).filter(
                Membership.user_id == user_id,
                Membership.group_id == group_id
            ).first()
            return membership is not None
        except Exception as e:
            logger.error(f"Error in is_member_of_group: {e}")
            return False

    def get_user_memberships(self, user_id: str) -> List[Membership]:
        """
        Get all memberships for a user.

        Args:
            user_id: User UUID

        Returns:
            List of Membership objects
        """
        try:
            return self.session.query(Membership).filter(
                Membership.user_id == user_id
            ).all()
        except Exception as e:
            logger.error(f"Error in get_user_memberships: {e}")
            return []

    def remove_member_from_club(self, user_id: str, club_id: str) -> bool:
        """
        Remove user from club.

        Args:
            user_id: User UUID
            club_id: Club UUID

        Returns:
            True if successful, False otherwise
        """
        try:
            membership = self.session.query(Membership).filter(
                Membership.user_id == user_id,
                Membership.club_id == club_id
            ).first()

            if not membership:
                return False

            self.session.delete(membership)
            self.session.commit()
            logger.info(f"Removed user {user_id} from club {club_id}")
            return True

        except Exception as e:
            self.session.rollback()
            logger.error(f"Error in remove_member_from_club: {e}")
            return False

    def remove_member_from_group(self, user_id: str, group_id: str) -> bool:
        """
        Remove user from group.

        Args:
            user_id: User UUID
            group_id: Group UUID

        Returns:
            True if successful, False otherwise
        """
        try:
            membership = self.session.query(Membership).filter(
                Membership.user_id == user_id,
                Membership.group_id == group_id
            ).first()

            if not membership:
                return False

            self.session.delete(membership)
            self.session.commit()
            logger.info(f"Removed user {user_id} from group {group_id}")
            return True

        except Exception as e:
            self.session.rollback()
            logger.error(f"Error in remove_member_from_group: {e}")
            return False
