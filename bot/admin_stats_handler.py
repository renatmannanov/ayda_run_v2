"""
Admin Stats Handler - Admin-only command for analytics summaries

Only the admin (defined by ADMIN_CHAT_ID) can see and use this command.
"""

import logging
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from config import settings
from storage.analytics_storage import AnalyticsStorage
from storage.db import SessionLocal

logger = logging.getLogger(__name__)


def is_admin(telegram_id: int) -> bool:
    """Check if user is admin based on ADMIN_CHAT_ID"""
    admin_id = settings.admin_chat_id
    if not admin_id:
        return False
    return str(telegram_id) == str(admin_id)


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /stats command - show analytics summary.

    Only visible to admin.
    """
    user = update.effective_user

    # Check if user is admin
    if not is_admin(user.id):
        # Silently ignore for non-admins (command not visible to them anyway)
        return

    try:
        # Get analytics data
        db = SessionLocal()
        try:
            analytics = AnalyticsStorage(db)

            # Today's stats
            today = datetime.utcnow()
            yesterday = today - timedelta(days=1)
            week_ago = today - timedelta(days=7)

            # DAU
            dau_today = analytics.get_dau(today)
            dau_yesterday = analytics.get_dau(yesterday)

            # Event counts for today
            today_start = today.replace(hour=0, minute=0, second=0, microsecond=0)
            today_events = analytics.get_event_counts(start_date=today_start)

            # Event counts for last 7 days
            week_events = analytics.get_event_counts(start_date=week_ago)

            # Screen views for last 7 days
            screen_views = analytics.get_screen_views(start_date=week_ago)
        finally:
            db.close()

        # Format message
        message = format_stats_message(
            dau_today=dau_today,
            dau_yesterday=dau_yesterday,
            today_events=today_events,
            week_events=week_events,
            screen_views=screen_views
        )

        await update.message.reply_text(message, parse_mode="HTML")

    except Exception as e:
        logger.error(f"Error in stats command: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ Ошибка при получении статистики. Проверь логи."
        )


def format_stats_message(
    dau_today: int,
    dau_yesterday: int,
    today_events: dict,
    week_events: dict,
    screen_views: dict
) -> str:
    """Format analytics data into readable message"""

    # DAU change indicator
    dau_change = ""
    if dau_yesterday > 0:
        diff = dau_today - dau_yesterday
        if diff > 0:
            dau_change = f" (+{diff})"
        elif diff < 0:
            dau_change = f" ({diff})"

    # Key events for today
    today_joins = today_events.get('activity_join', 0)
    today_creates = today_events.get('activity_create', 0)
    today_screens = today_events.get('screen_view', 0)

    # Key events for week
    week_joins = week_events.get('activity_join', 0)
    week_creates = week_events.get('activity_create', 0)
    week_cancels = week_events.get('activity_cancel', 0)
    week_club_joins = week_events.get('club_join', 0)
    week_group_joins = week_events.get('group_join', 0)

    # Top screens (sort by count, top 5)
    top_screens = sorted(screen_views.items(), key=lambda x: x[1], reverse=True)[:5]
    screens_text = "\n".join([f"  • {name}: {count}" for name, count in top_screens])
    if not screens_text:
        screens_text = "  (нет данных)"

    # Onboarding funnel (from week events)
    onboarding_start = week_events.get('onboarding_start', 0)
    onboarding_complete = week_events.get('onboarding_complete', 0)
    onboarding_rate = 0
    if onboarding_start > 0:
        onboarding_rate = round((onboarding_complete / onboarding_start) * 100)

    message = f"""📊 <b>Аналитика Ayda Run</b>

<b>Сегодня:</b>
👥 DAU: {dau_today}{dau_change}
📱 Просмотров экранов: {today_screens}
➕ Создано активностей: {today_creates}
✅ Присоединений: {today_joins}

<b>За 7 дней:</b>
➕ Создано активностей: {week_creates}
✅ Присоединений: {week_joins}
❌ Отмен: {week_cancels}
🏃 Присоединений к клубам: {week_club_joins}
👥 Присоединений к группам: {week_group_joins}

<b>Топ экранов (7 дней):</b>
{screens_text}

<b>Онбординг (7 дней):</b>
🚀 Начали: {onboarding_start}
✅ Завершили: {onboarding_complete}
📈 Конверсия: {onboarding_rate}%
"""

    return message


def get_admin_stats_handler():
    """Return the admin stats command handler"""
    return CommandHandler("stats", stats_command)
