"""
Strava Activity Matching Service

Matches incoming Strava activities to Ayda Run activities:
1. Receives Strava activity ID from webhook
2. Fetches activity details from Strava API
3. Finds matching Ayda activity by time window (+-1h) and distance (+-5km)
4. Creates PendingStravaMatch for user confirmation via bot

Confidence levels:
- "high": user has participation in matching activity
- "medium": user is member of group/club with matching activity (scenario C)
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple

from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy.orm import Session

from storage.db import (
    SessionLocal, User, Activity, Participation, Membership,
    MembershipStatus, ActivityStatus, ParticipationStatus,
    StravaWebhookEvent, PendingStravaMatch
)
from app.services.strava_service import StravaService
from app.core.timezone import ensure_utc_from_db

logger = logging.getLogger(__name__)

# Matching constants
TIME_WINDOW_HOURS = 1
DISTANCE_TOLERANCE_KM = 5
MAX_RETRY_COUNT = 3


def find_matching_activity(
    db: Session,
    user_id: str,
    strava_activity: dict
) -> Tuple[Optional[Activity], str]:
    """
    Match Strava activity to Ayda activity.

    Args:
        db: Database session
        user_id: Ayda user ID
        strava_activity: Strava activity data dict

    Returns:
        Tuple of (Activity or None, confidence: "high"|"medium"|"")
    """
    strava_start_str = strava_activity.get("start_date_local") or strava_activity.get("start_date")
    if not strava_start_str:
        logger.warning(f"Strava activity {strava_activity.get('id')} has no start_date")
        return None, ""

    # Parse Strava datetime (ISO 8601)
    try:
        strava_start = datetime.fromisoformat(strava_start_str.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        logger.warning(f"Cannot parse Strava start_date: {strava_start_str}")
        return None, ""

    strava_distance_km = strava_activity.get("distance", 0) / 1000

    # Time window: +-1 hour (as naive UTC for DB comparison)
    time_min = strava_start.replace(tzinfo=None) - timedelta(hours=TIME_WINDOW_HOURS)
    time_max = strava_start.replace(tzinfo=None) + timedelta(hours=TIME_WINDOW_HOURS)

    # === High confidence: user has participation ===
    participations = db.query(Participation).join(Activity).filter(
        Participation.user_id == user_id,
        Activity.date.between(time_min, time_max),
        Activity.status == ActivityStatus.COMPLETED
    ).all()

    for p in participations:
        activity = p.activity
        if activity.distance and strava_distance_km > 0:
            if abs(activity.distance - strava_distance_km) > DISTANCE_TOLERANCE_KM:
                continue
        return activity, "high"

    # === Medium confidence: user is member of group/club with activity ===
    active_memberships = db.query(Membership).filter(
        Membership.user_id == user_id,
        Membership.status == MembershipStatus.ACTIVE
    ).all()

    group_ids = [m.group_id for m in active_memberships if m.group_id]
    club_ids = [m.club_id for m in active_memberships if m.club_id]

    if group_ids or club_ids:
        query = db.query(Activity).filter(
            Activity.date.between(time_min, time_max),
            Activity.status == ActivityStatus.COMPLETED
        )

        from sqlalchemy import or_
        conditions = []
        if group_ids:
            conditions.append(Activity.group_id.in_(group_ids))
        if club_ids:
            conditions.append(Activity.club_id.in_(club_ids))
        query = query.filter(or_(*conditions))

        activities = query.all()
        for activity in activities:
            # Skip if user already has participation (would have matched above)
            existing = db.query(Participation).filter(
                Participation.activity_id == activity.id,
                Participation.user_id == user_id
            ).first()
            if existing:
                continue

            if activity.distance and strava_distance_km > 0:
                if abs(activity.distance - strava_distance_km) > DISTANCE_TOLERANCE_KM:
                    continue
            return activity, "medium"

    return None, ""


async def process_strava_activity(
    bot: Bot,
    user_id: str,
    strava_activity_id: int,
    webhook_event_id: int
):
    """
    Process incoming Strava activity: fetch details, find match, send confirmation.

    Args:
        bot: Telegram Bot instance
        user_id: Ayda user ID
        strava_activity_id: Strava activity ID
        webhook_event_id: StravaWebhookEvent ID for status tracking
    """
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            _update_event_result(db, webhook_event_id, "error")
            return

        # Fetch activity details from Strava API
        strava_service = StravaService(db)
        strava_activity = await strava_service.get_activity(user, strava_activity_id)

        if strava_activity is None:
            # API unavailable or rate limited — schedule retry
            _schedule_retry(db, webhook_event_id)
            logger.warning(f"Strava API unavailable, scheduled retry for activity {strava_activity_id}")
            return

        # Find matching Ayda activity
        activity, confidence = find_matching_activity(db, user_id, strava_activity)

        if not activity:
            _update_event_result(db, webhook_event_id, "no_match")
            logger.info(f"No match for Strava activity {strava_activity_id}, user {user_id}")
            return

        # Check if participation already has a link (high confidence only)
        if confidence == "high":
            participation = db.query(Participation).filter(
                Participation.activity_id == activity.id,
                Participation.user_id == user_id
            ).first()
            if participation and participation.training_link:
                _update_event_result(db, webhook_event_id, "already_linked")
                logger.info(f"Activity {activity.id} already has link for user {user_id}")
                return

        # Create PendingStravaMatch for user confirmation
        match = PendingStravaMatch(
            user_id=user_id,
            activity_id=activity.id,
            strava_activity_id=strava_activity_id,
            strava_activity_data=json.dumps({
                "id": strava_activity.get("id"),
                "name": strava_activity.get("name", ""),
                "distance": strava_activity.get("distance", 0),
                "moving_time": strava_activity.get("moving_time", 0),
                "type": strava_activity.get("type", ""),
                "start_date_local": strava_activity.get("start_date_local", ""),
            }),
            confidence=confidence,
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        db.add(match)
        db.commit()

        # Send confirmation message to user
        await _send_match_confirmation(bot, user, activity, strava_activity, match)
        _update_event_result(db, webhook_event_id, "matched")

        logger.info(
            f"Matched Strava activity {strava_activity_id} → "
            f"Ayda activity {activity.id} ({confidence}) for user {user_id}"
        )

    except Exception as e:
        logger.error(f"Error processing Strava activity {strava_activity_id}: {e}", exc_info=True)
        try:
            _update_event_result(db, webhook_event_id, "error")
        except Exception:
            pass
    finally:
        db.close()


async def _send_match_confirmation(
    bot: Bot,
    user: User,
    activity: Activity,
    strava_activity: dict,
    match: PendingStravaMatch
):
    """Send Strava match confirmation message to user via bot."""
    strava_link = f"https://strava.com/activities/{strava_activity['id']}"
    distance_km = strava_activity.get("distance", 0) / 1000
    strava_name = strava_activity.get("name", "")
    short_id = match.id[:8]

    if match.confidence == "high":
        text = (
            f"🏃 Нашли твою тренировку!\n\n"
            f"«{strava_name}» — {distance_km:.1f} км\n"
            f"Совпадает с «{activity.title}»\n\n"
            f"[Открыть в Strava]({strava_link})"
        )
        keyboard = [[
            InlineKeyboardButton("✅ Подтвердить", callback_data=f"sc_{short_id}"),
            InlineKeyboardButton("❌ Другая", callback_data=f"sr_{short_id}")
        ]]
    else:
        text = (
            f"🏃 Похоже, ты был(а) на тренировке!\n\n"
            f"«{strava_name}» — {distance_km:.1f} км\n"
            f"Совпадает с «{activity.title}»\n\n"
            f"[Открыть в Strava]({strava_link})"
        )
        keyboard = [[
            InlineKeyboardButton("✅ Да, я был(а)", callback_data=f"si_{short_id}"),
            InlineKeyboardButton("❌ Нет", callback_data=f"sr_{short_id}")
        ]]

    try:
        await bot.send_message(
            chat_id=user.telegram_id,
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Failed to send Strava match confirmation to user {user.id}: {e}")


def _update_event_result(db: Session, event_id: int, result: str):
    """Update StravaWebhookEvent result."""
    event = db.query(StravaWebhookEvent).filter(StravaWebhookEvent.id == event_id).first()
    if event:
        event.result = result
        event.processed_at = datetime.utcnow()
        db.commit()


def _schedule_retry(db: Session, event_id: int):
    """Schedule retry for failed Strava API call."""
    event = db.query(StravaWebhookEvent).filter(StravaWebhookEvent.id == event_id).first()
    if event:
        event.result = "pending_retry"
        event.retry_count = (event.retry_count or 0) + 1
        event.next_retry_at = datetime.utcnow() + timedelta(minutes=15 * event.retry_count)
        db.commit()
