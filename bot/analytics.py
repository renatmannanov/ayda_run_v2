"""
Analytics tracking for Telegram Bot events.

Tracks onboarding steps and other bot-related events.
"""
import logging
from typing import Optional
from storage.db import SessionLocal
from storage.analytics_storage import AnalyticsStorage

logger = logging.getLogger(__name__)


def track_bot_event(
    event_name: str,
    user_id: Optional[str] = None,
    event_params: Optional[dict] = None
) -> None:
    """
    Track an analytics event from the bot.
    Fire and forget - errors are logged but don't interrupt the flow.

    Args:
        event_name: Name of the event
        user_id: Internal user ID (UUID string)
        event_params: Additional parameters
    """
    try:
        db = SessionLocal()
        try:
            storage = AnalyticsStorage(session=db)
            storage.track_event(
                event_name=event_name,
                user_id=user_id,
                event_params=event_params
            )
        finally:
            db.close()
    except Exception as e:
        logger.debug(f"Failed to track bot event {event_name}: {e}")


def track_onboarding_step(user_id: str, step_name: str, step_number: int) -> None:
    """
    Track an onboarding step completion.

    Args:
        user_id: Internal user ID
        step_name: Name of the step (consent, photo_visibility, sports, role, intro)
        step_number: Step number (1-5)
    """
    track_bot_event(
        event_name="onboarding_step",
        user_id=user_id,
        event_params={
            "step_name": step_name,
            "step_number": step_number
        }
    )


def track_onboarding_complete(user_id: str) -> None:
    """Track onboarding completion."""
    track_bot_event(
        event_name="onboarding_complete",
        user_id=user_id
    )
