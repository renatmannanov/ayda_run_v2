"""
Analytics Storage - handles analytics event persistence
"""
import json
from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from storage.db import AnalyticsEvent


class AnalyticsStorage:
    """Storage class for analytics events"""

    def __init__(self, session: Session):
        self.session = session

    def track_event(
        self,
        event_name: str,
        user_id: Optional[str] = None,
        event_params: Optional[dict] = None,
        session_id: Optional[str] = None
    ) -> AnalyticsEvent:
        """
        Track a single analytics event.

        Args:
            event_name: Name of the event (e.g., "screen_view", "activity_join")
            user_id: User ID (optional for anonymous events)
            event_params: Additional parameters as dict
            session_id: Session ID for grouping events

        Returns:
            Created AnalyticsEvent
        """
        event = AnalyticsEvent(
            event_name=event_name,
            user_id=user_id,
            event_params=json.dumps(event_params) if event_params else None,
            session_id=session_id
        )
        self.session.add(event)
        self.session.commit()
        self.session.refresh(event)
        return event

    def track_events_batch(
        self,
        events: List[dict],
        user_id: Optional[str] = None
    ) -> int:
        """
        Track multiple events in batch.

        Args:
            events: List of event dicts with event_name, event_params, session_id
            user_id: User ID to apply to all events

        Returns:
            Number of events created
        """
        db_events = []
        for event_data in events:
            event = AnalyticsEvent(
                event_name=event_data["event_name"],
                user_id=user_id,
                event_params=json.dumps(event_data.get("event_params")) if event_data.get("event_params") else None,
                session_id=event_data.get("session_id")
            )
            db_events.append(event)

        self.session.add_all(db_events)
        self.session.commit()
        return len(db_events)

    def get_events(
        self,
        user_id: Optional[str] = None,
        event_name: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 1000,
        offset: int = 0
    ) -> List[AnalyticsEvent]:
        """
        Get analytics events with filters.
        """
        query = self.session.query(AnalyticsEvent)

        if user_id:
            query = query.filter(AnalyticsEvent.user_id == user_id)
        if event_name:
            query = query.filter(AnalyticsEvent.event_name == event_name)
        if start_date:
            query = query.filter(AnalyticsEvent.created_at >= start_date)
        if end_date:
            query = query.filter(AnalyticsEvent.created_at <= end_date)

        return query.order_by(AnalyticsEvent.created_at.desc()).offset(offset).limit(limit).all()

    def get_dau(self, date: Optional[datetime] = None) -> int:
        """Get Daily Active Users count for a specific date."""
        if date is None:
            date = datetime.utcnow()

        start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)

        return self.session.query(func.count(func.distinct(AnalyticsEvent.user_id)))\
            .filter(AnalyticsEvent.created_at >= start)\
            .filter(AnalyticsEvent.created_at < end)\
            .filter(AnalyticsEvent.user_id.isnot(None))\
            .scalar() or 0

    def get_event_counts(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> dict:
        """Get event counts grouped by event_name."""
        query = self.session.query(
            AnalyticsEvent.event_name,
            func.count(AnalyticsEvent.id).label('count')
        )

        if start_date:
            query = query.filter(AnalyticsEvent.created_at >= start_date)
        if end_date:
            query = query.filter(AnalyticsEvent.created_at <= end_date)

        results = query.group_by(AnalyticsEvent.event_name).all()
        return {row.event_name: row.count for row in results}

    def get_screen_views(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> dict:
        """Get screen view counts."""
        events = self.get_events(
            event_name="screen_view",
            start_date=start_date,
            end_date=end_date,
            limit=10000
        )

        screen_counts = {}
        for event in events:
            if event.event_params:
                params = json.loads(event.event_params)
                screen_name = params.get("screen_name", "unknown")
                screen_counts[screen_name] = screen_counts.get(screen_name, 0) + 1

        return screen_counts
