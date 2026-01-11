"""
Recurring Activities API Router

Handles recurring activity series:
- Create recurring series (generates all instances)
- Update single instance or following
- Cancel single instance or entire series
"""

import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List

from storage.db import (
    Activity, RecurringTemplate, User, Participation, Membership,
    ActivityStatus, ParticipationStatus, PaymentStatus
)
from app.core.dependencies import get_db, get_current_user
from app.core.timezone import utc_now, is_past, is_future
from permissions import can_create_activity_in_club, can_create_activity_in_group
from schemas.recurring import (
    RecurringTemplateCreate,
    RecurringTemplateResponse,
    RecurringSeriesCreateResponse,
    RecurringUpdateScope,
    RecurringCancelScope,
    RecurringUpdateRequest,
    RecurringActionResponse
)
from app_config.constants import DEFAULT_COUNTRY

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/recurring", tags=["recurring"])


def generate_occurrence_dates(
    start_date: datetime,
    frequency: int,
    total: int
) -> List[datetime]:
    """
    Generate dates for recurring activities.

    Args:
        start_date: First occurrence date/time
        frequency: 1-4 times per month (4=weekly, 2=bi-weekly, 1=monthly)
        total: Total occurrences to generate

    Returns:
        List of datetime objects for each occurrence
    """
    dates = []
    current = start_date

    # Calculate interval based on frequency
    # frequency=4: weekly (every 1 week)
    # frequency=2: bi-weekly (every 2 weeks)
    # frequency=1: monthly (every 4 weeks)
    week_interval = 4 // frequency

    for i in range(total):
        dates.append(current)
        current = current + timedelta(weeks=week_interval)

    return dates


def _build_template_response(template: RecurringTemplate, db: Session) -> RecurringTemplateResponse:
    """Build RecurringTemplateResponse from template model."""
    response = RecurringTemplateResponse.model_validate(template)

    # Add club/group names
    if template.club:
        response.club_name = template.club.name
    if template.group:
        response.group_name = template.group.name

    return response


@router.post("", response_model=RecurringSeriesCreateResponse, status_code=201)
async def create_recurring_series(
    data: RecurringTemplateCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a recurring activity series.

    Generates all activity instances immediately (Variant A).
    Only club/group organizers can create recurring activities.

    Returns template info and first activity ID.
    """
    # Validate organization is set
    if not data.club_id and not data.group_id:
        raise HTTPException(
            status_code=400,
            detail="Either club_id or group_id is required for recurring activities"
        )

    # Check permissions
    if data.club_id:
        if not can_create_activity_in_club(db, current_user, data.club_id):
            raise HTTPException(
                status_code=403,
                detail="Only club organizers can create recurring activities"
            )

    if data.group_id:
        if not can_create_activity_in_group(db, current_user, data.group_id):
            raise HTTPException(
                status_code=403,
                detail="Only group organizers can create recurring activities"
            )

    # Create template
    template = RecurringTemplate(
        title=data.title,
        description=data.description,
        day_of_week=data.day_of_week,
        time_of_day=data.time_of_day,
        frequency=data.frequency,
        total_occurrences=data.total_occurrences,
        location=data.location,
        sport_type=data.sport_type,
        difficulty=data.difficulty,
        distance=data.distance,
        duration=data.duration,
        max_participants=data.max_participants,
        club_id=data.club_id,
        group_id=data.group_id,
        creator_id=current_user.id
    )
    db.add(template)
    db.flush()  # Get template ID

    # Generate all occurrence dates
    dates = generate_occurrence_dates(
        data.start_date,
        data.frequency,
        data.total_occurrences
    )

    # Create all activity instances
    first_activity_id = None
    for seq, date in enumerate(dates, start=1):
        activity = Activity(
            title=data.title,
            description=data.description,
            date=date,
            location=data.location,
            sport_type=data.sport_type,
            difficulty=data.difficulty,
            distance=data.distance,
            duration=data.duration,
            max_participants=data.max_participants,
            club_id=data.club_id,
            group_id=data.group_id,
            creator_id=current_user.id,
            recurring_template_id=template.id,
            recurring_sequence=seq,
            city=current_user.city,
            country=current_user.country or DEFAULT_COUNTRY,
            status=ActivityStatus.UPCOMING
        )
        db.add(activity)
        db.flush()

        # Save first activity ID
        if seq == 1:
            first_activity_id = activity.id

        # Add creator as participant for each activity
        participation = Participation(
            activity_id=activity.id,
            user_id=current_user.id,
            status=ParticipationStatus.CONFIRMED
        )
        db.add(participation)

    template.generated_count = len(dates)
    db.commit()
    db.refresh(template)

    logger.info(
        f"Created recurring series '{data.title}' with {len(dates)} activities "
        f"(template_id={template.id}, user={current_user.id})"
    )

    return RecurringSeriesCreateResponse(
        template=_build_template_response(template, db),
        activities_created=len(dates),
        first_activity_id=first_activity_id
    )


@router.patch("/{activity_id}", response_model=RecurringActionResponse)
async def update_recurring_activity(
    activity_id: str,
    scope: RecurringUpdateScope = Query(..., description="Update scope: this_only or this_and_following"),
    data: RecurringUpdateRequest = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a recurring activity.

    scope=THIS_ONLY: Update only this instance (detaches from template for edited fields)
    scope=THIS_AND_FOLLOWING: Update this and all future instances in the series
    """
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    if not activity.recurring_template_id:
        raise HTTPException(status_code=400, detail="This is not a recurring activity")

    # Check permissions
    if activity.creator_id != current_user.id:
        # Check if user is club/group admin
        is_admin = False
        if activity.club_id:
            membership = db.query(Membership).filter(
                Membership.club_id == activity.club_id,
                Membership.user_id == current_user.id,
                Membership.role.in_(['admin', 'organizer'])
            ).first()
            is_admin = membership is not None

        if activity.group_id and not is_admin:
            membership = db.query(Membership).filter(
                Membership.group_id == activity.group_id,
                Membership.user_id == current_user.id,
                Membership.role.in_(['admin', 'trainer'])
            ).first()
            is_admin = membership is not None

        if not is_admin:
            raise HTTPException(
                status_code=403,
                detail="Only creator or organizer can update recurring activities"
            )

    # Check if activity is in the past
    if is_past(activity.date):
        raise HTTPException(status_code=400, detail="Cannot update past activities")

    update_data = data.model_dump(exclude_unset=True) if data else {}

    if scope == RecurringUpdateScope.THIS_ONLY:
        # Update only this instance
        for field, value in update_data.items():
            if hasattr(activity, field):
                setattr(activity, field, value)
        db.commit()

        logger.info(f"Updated single recurring activity {activity_id}")
        return RecurringActionResponse(
            message="Activity updated",
            affected_count=1
        )

    else:  # THIS_AND_FOLLOWING
        # Update this and all following in the series
        activities = db.query(Activity).filter(
            Activity.recurring_template_id == activity.recurring_template_id,
            Activity.recurring_sequence >= activity.recurring_sequence,
            Activity.status == ActivityStatus.UPCOMING
        ).all()

        updated_count = 0
        for act in activities:
            # Don't update past activities
            if is_past(act.date):
                continue

            for field, value in update_data.items():
                # Don't update date or sequence
                if field not in ['date', 'recurring_sequence'] and hasattr(act, field):
                    setattr(act, field, value)
            updated_count += 1

        db.commit()

        logger.info(f"Updated {updated_count} recurring activities from {activity_id}")
        return RecurringActionResponse(
            message="Activities updated",
            affected_count=updated_count
        )


@router.delete("/{activity_id}", response_model=RecurringActionResponse)
async def cancel_recurring_activity(
    activity_id: str,
    scope: RecurringCancelScope = Query(..., description="Cancel scope: this_only or entire_series"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Cancel recurring activity.

    scope=THIS_ONLY: Cancel only this instance
    scope=ENTIRE_SERIES: Cancel all future instances and deactivate template
    """
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    if not activity.recurring_template_id:
        raise HTTPException(status_code=400, detail="This is not a recurring activity")

    # Check permissions
    if activity.creator_id != current_user.id:
        # Check if user is club/group admin
        is_admin = False
        if activity.club_id:
            membership = db.query(Membership).filter(
                Membership.club_id == activity.club_id,
                Membership.user_id == current_user.id,
                Membership.role.in_(['admin', 'organizer'])
            ).first()
            is_admin = membership is not None

        if activity.group_id and not is_admin:
            membership = db.query(Membership).filter(
                Membership.group_id == activity.group_id,
                Membership.user_id == current_user.id,
                Membership.role.in_(['admin', 'trainer'])
            ).first()
            is_admin = membership is not None

        if not is_admin:
            raise HTTPException(
                status_code=403,
                detail="Only creator or organizer can cancel recurring activities"
            )

    template_id = activity.recurring_template_id

    if scope == RecurringCancelScope.THIS_ONLY:
        # Cancel only this instance
        if is_past(activity.date):
            raise HTTPException(status_code=400, detail="Cannot cancel past activities")

        activity.status = ActivityStatus.CANCELLED
        db.commit()

        logger.info(f"Cancelled single recurring activity {activity_id}")
        return RecurringActionResponse(
            message="Activity cancelled",
            affected_count=1
        )

    else:  # ENTIRE_SERIES
        # Cancel all future instances and deactivate template
        activities = db.query(Activity).filter(
            Activity.recurring_template_id == template_id,
            Activity.date > utc_now(),
            Activity.status == ActivityStatus.UPCOMING
        ).all()

        cancelled_count = 0
        for act in activities:
            act.status = ActivityStatus.CANCELLED
            cancelled_count += 1

        # Deactivate template
        template = db.query(RecurringTemplate).filter(
            RecurringTemplate.id == template_id
        ).first()
        if template:
            template.active = False

        db.commit()

        logger.info(f"Cancelled {cancelled_count} recurring activities in series {template_id}")
        return RecurringActionResponse(
            message="Series cancelled",
            affected_count=cancelled_count
        )


@router.get("/{template_id}", response_model=RecurringTemplateResponse)
async def get_recurring_template(
    template_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get recurring template details."""
    template = db.query(RecurringTemplate).filter(
        RecurringTemplate.id == template_id
    ).first()

    if not template:
        raise HTTPException(status_code=404, detail="Recurring template not found")

    return _build_template_response(template, db)
