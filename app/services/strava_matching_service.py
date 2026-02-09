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
from app.services.strava_service import StravaService, StravaAPIError
from app.core.timezone import ensure_utc_from_db, format_datetime_local
from bot.activity_notifications import get_sport_icon

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
    # Use start_date (UTC) for matching — Activity.date in DB is stored as naive UTC
    strava_start_str = strava_activity.get("start_date") or strava_activity.get("start_date_local")
    if not strava_start_str:
        logger.warning(f"Strava activity {strava_activity.get('id')} has no start_date")
        return None, ""

    # Parse Strava datetime (ISO 8601, e.g. "2026-02-09T08:50:00Z")
    try:
        strava_start = datetime.fromisoformat(strava_start_str.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        logger.warning(f"Cannot parse Strava start_date: {strava_start_str}")
        return None, ""

    strava_distance_km = strava_activity.get("distance", 0) / 1000

    # Time window: +-1 hour (as naive UTC for DB comparison)
    time_min = strava_start.replace(tzinfo=None) - timedelta(hours=TIME_WINDOW_HOURS)
    time_max = strava_start.replace(tzinfo=None) + timedelta(hours=TIME_WINDOW_HOURS)

    logger.info(
        f"Matching strava activity: start_utc={strava_start}, "
        f"distance={strava_distance_km:.1f}km, window=[{time_min}, {time_max}]"
    )

    # Match COMPLETED or UPCOMING activities (webhook can arrive before service marks COMPLETED)
    allowed_statuses = [ActivityStatus.COMPLETED, ActivityStatus.UPCOMING]

    # === High confidence: user has participation ===
    participations = db.query(Participation).join(Activity).filter(
        Participation.user_id == user_id,
        Activity.date.between(time_min, time_max),
        Activity.status.in_(allowed_statuses)
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
            Activity.status.in_(allowed_statuses)
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
        try:
            strava_activity = await strava_service.get_activity(user, strava_activity_id)
        except StravaAPIError as e:
            # API unavailable or rate limited — schedule retry
            _schedule_retry(db, webhook_event_id)
            logger.warning(f"Strava API error, scheduled retry for activity {strava_activity_id}: {e}")
            return

        if strava_activity is None:
            # Activity not found on Strava (404) — no point retrying
            _update_event_result(db, webhook_event_id, "not_found")
            logger.info(f"Strava activity {strava_activity_id} not found (404), skipping")
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
    match_id = match.id
    sport_icon = get_sport_icon(activity.sport_type)

    # Format Strava date for display
    strava_date_str = ""
    strava_date_local = strava_activity.get("start_date_local", "")
    if strava_date_local:
        try:
            strava_dt = datetime.fromisoformat(strava_date_local.replace("Z", "+00:00"))
            strava_date_str = strava_dt.strftime("%d %b · %H:%M")
        except (ValueError, AttributeError):
            pass

    # Build Strava activity line: 🔸 «Name» · date · distance
    strava_parts = [f"[{strava_name}]({strava_link})"]
    if strava_date_str:
        strava_parts.append(strava_date_str)
    strava_parts.append(f"{distance_km:.1f} км")
    strava_info = " · ".join(strava_parts)

    # Build our activity line: icon «Title» · date · location
    activity_date_str = ""
    if activity.date:
        activity_date_str = format_datetime_local(
            activity.date, activity.country, activity.city, "%d %b · %H:%M"
        )
    activity_parts = [f"«{activity.title}»"]
    if activity_date_str:
        activity_parts.append(activity_date_str)
    if activity.location:
        activity_parts.append(activity.location)
    activity_info = " · ".join(activity_parts)

    if match.confidence == "high":
        confidence_word = "_уверены_"
        callback_prefix = "sc_"
    else:
        confidence_word = "_кажется_"
        callback_prefix = "si_"

    text = (
        f"Получили твою тренировку от Strava.\n\n"
        f"🔸 {strava_info}\n"
        f"Мы {confidence_word}, что она совпадает с тренировкой\n"
        f"{sport_icon} {activity_info}"
    )
    keyboard = [[
        InlineKeyboardButton("✅ Подтвердить", callback_data=f"{callback_prefix}{match_id}"),
        InlineKeyboardButton("❌ Другая", callback_data=f"sr_{match_id}")
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
