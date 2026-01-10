"""
Club Storage Layer

Provides high-level interface for club-related database operations.
Used by both Telegram bot and FastAPI endpoints.
"""

from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
import logging

from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from storage.db import SessionLocal, Club, Membership, MembershipStatus, Group, UserRole

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
            from storage.db import Group, Activity
            groups_count = self.session.query(func.count(Group.id)).filter(
                Group.club_id == club_id
            ).scalar() or 0

            # Count activities
            activities_count = self.session.query(func.count(Activity.id)).filter(
                Activity.club_id == club_id
            ).scalar() or 0

            return {
                'id': club.id,
                'name': club.name,
                'description': club.description or '',
                'member_count': member_count,
                'groups_count': groups_count,
                'activities_count': activities_count,
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
                    'contact': '@username',
                    'is_open': True
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
                contact=data.get('contact'),
                is_open=data.get('is_open', True)
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

    def update_club_request_status(self, request_id: str, status: 'ClubRequestStatus') -> bool:
        """
        Update club request status.

        Args:
            request_id: ClubRequest UUID
            status: New status

        Returns:
            True if successful, False otherwise
        """
        try:
            from storage.db import ClubRequest

            request = self.session.query(ClubRequest).filter(
                ClubRequest.id == request_id
            ).first()

            if not request:
                return False

            request.status = status
            request.updated_at = datetime.utcnow()
            self.session.commit()
            logger.info(f"Updated club request {request_id} status to {status}")
            return True

        except Exception as e:
            self.session.rollback()
            logger.error(f"Error in update_club_request_status: {e}")
            return False

    def get_club_by_telegram_chat_id(self, chat_id: int) -> Optional[Club]:
        """
        Получить клуб по telegram_chat_id

        Args:
            chat_id: Telegram chat ID группы

        Returns:
            Club или None
        """
        try:
            return self.session.query(Club).filter(
                Club.telegram_chat_id == chat_id
            ).first()
        except Exception as e:
            logger.error(f"Error in get_club_by_telegram_chat_id: {e}")
            return None

    def create_club_from_telegram_group(
        self,
        creator_id: str,
        group_data: dict,
        sports: List[str],
        is_open: bool = True
    ) -> Club:
        """
        Создать клуб на основе данных Telegram группы

        Args:
            creator_id: ID пользователя-создателя
            group_data: Данные из TelegramGroupParser
                {
                    'chat_id': int,
                    'title': str,
                    'description': str,
                    'username': str,
                    'member_count': int,
                    'invite_link': str,
                    'photo': str,
                    'type': str,
                }
            sports: Выбранные виды спорта
            is_open: Открыт ли клуб для вступления

        Returns:
            Club: Созданный клуб

        Raises:
            ValueError: Если группа уже связана с клубом
        """
        try:
            # Проверить, что группа не связана с другим клубом
            existing_club = self.get_club_by_telegram_chat_id(group_data['chat_id'])
            if existing_club:
                raise ValueError(f"Группа уже связана с клубом {existing_club.name}")

            import json

            # Создать клуб
            club = Club(
                name=group_data['title'],
                description=group_data.get('description') or '',
                creator_id=creator_id,
                username=group_data.get('username'),
                telegram_chat_id=group_data['chat_id'],
                invite_link=group_data.get('invite_link'),
                photo=group_data.get('photo'),
                city='Almaty',  # TODO: определять из группы или пользователя
                is_open=is_open,
            )

            self.session.add(club)
            self.session.commit()
            self.session.refresh(club)

            logger.info(f"Created club {club.id} from Telegram group {group_data['chat_id']}")
            return club

        except ValueError:
            raise
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error in create_club_from_telegram_group: {e}")
            raise

    # ============= Sync methods =============

    def update_telegram_member_count(self, club_id: str, count: int) -> None:
        """
        Update Telegram member count from API.

        Args:
            club_id: Club UUID
            count: Member count from Telegram API
        """
        try:
            self.session.query(Club).filter(Club.id == club_id).update({
                "telegram_member_count": count,
                "last_sync_at": datetime.utcnow()
            })
            self.session.commit()
            logger.info(f"Updated telegram_member_count for club {club_id}: {count}")
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error updating telegram_member_count: {e}")

    def mark_sync_completed(self, club_id: str) -> None:
        """
        Mark sync as completed for club.

        Args:
            club_id: Club UUID
        """
        try:
            self.session.query(Club).filter(Club.id == club_id).update({
                "sync_completed": True,
                "last_sync_at": datetime.utcnow()
            })
            self.session.commit()
            logger.info(f"Marked sync completed for club {club_id}")
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error marking sync completed: {e}")

    def reset_sync_status(self, club_id: str) -> None:
        """
        Reset sync status (when new members detected in TG).

        Args:
            club_id: Club UUID
        """
        try:
            self.session.query(Club).filter(Club.id == club_id).update({
                "sync_completed": False
            })
            self.session.commit()
            logger.info(f"Reset sync status for club {club_id}")
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error resetting sync status: {e}")

    def update_bot_admin_status(self, club_id: str, is_admin: bool) -> None:
        """
        Update bot admin status for club.

        Args:
            club_id: Club UUID
            is_admin: Whether bot is admin in the group
        """
        try:
            self.session.query(Club).filter(Club.id == club_id).update({
                "bot_is_admin": is_admin
            })
            self.session.commit()
            logger.info(f"Updated bot_is_admin for club {club_id}: {is_admin}")
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error updating bot_is_admin: {e}")

    def find_similar_entities_for_user(
        self,
        user_id: str,
        tg_group_name: str,
        similarity_threshold: float = 0.6
    ) -> List[Dict[str, Any]]:
        """
        Find clubs and groups created by user that have similar names to the Telegram group.

        Args:
            user_id: User UUID (creator)
            tg_group_name: Name of the Telegram group
            similarity_threshold: Minimum similarity score (0-1) to consider as match

        Returns:
            List of matching entities:
            [
                {
                    'type': 'club' | 'group',
                    'id': 'uuid',
                    'name': 'Entity Name',
                    'member_count': 10,
                    'has_telegram': True/False,  # Already linked to Telegram
                    'similarity': 0.85
                }
            ]
        """
        try:
            results = []
            tg_name_lower = tg_group_name.lower().strip()

            # Get user's clubs (where they are creator or organizer)
            clubs = self.session.query(Club).filter(
                or_(
                    Club.creator_id == user_id,
                    Club.id.in_(
                        self.session.query(Membership.club_id).filter(
                            Membership.user_id == user_id,
                            Membership.role == UserRole.ORGANIZER,
                            Membership.club_id.isnot(None)
                        )
                    )
                )
            ).all()

            for club in clubs:
                similarity = self._calculate_similarity(tg_name_lower, club.name.lower())
                if similarity >= similarity_threshold:
                    member_count = self.session.query(func.count(Membership.id)).filter(
                        Membership.club_id == club.id
                    ).scalar() or 0

                    results.append({
                        'type': 'club',
                        'id': club.id,
                        'name': club.name,
                        'member_count': member_count,
                        'has_telegram': club.telegram_chat_id is not None,
                        'similarity': similarity
                    })

            # Get user's groups (where they are creator or organizer)
            groups = self.session.query(Group).filter(
                or_(
                    Group.creator_id == user_id,
                    Group.id.in_(
                        self.session.query(Membership.group_id).filter(
                            Membership.user_id == user_id,
                            Membership.role == UserRole.ORGANIZER,
                            Membership.group_id.isnot(None)
                        )
                    )
                )
            ).all()

            for group in groups:
                similarity = self._calculate_similarity(tg_name_lower, group.name.lower())
                if similarity >= similarity_threshold:
                    member_count = self.session.query(func.count(Membership.id)).filter(
                        Membership.group_id == group.id
                    ).scalar() or 0

                    results.append({
                        'type': 'group',
                        'id': group.id,
                        'name': group.name,
                        'member_count': member_count,
                        'has_telegram': group.telegram_chat_id is not None,
                        'club_name': group.club.name if group.club else None,
                        'similarity': similarity
                    })

            # Sort by similarity (descending)
            results.sort(key=lambda x: x['similarity'], reverse=True)

            return results

        except Exception as e:
            logger.error(f"Error in find_similar_entities_for_user: {e}")
            return []

    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """
        Calculate similarity between two strings.
        Uses a combination of containment and character-level similarity.

        Args:
            str1: First string (lowercase)
            str2: Second string (lowercase)

        Returns:
            Similarity score (0-1)
        """
        # Exact match
        if str1 == str2:
            return 1.0

        # One contains the other
        if str1 in str2 or str2 in str1:
            return 0.9

        # Word overlap
        words1 = set(str1.split())
        words2 = set(str2.split())
        if words1 and words2:
            overlap = len(words1 & words2)
            total = len(words1 | words2)
            if overlap > 0:
                return 0.7 + (0.2 * overlap / total)

        # Character-level Jaccard similarity
        chars1 = set(str1)
        chars2 = set(str2)
        if chars1 and chars2:
            intersection = len(chars1 & chars2)
            union = len(chars1 | chars2)
            return intersection / union

        return 0.0

    def link_telegram_chat_to_club(self, club_id: str, chat_id: int, member_count: int = 0) -> bool:
        """
        Link a Telegram chat to an existing club.

        Args:
            club_id: Club UUID
            chat_id: Telegram chat ID
            member_count: Number of members in TG group

        Returns:
            True if successful, False otherwise
        """
        try:
            club = self.session.query(Club).filter(Club.id == club_id).first()
            if not club:
                logger.error(f"Club {club_id} not found")
                return False

            if club.telegram_chat_id:
                logger.warning(f"Club {club_id} already linked to chat {club.telegram_chat_id}")
                return False

            club.telegram_chat_id = chat_id
            club.telegram_member_count = member_count
            club.last_sync_at = datetime.utcnow()

            self.session.commit()
            logger.info(f"Linked club {club_id} to Telegram chat {chat_id}")
            return True

        except Exception as e:
            self.session.rollback()
            logger.error(f"Error in link_telegram_chat_to_club: {e}")
            return False

    def link_telegram_chat_to_group(self, group_id: str, chat_id: int) -> bool:
        """
        Link a Telegram chat to an existing group.

        Args:
            group_id: Group UUID
            chat_id: Telegram chat ID

        Returns:
            True if successful, False otherwise
        """
        try:
            group = self.session.query(Group).filter(Group.id == group_id).first()
            if not group:
                logger.error(f"Group {group_id} not found")
                return False

            if group.telegram_chat_id:
                logger.warning(f"Group {group_id} already linked to chat {group.telegram_chat_id}")
                return False

            group.telegram_chat_id = chat_id

            self.session.commit()
            logger.info(f"Linked group {group_id} to Telegram chat {chat_id}")
            return True

        except Exception as e:
            self.session.rollback()
            logger.error(f"Error in link_telegram_chat_to_group: {e}")
            return False

    def get_group_by_telegram_chat_id(self, chat_id: int) -> Optional[Group]:
        """
        Get group by telegram_chat_id.

        Args:
            chat_id: Telegram chat ID

        Returns:
            Group or None
        """
        try:
            return self.session.query(Group).filter(
                Group.telegram_chat_id == chat_id
            ).first()
        except Exception as e:
            logger.error(f"Error in get_group_by_telegram_chat_id: {e}")
            return None
