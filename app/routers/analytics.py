"""
Analytics API Router
"""
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from storage.db import User
from storage.analytics_storage import AnalyticsStorage
from app.core.dependencies import get_db, get_current_user
from schemas.analytics import AnalyticsEventCreate, AnalyticsEventResponse, AnalyticsEventBatch

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.post("/event", response_model=AnalyticsEventResponse)
def track_event(
    event: AnalyticsEventCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> AnalyticsEventResponse:
    """
    Track a single analytics event.

    Events:
    - screen_view: {"screen_name": "home"}
    - activity_create: {"activity_id": "...", "sport_type": "running"}
    - activity_join: {"activity_id": "..."}
    - activity_cancel: {"activity_id": "..."}
    - activity_attend: {"activity_id": "..."}
    - club_join: {"club_id": "..."}
    - group_join: {"group_id": "..."}
    - gpx_download: {"activity_id": "..."}
    """
    storage = AnalyticsStorage(session=db)

    db_event = storage.track_event(
        event_name=event.event_name,
        user_id=current_user.id,
        event_params=event.event_params,
        session_id=event.session_id
    )

    # Parse event_params back to dict for response
    response_params = None
    if db_event.event_params:
        response_params = json.loads(db_event.event_params)

    return AnalyticsEventResponse(
        id=db_event.id,
        user_id=db_event.user_id,
        event_name=db_event.event_name,
        event_params=response_params,
        session_id=db_event.session_id,
        created_at=db_event.created_at
    )


@router.post("/events/batch")
def track_events_batch(
    batch: AnalyticsEventBatch,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """
    Track multiple analytics events in batch.
    Useful for offline sync or reducing API calls.
    Max 100 events per batch.
    """
    storage = AnalyticsStorage(session=db)

    events_data = [
        {
            "event_name": e.event_name,
            "event_params": e.event_params,
            "session_id": e.session_id
        }
        for e in batch.events
    ]

    count = storage.track_events_batch(
        events=events_data,
        user_id=current_user.id
    )

    return {"tracked": count}
