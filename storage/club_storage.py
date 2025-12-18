"""
Club Storage Layer

Provides high-level interface for club-related database operations.
Used by both Telegram bot and FastAPI endpoints.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from sqlalchemy.orm import Session
from sqlalchemy import func
from storage.db import SessionLocal, Club, Membership

logger = logging.getLogger(__name__)


class ClubStorage:
    """
    Storage class for Club operations with context manager support.

    Usage:
        # Bot usage (creates own session)
        with ClubStorage() as club_storage:
            club = club_storage.get_club_by_id(club_id)

        # FastAPI usage (uses provided session)
        club_storage = ClubStorage(session=db)
        preview = club_storage.get_club_preview(club_id)
    """

    def __init__(self, session: Optional[Session] = None):
        """
        Initialize ClubStorage.

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

    def get_club_by_id(self, club_id: str) -> Optional[Club]:
        """
        Get club by UUID.

        Args:
            club_id: Club UUID

        Returns:
            Club object or None if not found
        """
        try:
            return self.session.query(Club).filter(Club.id == club_id).first()
        except Exception as e:
            logger.error(f"Error in get_club_by_id: {e}")
            return None

    def get_club_preview(self, club_id: str) -> Optional[Dict[str, Any]]:
        """
        Get club preview data for invitation messages.

        Args:
            club_id: Club UUID

        Returns:
            Dictionary with club preview data or None if not found
            {
                'id': 'uuid',
                'name': 'Club Name',
                'description': 'Club description',
                'member_count': 80,
                'groups_count': 3
            }
        """
        try:
            club = self.session.query(Club).filter(Club.id == club_id).first()
            if not club:
                return None

            # Count members
            member_count = self.session.query(func.count(Membership.id)).filter(
                Membership.club_id == club_id
            ).scalar() or 0

            # Count groups
            from storage.db import Group
            groups_count = self.session.query(func.count(Group.id)).filter(
                Group.club_id == club_id
            ).scalar() or 0

            return {
                'id': club.id,
                'name': club.name,
                'description': club.description or '',
                'member_count': member_count,
                'groups_count': groups_count,
                'city': club.city,
                'photo': club.photo
            }

        except Exception as e:
            logger.error(f"Error in get_club_preview: {e}")
            return None

    def create_club_request(self, data: Dict[str, Any]) -> Optional['ClubRequest']:
        """
        Create a new club request (for organizers).

        Args:
            data: Dictionary with club request data
                {
                    'user_id': 'uuid',
                    'name': 'Club Name',
                    'description': 'Description',
                    'sports': ['RUNNING', 'TRAIL'],
                    'members_count': 120,
                    'groups_count': 4,
                    'telegram_group_link': 'https://t.me/...',
                    'contact': '@username'
                }

        Returns:
            ClubRequest object or None if error
        """
        try:
            from storage.db import ClubRequest
            import json

            request = ClubRequest(
                user_id=data['user_id'],
                name=data['name'],
                description=data.get('description'),
                sports=json.dumps(data.get('sports', [])),
                members_count=data.get('members_count'),
                groups_count=data.get('groups_count'),
                telegram_group_link=data.get('telegram_group_link'),
                contact=data.get('contact')
            )
            self.session.add(request)
            self.session.commit()
            self.session.refresh(request)
            logger.info(f"Created club request: {request.id}")
            return request

        except Exception as e:
            self.session.rollback()
            logger.error(f"Error in create_club_request: {e}")
            return None

    def get_pending_requests(self) -> List['ClubRequest']:
        """
        Get all pending club requests.

        Returns:
            List of ClubRequest objects
        """
        try:
            from storage.db import ClubRequest, ClubRequestStatus

            return self.session.query(ClubRequest).filter(
                ClubRequest.status == ClubRequestStatus.PENDING
            ).order_by(ClubRequest.created_at.desc()).all()

        except Exception as e:
            logger.error(f"Error in get_pending_requests: {e}")
            return []

    def get_club_request_by_id(self, request_id: str) -> Optional['ClubRequest']:
        """
        Get club request by ID.

        Args:
            request_id: ClubRequest UUID

        Returns:
            ClubRequest object or None if not found
        """
        try:
            from storage.db import ClubRequest

            return self.session.query(ClubRequest).filter(
                ClubRequest.id == request_id
            ).first()

        except Exception as e:
            logger.error(f"Error in get_club_request_by_id: {e}")
            return None

    def approve_club_request(self, request_id: str) -> bool:
        """
        Approve club request and create actual club.

        Args:
            request_id: ClubRequest UUID

        Returns:
            True if successful, False otherwise
        """
        try:
            from storage.db import ClubRequest, ClubRequestStatus

            request = self.session.query(ClubRequest).filter(
                ClubRequest.id == request_id
            ).first()

            if not request:
                return False

            # Create actual club
            club = Club(
                name=request.name,
                description=request.description,
                creator_id=request.user_id,
                city=request.city if hasattr(request, 'city') else 'Almaty'
            )
            self.session.add(club)

            # Update request status
            request.status = ClubRequestStatus.APPROVED
            request.updated_at = datetime.utcnow()

            self.session.commit()
            logger.info(f"Approved club request {request_id}, created club {club.id}")
            return True

        except Exception as e:
            self.session.rollback()
            logger.error(f"Error in approve_club_request: {e}")
            return False

    def reject_club_request(self, request_id: str) -> bool:
        """
        Reject club request.

        Args:
            request_id: ClubRequest UUID

        Returns:
            True if successful, False otherwise
        """
        try:
            from storage.db import ClubRequest, ClubRequestStatus

            request = self.session.query(ClubRequest).filter(
                ClubRequest.id == request_id
            ).first()

            if not request:
                return False

            request.status = ClubRequestStatus.REJECTED
            request.updated_at = datetime.utcnow()
            self.session.commit()
            logger.info(f"Rejected club request {request_id}")
            return True

        except Exception as e:
            self.session.rollback()
            logger.error(f"Error in reject_club_request: {e}")
            return False
