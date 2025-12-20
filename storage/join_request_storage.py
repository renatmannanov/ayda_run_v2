"""
Join Request Storage Layer

Provides high-level interface for join request-related database operations.
Handles join requests for closed clubs, groups, and activities.
"""

from typing import Optional, List
from datetime import datetime, timedelta
import logging

from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from storage.db import SessionLocal, JoinRequest, JoinRequestStatus, User, Club, Group, Activity

logger = logging.getLogger(__name__)


class JoinRequestStorage:
    """
    Storage class for JoinRequest operations with context manager support.

    Usage:
        # Bot usage (creates own session)
        with JoinRequestStorage() as jr_storage:
            jr_storage.create_join_request(user_id, "club", club_id)

        # FastAPI usage (uses provided session)
        jr_storage = JoinRequestStorage(session=db)
        requests = jr_storage.get_pending_requests_for_club(club_id)
    """

    def __init__(self, session: Optional[Session] = None):
        """
        Initialize JoinRequestStorage.

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

    def create_join_request(
        self,
        user_id: str,
        entity_type: str,
        entity_id: str
    ) -> Optional[JoinRequest]:
        """
        Create a join request for a closed club/group/activity.

        Args:
            user_id: User UUID
            entity_type: "club", "group", or "activity"
            entity_id: Entity UUID

        Returns:
            JoinRequest object or None if already has pending request
        """
        try:
            # Check if pending request already exists
            existing = self.get_user_pending_request(user_id, entity_type, entity_id)
            if existing:
                logger.info(f"User {user_id} already has pending request for {entity_type} {entity_id}")
                return existing

            # Delete any rejected/expired requests to allow re-application
            self._delete_old_requests(user_id, entity_type, entity_id)

            # Create join request
            kwargs = {"user_id": user_id}
            if entity_type == "club":
                kwargs["club_id"] = entity_id
            elif entity_type == "group":
                kwargs["group_id"] = entity_id
            elif entity_type == "activity":
                kwargs["activity_id"] = entity_id
                # Set expiry to activity date (will be handled by auto-reject service)
            else:
                raise ValueError(f"Invalid entity_type: {entity_type}")

            join_request = JoinRequest(**kwargs)
            self.session.add(join_request)
            self.session.commit()
            self.session.refresh(join_request)

            logger.info(f"Created join request {join_request.id} for user {user_id} to {entity_type} {entity_id}")
            return join_request

        except Exception as e:
            logger.error(f"Error creating join request: {e}")
            self.session.rollback()
            return None

    def get_join_request(self, request_id: str) -> Optional[JoinRequest]:
        """
        Get join request by ID.

        Args:
            request_id: JoinRequest UUID

        Returns:
            JoinRequest object or None
        """
        try:
            return self.session.query(JoinRequest).filter(
                JoinRequest.id == request_id
            ).first()
        except Exception as e:
            logger.error(f"Error getting join request {request_id}: {e}")
            return None

    def get_user_pending_request(
        self,
        user_id: str,
        entity_type: str,
        entity_id: str
    ) -> Optional[JoinRequest]:
        """
        Get user's pending join request for specific entity.

        Args:
            user_id: User UUID
            entity_type: "club", "group", or "activity"
            entity_id: Entity UUID

        Returns:
            JoinRequest object or None
        """
        try:
            query = self.session.query(JoinRequest).filter(
                JoinRequest.user_id == user_id,
                JoinRequest.status == JoinRequestStatus.PENDING
            )

            if entity_type == "club":
                query = query.filter(JoinRequest.club_id == entity_id)
            elif entity_type == "group":
                query = query.filter(JoinRequest.group_id == entity_id)
            elif entity_type == "activity":
                query = query.filter(JoinRequest.activity_id == entity_id)

            return query.first()

        except Exception as e:
            logger.error(f"Error getting pending request for user {user_id}: {e}")
            return None

    def get_pending_requests_for_entity(
        self,
        entity_type: str,
        entity_id: str
    ) -> List[JoinRequest]:
        """
        Get all pending join requests for a specific entity.

        Args:
            entity_type: "club", "group", or "activity"
            entity_id: Entity UUID

        Returns:
            List of JoinRequest objects
        """
        try:
            query = self.session.query(JoinRequest).filter(
                JoinRequest.status == JoinRequestStatus.PENDING
            )

            if entity_type == "club":
                query = query.filter(JoinRequest.club_id == entity_id)
            elif entity_type == "group":
                query = query.filter(JoinRequest.group_id == entity_id)
            elif entity_type == "activity":
                query = query.filter(JoinRequest.activity_id == entity_id)

            return query.all()

        except Exception as e:
            logger.error(f"Error getting pending requests for {entity_type} {entity_id}: {e}")
            return []

    def update_request_status(
        self,
        request_id: str,
        status: JoinRequestStatus
    ) -> Optional[JoinRequest]:
        """
        Update join request status.

        Args:
            request_id: JoinRequest UUID
            status: New status

        Returns:
            Updated JoinRequest object or None
        """
        try:
            join_request = self.get_join_request(request_id)
            if not join_request:
                logger.warning(f"Join request {request_id} not found")
                return None

            join_request.status = status
            join_request.updated_at = datetime.utcnow()
            self.session.commit()
            self.session.refresh(join_request)

            logger.info(f"Updated join request {request_id} status to {status}")
            return join_request

        except Exception as e:
            logger.error(f"Error updating join request {request_id}: {e}")
            self.session.rollback()
            return None

    def get_expired_requests(self) -> List[JoinRequest]:
        """
        Get all requests that have expired (past expires_at date).

        Returns:
            List of expired JoinRequest objects
        """
        try:
            now = datetime.utcnow()
            return self.session.query(JoinRequest).filter(
                JoinRequest.status == JoinRequestStatus.PENDING,
                JoinRequest.expires_at.isnot(None),
                JoinRequest.expires_at < now
            ).all()

        except Exception as e:
            logger.error(f"Error getting expired requests: {e}")
            return []

    def set_expiry_for_past_activities(self) -> int:
        """
        Set expires_at for all pending activity join requests where activity date has passed.

        Returns:
            Number of requests marked for expiry
        """
        try:
            now = datetime.utcnow()

            # Get all pending activity join requests
            pending_requests = self.session.query(JoinRequest).filter(
                JoinRequest.status == JoinRequestStatus.PENDING,
                JoinRequest.activity_id.isnot(None)
            ).all()

            count = 0
            for request in pending_requests:
                # Get activity
                activity = self.session.query(Activity).filter(
                    Activity.id == request.activity_id
                ).first()

                if activity and activity.date < now:
                    request.expires_at = now  # Mark for immediate expiry
                    count += 1

            self.session.commit()
            logger.info(f"Marked {count} activity join requests for expiry")
            return count

        except Exception as e:
            logger.error(f"Error setting expiry for past activities: {e}")
            self.session.rollback()
            return 0

    def delete_request(self, request_id: str) -> bool:
        """
        Delete join request.

        Args:
            request_id: JoinRequest UUID

        Returns:
            True if deleted, False otherwise
        """
        try:
            join_request = self.get_join_request(request_id)
            if not join_request:
                return False

            self.session.delete(join_request)
            self.session.commit()
            logger.info(f"Deleted join request {request_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting join request {request_id}: {e}")
            self.session.rollback()
            return False

    def _delete_old_requests(
        self,
        user_id: str,
        entity_type: str,
        entity_id: str
    ) -> int:
        """
        Delete old rejected/expired requests to allow re-application.

        Args:
            user_id: User UUID
            entity_type: "club", "group", or "activity"
            entity_id: Entity UUID

        Returns:
            Number of deleted requests
        """
        try:
            query = self.session.query(JoinRequest).filter(
                JoinRequest.user_id == user_id,
                JoinRequest.status.in_([JoinRequestStatus.REJECTED, JoinRequestStatus.EXPIRED])
            )

            if entity_type == "club":
                query = query.filter(JoinRequest.club_id == entity_id)
            elif entity_type == "group":
                query = query.filter(JoinRequest.group_id == entity_id)
            elif entity_type == "activity":
                query = query.filter(JoinRequest.activity_id == entity_id)

            old_requests = query.all()
            count = len(old_requests)

            for req in old_requests:
                self.session.delete(req)

            if count > 0:
                self.session.commit()
                logger.info(f"Deleted {count} old rejected/expired requests for user {user_id}")

            return count

        except Exception as e:
            logger.error(f"Error deleting old requests: {e}")
            self.session.rollback()
            return 0
