"""
Strava API Service

Handles all Strava API interactions:
- OAuth token management (refresh on demand)
- Activity fetching
- Token encryption/decryption

Token refresh strategy: on-demand (not cron job).
Refresh token if expires in < 5 minutes before making API call.
Tokens are encrypted at rest using Fernet.
"""
import httpx
import logging
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session

from config import settings
from storage.db import User
from app.core.crypto import encrypt_token, decrypt_token

logger = logging.getLogger(__name__)


class StravaService:
    """
    Service for interacting with Strava API.

    Handles OAuth token refresh and API calls.
    """

    BASE_URL = "https://www.strava.com/api/v3"
    OAUTH_URL = "https://www.strava.com/oauth/token"
    TOKEN_REFRESH_BUFFER_MINUTES = 5

    def __init__(self, db: Session):
        """
        Initialize Strava service.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def get_decrypted_access_token(self, user: User) -> Optional[str]:
        """
        Get decrypted access token.

        Args:
            user: User model instance

        Returns:
            Decrypted access token or None
        """
        if not user.strava_access_token:
            return None
        try:
            return decrypt_token(user.strava_access_token)
        except Exception as e:
            logger.error(f"Failed to decrypt access token for user {user.id}: {e}")
            return None

    def get_decrypted_refresh_token(self, user: User) -> Optional[str]:
        """
        Get decrypted refresh token.

        Args:
            user: User model instance

        Returns:
            Decrypted refresh token or None
        """
        if not user.strava_refresh_token:
            return None
        try:
            return decrypt_token(user.strava_refresh_token)
        except Exception as e:
            logger.error(f"Failed to decrypt refresh token for user {user.id}: {e}")
            return None

    async def get_valid_token(self, user: User) -> Optional[str]:
        """
        Get valid access token, refreshing if needed.

        Args:
            user: User model instance

        Returns:
            Valid access token or None if refresh failed
        """
        if not user.strava_refresh_token:
            return None

        # Check if token expires soon (< 5 min)
        if user.strava_token_expires_at is None:
            # No expiration set, try to refresh
            success = await self._refresh_token(user)
            if not success:
                return None
        elif user.strava_token_expires_at < datetime.utcnow() + timedelta(minutes=self.TOKEN_REFRESH_BUFFER_MINUTES):
            success = await self._refresh_token(user)
            if not success:
                return None

        return self.get_decrypted_access_token(user)

    async def _refresh_token(self, user: User) -> bool:
        """
        Refresh expired token.

        Args:
            user: User model instance

        Returns:
            True if refresh succeeded, False otherwise
        """
        refresh_token = self.get_decrypted_refresh_token(user)
        if not refresh_token:
            logger.warning(f"No refresh token available for user {user.id}")
            return False

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    self.OAUTH_URL,
                    data={
                        "client_id": settings.strava_client_id,
                        "client_secret": settings.strava_client_secret,
                        "refresh_token": refresh_token,
                        "grant_type": "refresh_token"
                    },
                    timeout=30.0
                )

            if resp.status_code != 200:
                logger.error(f"Strava token refresh failed for user {user.id}: {resp.status_code} {resp.text}")
                return False

            data = resp.json()

            # Update tokens (encrypted)
            user.strava_access_token = encrypt_token(data["access_token"])
            user.strava_refresh_token = encrypt_token(data["refresh_token"])
            user.strava_token_expires_at = datetime.fromtimestamp(data["expires_at"])
            self.db.commit()

            logger.info(f"Refreshed Strava token for user {user.id}")
            return True

        except httpx.TimeoutException:
            logger.error(f"Strava token refresh timeout for user {user.id}")
            return False
        except Exception as e:
            logger.error(f"Error refreshing Strava token for user {user.id}: {e}")
            return False

    async def get_activity(self, user: User, activity_id: int) -> Optional[dict]:
        """
        Get activity details from Strava.

        Args:
            user: User model instance
            activity_id: Strava activity ID

        Returns:
            Activity data dict or None if failed
        """
        token = await self.get_valid_token(user)
        if not token:
            logger.warning(f"No valid token for user {user.id}")
            return None

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self.BASE_URL}/activities/{activity_id}",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=30.0
                )

            if resp.status_code == 404:
                logger.warning(f"Strava activity {activity_id} not found")
                return None

            if resp.status_code != 200:
                logger.error(f"Strava get_activity failed: {resp.status_code} {resp.text}")
                return None

            return resp.json()

        except httpx.TimeoutException:
            logger.error(f"Strava get_activity timeout for activity {activity_id}")
            return None
        except Exception as e:
            logger.error(f"Error getting Strava activity {activity_id}: {e}")
            return None

    async def get_athlete(self, user: User) -> Optional[dict]:
        """
        Get authenticated athlete info from Strava.

        Args:
            user: User model instance

        Returns:
            Athlete data dict or None if failed
        """
        token = await self.get_valid_token(user)
        if not token:
            return None

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self.BASE_URL}/athlete",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=30.0
                )

            if resp.status_code != 200:
                logger.error(f"Strava get_athlete failed: {resp.status_code}")
                return None

            return resp.json()

        except Exception as e:
            logger.error(f"Error getting Strava athlete: {e}")
            return None

    def save_tokens(self, user: User, token_data: dict) -> None:
        """
        Save OAuth tokens to user (encrypted).

        Args:
            user: User model instance
            token_data: Token response from Strava OAuth
        """
        user.strava_athlete_id = token_data["athlete"]["id"]
        user.strava_access_token = encrypt_token(token_data["access_token"])
        user.strava_refresh_token = encrypt_token(token_data["refresh_token"])
        user.strava_token_expires_at = datetime.fromtimestamp(token_data["expires_at"])
        self.db.commit()

        logger.info(f"Saved Strava tokens for user {user.id}, athlete_id={user.strava_athlete_id}")

    def clear_tokens(self, user: User) -> None:
        """
        Clear Strava tokens from user.

        Args:
            user: User model instance
        """
        athlete_id = user.strava_athlete_id
        user.strava_athlete_id = None
        user.strava_access_token = None
        user.strava_refresh_token = None
        user.strava_token_expires_at = None
        self.db.commit()

        logger.info(f"Cleared Strava tokens for user {user.id}, was athlete_id={athlete_id}")

    def is_connected(self, user: User) -> bool:
        """
        Check if user has Strava connected.

        Args:
            user: User model instance

        Returns:
            True if Strava is connected
        """
        return user.strava_athlete_id is not None
