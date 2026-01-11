"""
Feedback Storage Module

Handles saving and retrieving user feedback messages.
"""

from sqlalchemy.orm import Session
from storage.db import Feedback, User
from typing import Optional
from datetime import datetime


def save_feedback(
    db: Session,
    telegram_id: int,
    message: str,
    message_id: Optional[int] = None,
    user_id: Optional[str] = None
) -> Feedback:
    """
    Save user feedback to database.

    Args:
        db: Database session
        telegram_id: User's Telegram ID
        message: Feedback message text
        message_id: Telegram message ID (optional)
        user_id: Internal user ID if user exists (optional)

    Returns:
        Created Feedback object
    """
    feedback = Feedback(
        telegram_id=telegram_id,
        user_id=user_id,
        message=message,
        message_id=message_id,
        created_at=datetime.utcnow()
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return feedback


def get_feedback_by_telegram_id(db: Session, telegram_id: int, limit: int = 50) -> list[Feedback]:
    """Get all feedback from a specific user."""
    return (
        db.query(Feedback)
        .filter(Feedback.telegram_id == telegram_id)
        .order_by(Feedback.created_at.desc())
        .limit(limit)
        .all()
    )


def get_recent_feedback(db: Session, limit: int = 100) -> list[Feedback]:
    """Get recent feedback messages."""
    return (
        db.query(Feedback)
        .order_by(Feedback.created_at.desc())
        .limit(limit)
        .all()
    )


def get_feedback_count(db: Session) -> int:
    """Get total feedback count."""
    return db.query(Feedback).count()
