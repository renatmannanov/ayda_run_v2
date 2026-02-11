"""
Send Telegram message to production users from local machine.

Usage:
    # Send to specific users by telegram_id:
    python scripts/send_message.py --users 1082768332 930226366 205836252 1041924294

    # Send to all users who were spammed today (post_training_notifications sent on date):
    python scripts/send_message.py --spammed-on 2026-02-11

    # Dry run (show who would receive, don't actually send):
    python scripts/send_message.py --users 1082768332 --dry-run

    # Custom message (default is apology):
    python scripts/send_message.py --users 1082768332 --message "Привет! Тестовое сообщение."

Requires PROD_DATABASE_URL and TELEGRAM_BOT_TOKEN in .env
"""

import argparse
import asyncio
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

import sqlalchemy as sa
from telegram import Bot
from telegram.error import TelegramError


PROD_DB_URL = os.environ.get("PROD_DATABASE_URL", "")
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")

DEFAULT_APOLOGY_MESSAGE = (
    "Привет! 👋\n\n"
    "Извини за спам сообщениями сегодня — произошёл технический сбой, "
    "из-за которого уведомления отправлялись повторно.\n\n"
    "Мы уже всё починили. Спасибо за понимание! 🙏"
)


def get_prod_engine():
    """Create SQLAlchemy engine for prod database."""
    if not PROD_DB_URL:
        print("ERROR: PROD_DATABASE_URL not set in .env")
        sys.exit(1)

    url = PROD_DB_URL
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)

    return sa.create_engine(url)


def find_spammed_users(engine, date_str: str) -> list[dict]:
    """Find users who received post_training_notifications on a given date."""
    query = sa.text("""
        SELECT DISTINCT u.id, u.first_name, u.username, u.telegram_id,
               COUNT(ptn.id) as notification_count
        FROM post_training_notifications ptn
        JOIN users u ON u.id = ptn.user_id
        WHERE DATE(ptn.sent_at) = :target_date
        GROUP BY u.id, u.first_name, u.username, u.telegram_id
        ORDER BY notification_count DESC
    """)

    with engine.connect() as conn:
        rows = conn.execute(query, {"target_date": date_str}).fetchall()

    return [
        {
            "id": str(row[0]),
            "first_name": row[1],
            "username": row[2],
            "telegram_id": row[3],
            "notification_count": row[4],
        }
        for row in rows
    ]


def find_users_by_telegram_ids(engine, telegram_ids: list[int]) -> list[dict]:
    """Find users by their telegram IDs."""
    placeholders = ", ".join(f":tid_{i}" for i in range(len(telegram_ids)))
    query = sa.text(f"""
        SELECT id, first_name, username, telegram_id
        FROM users
        WHERE telegram_id IN ({placeholders})
    """)

    params = {f"tid_{i}": tid for i, tid in enumerate(telegram_ids)}

    with engine.connect() as conn:
        rows = conn.execute(query, params).fetchall()

    return [
        {
            "id": str(row[0]),
            "first_name": row[1],
            "username": row[2],
            "telegram_id": row[3],
        }
        for row in rows
    ]


async def send_messages(bot_token: str, users: list[dict], message: str, dry_run: bool = False):
    """Send message to list of users via Telegram bot."""
    if not bot_token:
        print("ERROR: TELEGRAM_BOT_TOKEN not set in .env")
        return

    bot = Bot(token=bot_token)

    print(f"\n{'=' * 50}")
    print(f"{'DRY RUN — ' if dry_run else ''}Sending to {len(users)} user(s):")
    print(f"{'=' * 50}")

    for user in users:
        name = user.get("first_name") or user.get("username") or "Unknown"
        tid = user["telegram_id"]
        count_info = f" (notifications: {user['notification_count']})" if "notification_count" in user else ""
        print(f"  - {name} (telegram_id: {tid}){count_info}")

    print(f"\nMessage:\n{message}\n")

    if dry_run:
        print("DRY RUN — no messages sent.")
        return

    # Confirmation
    confirm = input("Send? [y/N]: ").strip().lower()
    if confirm != "y":
        print("Cancelled.")
        return

    success = 0
    failed = 0

    for user in users:
        name = user.get("first_name") or user.get("username") or "Unknown"
        tid = user["telegram_id"]

        try:
            await bot.send_message(chat_id=tid, text=message)
            print(f"  ✓ Sent to {name} ({tid})")
            success += 1
        except TelegramError as e:
            print(f"  ✗ Failed for {name} ({tid}): {e}")
            failed += 1

        # Small delay to avoid rate limiting
        await asyncio.sleep(0.1)

    print(f"\nDone: {success} sent, {failed} failed.")


def main():
    parser = argparse.ArgumentParser(description="Send Telegram message to prod users")
    parser.add_argument("--users", nargs="+", type=int, help="Telegram IDs of users to message")
    parser.add_argument("--spammed-on", type=str, help="Find users spammed on date (YYYY-MM-DD)")
    parser.add_argument("--message", type=str, default=DEFAULT_APOLOGY_MESSAGE, help="Message text")
    parser.add_argument("--dry-run", action="store_true", help="Show what would happen without sending")

    args = parser.parse_args()

    if not args.users and not args.spammed_on:
        parser.print_help()
        print("\nERROR: Specify --users or --spammed-on")
        sys.exit(1)

    engine = get_prod_engine()

    if args.spammed_on:
        users = find_spammed_users(engine, args.spammed_on)
        if not users:
            print(f"No spammed users found for date {args.spammed_on}")
            sys.exit(0)
    else:
        users = find_users_by_telegram_ids(engine, args.users)
        if not users:
            print("No users found with specified telegram IDs")
            sys.exit(0)

    asyncio.run(send_messages(BOT_TOKEN, users, args.message, args.dry_run))


if __name__ == "__main__":
    main()
