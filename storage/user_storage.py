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
from sqlalchemy import func
from datetime import timedelta
from collections import defaultdict
from storage.db import (
    SessionLocal, User, Participation, Activity, Club, Group,
    ParticipationStatus, SportType
)

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
                      strava_link: Optional[str] = None,
                      show_photo: Optional[bool] = None) -> Optional[User]:
        """
        Update user's profile (photo, strava_link, show_photo).

        Args:
            user_id: User UUID
            photo: Optional photo file_id or URL
            strava_link: Optional Strava profile URL
            show_photo: Optional flag to show photo instead of initials

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
                if show_photo is not None:
                    user.show_photo = show_photo
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

    def get_detailed_stats(self, user_id: str, period: str = "month") -> dict:
        """
        Get detailed statistics for user.

        Args:
            user_id: User UUID
            period: 'month', 'quarter', 'year', 'all'

        Returns:
            Dict with registered, attended, clubs stats, sports stats
        """
        # Sport type mappings
        SPORT_NAMES = {
            SportType.RUNNING: ("running", "Бег", "🏃"),
            SportType.TRAIL: ("trail", "Трейл", "⛰️"),
            SportType.HIKING: ("hiking", "Хайкинг", "🥾"),
            SportType.CYCLING: ("cycling", "Вело", "🚴"),
            SportType.YOGA: ("yoga", "Йога", "🧘"),
            SportType.WORKOUT: ("workout", "Workout", "💪"),
            SportType.OTHER: ("other", "Другое", "🏋️"),
        }

        try:
            # Calculate date range based on period
            now = datetime.utcnow()
            if period == "month":
                start_date = now - timedelta(days=30)
            elif period == "quarter":
                start_date = now - timedelta(days=90)
            elif period == "year":
                start_date = now - timedelta(days=365)
            else:  # all
                start_date = None

            # Query participations with activities
            query = self.session.query(Participation).join(Activity).filter(
                Participation.user_id == user_id
            )

            if start_date:
                query = query.filter(Activity.date >= start_date)

            participations = query.all()

            # Count registered and attended
            total_registered = len(participations)
            total_attended = sum(
                1 for p in participations
                if p.status == ParticipationStatus.ATTENDED or p.attended
            )

            # Aggregate by club/group
            club_stats = defaultdict(lambda: {"registered": 0, "attended": 0})
            group_stats = defaultdict(lambda: {"registered": 0, "attended": 0})
            sport_counts = defaultdict(int)

            for p in participations:
                activity = p.activity
                is_attended = p.status == ParticipationStatus.ATTENDED or p.attended

                # Count by club
                if activity.club_id:
                    club_stats[activity.club_id]["registered"] += 1
                    if is_attended:
                        club_stats[activity.club_id]["attended"] += 1

                # Count by group
                if activity.group_id:
                    group_stats[activity.group_id]["registered"] += 1
                    if is_attended:
                        group_stats[activity.group_id]["attended"] += 1

                # Count by sport type (only attended)
                if is_attended and activity.sport_type:
                    sport_counts[activity.sport_type] += 1

            # Get club details
            clubs_result = []
            if club_stats:
                clubs = self.session.query(Club).filter(
                    Club.id.in_(club_stats.keys())
                ).all()
                for club in clubs:
                    stats = club_stats[club.id]
                    # Get initials from name
                    words = club.name.split()
                    initials = "".join(w[0].upper() for w in words[:2]) if words else "?"
                    clubs_result.append({
                        "id": club.id,
                        "name": club.name,
                        "avatar": club.photo,
                        "initials": initials,
                        "type": "club",
                        "registered": stats["registered"],
                        "attended": stats["attended"],
                    })

            # Get group details
            if group_stats:
                groups = self.session.query(Group).filter(
                    Group.id.in_(group_stats.keys())
                ).all()
                for group in groups:
                    stats = group_stats[group.id]
                    words = group.name.split()
                    initials = "".join(w[0].upper() for w in words[:2]) if words else "?"
                    clubs_result.append({
                        "id": group.id,
                        "name": group.name,
                        "avatar": group.photo,
                        "initials": initials,
                        "type": "group",
                        "registered": stats["registered"],
                        "attended": stats["attended"],
                    })

            # Sort by attended count descending
            clubs_result.sort(key=lambda x: x["attended"], reverse=True)

            # Build sports stats
            sports_result = []
            for sport_type, count in sport_counts.items():
                if sport_type in SPORT_NAMES:
                    sport_id, name, icon = SPORT_NAMES[sport_type]
                    sports_result.append({
                        "id": sport_id,
                        "icon": icon,
                        "name": name,
                        "count": count,
                    })

            # Sort by count descending
            sports_result.sort(key=lambda x: x["count"], reverse=True)

            # Calculate attendance rate
            attendance_rate = (
                round(total_attended / total_registered * 100)
                if total_registered > 0
                else 0
            )

            return {
                "period": period,
                "registered": total_registered,
                "attended": total_attended,
                "attendance_rate": attendance_rate,
                "clubs": clubs_result,
                "sports": sports_result,
            }

        except Exception as e:
            logger.error(f"Error in get_detailed_stats: {e}")
            return {
                "period": period,
                "registered": 0,
                "attended": 0,
                "attendance_rate": 0,
                "clubs": [],
                "sports": [],
            }
