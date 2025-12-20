"""
User Storage Layer

Provides high-level interface for user-related database operations.
Used by both Telegram bot and FastAPI endpoints.
"""

from typing import Optional, List
from datetime import datetime
import json
import logging

from sqlalchemy.orm import Session
from storage.db import SessionLocal, User

logger = logging.getLogger(__name__)


class UserStorage:
    """
    Storage class for User operations with context manager support.

    Usage:
        # Bot usage (creates own session)
        with UserStorage() as user_storage:
            user = user_storage.get_or_create_user(telegram_id=123)

        # FastAPI usage (uses provided session)
        user_storage = UserStorage(session=db)
        user = user_storage.get_user_by_id(user_id)
    """

    def __init__(self, session: Optional[Session] = None):
        """
        Initialize UserStorage.

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

    def get_or_create_user(
        self,
        telegram_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None
    ) -> User:
        """
        Get existing user or create new one.

        Args:
            telegram_id: Telegram user ID
            username: Telegram username (without @)
            first_name: User's first name
            last_name: User's last name

        Returns:
            User object
        """
        try:
            user = self.session.query(User).filter(
                User.telegram_id == telegram_id
            ).first()

            if not user:
                # Create new user
                user = User(
                    telegram_id=telegram_id,
                    username=username,
                    first_name=first_name,
                    last_name=last_name
                )
                self.session.add(user)
                self.session.commit()
                self.session.refresh(user)
                logger.info(f"Created new user: {telegram_id}")
            else:
                # Update user info if changed
                updated = False
                if username and user.username != username:
                    user.username = username
                    updated = True
                if first_name and user.first_name != first_name:
                    user.first_name = first_name
                    updated = True
                if last_name and user.last_name != last_name:
                    user.last_name = last_name
                    updated = True

                if updated:
                    user.last_seen_at = datetime.utcnow()
                    user.updated_at = datetime.utcnow()
                    self.session.commit()
                    self.session.refresh(user)
                    logger.info(f"Updated user info: {telegram_id}")

            return user

        except Exception as e:
            self.session.rollback()
            logger.error(f"Error in get_or_create_user: {e}")
            raise

    def get_user_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """
        Get user by Telegram ID.

        Args:
            telegram_id: Telegram user ID

        Returns:
            User object or None if not found
        """
        try:
            return self.session.query(User).filter(
                User.telegram_id == telegram_id
            ).first()
        except Exception as e:
            logger.error(f"Error in get_user_by_telegram_id: {e}")
            return None

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """
        Get user by internal UUID.

        Args:
            user_id: User UUID

        Returns:
            User object or None if not found
        """
        try:
            return self.session.query(User).filter(User.id == user_id).first()
        except Exception as e:
            logger.error(f"Error in get_user_by_id: {e}")
            return None

    def update_preferred_sports(self, user_id: str, sports: List[str]) -> Optional[User]:
        """
        Update user's preferred sports.

        Args:
            user_id: User UUID
            sports: List of sport IDs (e.g., ["RUNNING", "TRAIL_RUNNING"])

        Returns:
            Updated User object or None if user not found
        """
        try:
            user = self.session.query(User).filter(User.id == user_id).first()
            if user:
                user.preferred_sports = json.dumps(sports)
                user.updated_at = datetime.utcnow()
                self.session.commit()
                self.session.refresh(user)
                logger.info(f"Updated preferred sports for user {user_id}: {sports}")
                return user
            return None
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error in update_preferred_sports: {e}")
            raise

    def mark_onboarding_complete(self, user_id: str) -> Optional[User]:
        """
        Mark user's onboarding as complete.

        Args:
            user_id: User UUID

        Returns:
            Updated User object or None if user not found
        """
        try:
            user = self.session.query(User).filter(User.id == user_id).first()
            if user:
                user.has_completed_onboarding = True
                user.updated_at = datetime.utcnow()
                self.session.commit()
                self.session.refresh(user)
                logger.info(f"Marked onboarding complete for user {user_id}")
                return user
            return None
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error in mark_onboarding_complete: {e}")
            raise

    def get_preferred_sports(self, user_id: str) -> List[str]:
        """
        Get user's preferred sports as list.

        Args:
            user_id: User UUID

        Returns:
            List of sport IDs or empty list
        """
        try:
            user = self.session.query(User).filter(User.id == user_id).first()
            if user and user.preferred_sports:
                return json.loads(user.preferred_sports)
            return []
        except Exception as e:
            logger.error(f"Error in get_preferred_sports: {e}")
            return []

    def update_photo(self, user_id: str, photo: str) -> Optional[User]:
        """
        Update user's photo (Telegram file_id or URL).

        Args:
            user_id: User UUID
            photo: Photo file_id or URL

        Returns:
            Updated User object or None if user not found
        """
        try:
            user = self.session.query(User).filter(User.id == user_id).first()
            if user:
                user.photo = photo
                user.updated_at = datetime.utcnow()
                self.session.commit()
                self.session.refresh(user)
                logger.info(f"Updated photo for user {user_id}")
                return user
            return None
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error in update_photo: {e}")
            raise

    def update_profile(self, user_id: str, photo: Optional[str] = None,
                      strava_link: Optional[str] = None) -> Optional[User]:
        """
        Update user's profile (photo and/or strava_link).

        Args:
            user_id: User UUID
            photo: Optional photo file_id or URL
            strava_link: Optional Strava profile URL

        Returns:
            Updated User object or None if user not found
        """
        try:
            user = self.session.query(User).filter(User.id == user_id).first()
            if user:
                if photo is not None:
                    user.photo = photo
                if strava_link is not None:
                    user.strava_link = strava_link
                user.updated_at = datetime.utcnow()
                self.session.commit()
                self.session.refresh(user)
                logger.info(f"Updated profile for user {user_id}")
                return user
            return None
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error in update_profile: {e}")
            raise
