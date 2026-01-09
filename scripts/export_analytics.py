#!/usr/bin/env python
"""
Analytics Export Script

Exports analytics data to CSV files for analysis.
Run from project root: python scripts/export_analytics.py

Output files are saved to: exports/analytics/
"""

import os
import sys
import csv
import json
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from storage.db import SessionLocal, AnalyticsEvent, User, Activity, Participation
from sqlalchemy import func, distinct


def ensure_export_dir():
    """Create export directory if it doesn't exist."""
    export_dir = project_root / "exports" / "analytics"
    export_dir.mkdir(parents=True, exist_ok=True)
    return export_dir


def export_raw_events(db, export_dir: Path):
    """Export all raw analytics events."""
    events = db.query(AnalyticsEvent).order_by(AnalyticsEvent.created_at.desc()).all()

    filepath = export_dir / f"events_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['id', 'user_id', 'event_name', 'event_params', 'session_id', 'created_at'])

        for event in events:
            writer.writerow([
                event.id,
                event.user_id,
                event.event_name,
                event.event_params,
                event.session_id,
                event.created_at.isoformat() if event.created_at else None
            ])

    print(f"Exported {len(events)} events to {filepath}")
    return len(events)


def export_event_summary(db, export_dir: Path):
    """Export event counts by type."""
    results = db.query(
        AnalyticsEvent.event_name,
        func.count(AnalyticsEvent.id).label('count')
    ).group_by(AnalyticsEvent.event_name).order_by(func.count(AnalyticsEvent.id).desc()).all()

    filepath = export_dir / f"event_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['event_name', 'count'])

        for row in results:
            writer.writerow([row.event_name, row.count])

    print(f"Exported event summary to {filepath}")


def export_screen_views(db, export_dir: Path):
    """Export screen view counts."""
    events = db.query(AnalyticsEvent).filter(
        AnalyticsEvent.event_name == 'screen_view'
    ).all()

    screen_counts = {}
    for event in events:
        if event.event_params:
            params = json.loads(event.event_params)
            screen_name = params.get('screen_name', 'unknown')
            screen_counts[screen_name] = screen_counts.get(screen_name, 0) + 1

    filepath = export_dir / f"screen_views_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['screen_name', 'view_count'])

        for screen, count in sorted(screen_counts.items(), key=lambda x: -x[1]):
            writer.writerow([screen, count])

    print(f"Exported screen views to {filepath}")


def export_dau_report(db, export_dir: Path, days: int = 30):
    """Export Daily Active Users for last N days."""
    filepath = export_dir / f"dau_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['date', 'active_users'])

        for i in range(days):
            date = datetime.utcnow().date() - timedelta(days=i)
            start = datetime.combine(date, datetime.min.time())
            end = start + timedelta(days=1)

            count = db.query(func.count(distinct(AnalyticsEvent.user_id))).filter(
                AnalyticsEvent.created_at >= start,
                AnalyticsEvent.created_at < end,
                AnalyticsEvent.user_id.isnot(None)
            ).scalar() or 0

            writer.writerow([date.isoformat(), count])

    print(f"Exported DAU report to {filepath}")


def export_onboarding_funnel(db, export_dir: Path):
    """Export onboarding funnel data."""
    steps = ['consent', 'photo_visibility', 'sports', 'role', 'intro']

    funnel = {}
    for step in steps:
        count = db.query(func.count(distinct(AnalyticsEvent.user_id))).filter(
            AnalyticsEvent.event_name == 'onboarding_step',
            AnalyticsEvent.event_params.like(f'%"{step}"%')
        ).scalar() or 0
        funnel[step] = count

    completed = db.query(func.count(distinct(AnalyticsEvent.user_id))).filter(
        AnalyticsEvent.event_name == 'onboarding_complete'
    ).scalar() or 0
    funnel['completed'] = completed

    filepath = export_dir / f"onboarding_funnel_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['step', 'users', 'conversion_rate'])

        first_step = funnel.get('consent', 0)
        for step, count in funnel.items():
            rate = f"{(count / first_step * 100):.1f}%" if first_step > 0 else "0%"
            writer.writerow([step, count, rate])

    print(f"Exported onboarding funnel to {filepath}")


def export_user_activity_stats(db, export_dir: Path):
    """Export user activity statistics."""
    # Get all users with their stats
    users = db.query(User).all()

    filepath = export_dir / f"user_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'user_id', 'username', 'first_name',
            'activities_created', 'activities_joined', 'activities_attended',
            'first_seen', 'last_seen', 'onboarding_completed'
        ])

        for user in users:
            # Activities created
            created = db.query(func.count(Activity.id)).filter(
                Activity.creator_id == user.id
            ).scalar() or 0

            # Activities joined (registered)
            joined = db.query(func.count(Participation.id)).filter(
                Participation.user_id == user.id
            ).scalar() or 0

            # Activities attended
            attended = db.query(func.count(Participation.id)).filter(
                Participation.user_id == user.id,
                Participation.status == 'attended'
            ).scalar() or 0

            writer.writerow([
                user.id,
                user.username,
                user.first_name,
                created,
                joined,
                attended,
                user.first_seen_at.isoformat() if user.first_seen_at else None,
                user.last_seen_at.isoformat() if user.last_seen_at else None,
                user.has_completed_onboarding
            ])

    print(f"Exported user stats to {filepath}")


def print_quick_stats(db):
    """Print quick summary stats to console."""
    print("\n" + "=" * 50)
    print("QUICK ANALYTICS SUMMARY")
    print("=" * 50)

    # Total events
    total_events = db.query(func.count(AnalyticsEvent.id)).scalar() or 0
    print(f"Total events tracked: {total_events}")

    # Unique users
    unique_users = db.query(func.count(distinct(AnalyticsEvent.user_id))).filter(
        AnalyticsEvent.user_id.isnot(None)
    ).scalar() or 0
    print(f"Unique users tracked: {unique_users}")

    # Today's DAU
    today = datetime.utcnow().date()
    today_start = datetime.combine(today, datetime.min.time())
    dau = db.query(func.count(distinct(AnalyticsEvent.user_id))).filter(
        AnalyticsEvent.created_at >= today_start,
        AnalyticsEvent.user_id.isnot(None)
    ).scalar() or 0
    print(f"Today's active users: {dau}")

    # Event breakdown
    print("\nTop events:")
    events = db.query(
        AnalyticsEvent.event_name,
        func.count(AnalyticsEvent.id).label('count')
    ).group_by(AnalyticsEvent.event_name).order_by(
        func.count(AnalyticsEvent.id).desc()
    ).limit(10).all()

    for event in events:
        print(f"  {event.event_name}: {event.count}")

    print("=" * 50 + "\n")


def main():
    """Main export function."""
    print("Starting analytics export...")

    db = SessionLocal()
    try:
        export_dir = ensure_export_dir()

        # Print quick stats
        print_quick_stats(db)

        # Export all reports
        export_raw_events(db, export_dir)
        export_event_summary(db, export_dir)
        export_screen_views(db, export_dir)
        export_dau_report(db, export_dir)
        export_onboarding_funnel(db, export_dir)
        export_user_activity_stats(db, export_dir)

        print(f"\nAll exports saved to: {export_dir}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
