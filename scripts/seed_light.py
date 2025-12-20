"""
Light Seed Script - creates minimal test data
Keeps users, clears everything else

Creator of all entities: @ray_mann
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from storage.db import (
    SessionLocal, init_db,
    User, Club, Group, Activity, Membership, Participation,
    UserRole, SportType, Difficulty, ActivityVisibility, ActivityStatus,
    ParticipationStatus, PaymentStatus, JoinRequest
)


def clear_data_except_users(db: Session):
    """Clear all data except users"""
    print("[CLEAR] Clearing data (keeping users)...")
    db.query(JoinRequest).delete()
    db.query(Participation).delete()
    db.query(Activity).delete()
    db.query(Membership).delete()
    db.query(Group).delete()
    db.query(Club).delete()
    db.commit()
    print("[SUCCESS] Data cleared (users kept)")


def get_ray_mann(db: Session) -> User:
    """Get @ray_mann user"""
    user = db.query(User).filter(User.username == "ray_mann").first()
    if not user:
        raise Exception("User @ray_mann not found! Create user first via bot.")
    print(f"[USER] Found @ray_mann: {user.id}")
    return user


def create_clubs(db: Session, creator: User):
    """Create 2 clubs: 1 open, 1 closed"""
    print("\n[CLUBS] Creating clubs...")

    # Open club
    open_club = Club(
        name="Nike Running Club Almaty",
        description="Открытый беговой клуб Nike. Регулярные тренировки для всех уровней подготовки. Присоединяйтесь!",
        creator_id=creator.id,
        city="Almaty",
        is_open=True,
        is_paid=False,
    )
    db.add(open_club)

    # Closed club
    closed_club = Club(
        name="SRG - Sky Running Group",
        description="Команда скайраннеров Алматы. Тренировки в горах, восхождения, trail running. Закрытый клуб - только по приглашениям.",
        creator_id=creator.id,
        city="Almaty",
        is_open=False,
        is_paid=False,
    )
    db.add(closed_club)

    db.commit()
    db.refresh(open_club)
    db.refresh(closed_club)

    # Add creator as organizer
    db.add(Membership(user_id=creator.id, club_id=open_club.id, role=UserRole.ORGANIZER))
    db.add(Membership(user_id=creator.id, club_id=closed_club.id, role=UserRole.ORGANIZER))
    db.commit()

    print(f"   [OK] Nike Running Club (OPEN): {open_club.id}")
    print(f"   [OK] SRG (CLOSED): {closed_club.id}")

    return open_club, closed_club


def create_groups(db: Session, creator: User, open_club: Club, closed_club: Club):
    """Create 2 groups: 1 open standalone, 1 closed in club"""
    print("\n[GROUPS] Creating groups...")

    # Open standalone group
    open_group = Group(
        name="Parkrun Almaty",
        description="Открытая группа для паркранов по субботам. Каждую субботу в 9:00 в парке Горького.",
        club_id=None,
        creator_id=creator.id,
        city="Almaty",
        is_open=True,
    )
    db.add(open_group)

    # Closed group in SRG club
    closed_group = Group(
        name="SRG Мощные",
        description="Закрытая группа для продвинутых спортсменов SRG. Только для участников клуба.",
        club_id=closed_club.id,
        creator_id=creator.id,
        city="Almaty",
        is_open=False,
    )
    db.add(closed_group)

    db.commit()
    db.refresh(open_group)
    db.refresh(closed_group)

    # Add creator as organizer
    db.add(Membership(user_id=creator.id, group_id=open_group.id, role=UserRole.ORGANIZER))
    db.add(Membership(user_id=creator.id, group_id=closed_group.id, role=UserRole.ORGANIZER))
    db.commit()

    print(f"   [OK] Parkrun Almaty (OPEN, standalone): {open_group.id}")
    print(f"   [OK] SRG Powerful (CLOSED, in SRG): {closed_group.id}")

    return open_group, closed_group


def create_activities(db: Session, creator: User, open_club: Club, closed_club: Club, open_group: Group, closed_group: Group):
    """Create 2-3 activities for each entity"""
    print("\n[ACTIVITIES] Creating activities...")

    now = datetime.now()
    activities_created = 0

    # Nike Club (OPEN) - 3 activities
    nike_activities = [
        {
            "title": "Утренняя пробежка на терренкуре",
            "description": "Легкая восстановительная пробежка. Сбор у нижней станции канатки.",
            "date": now + timedelta(days=2, hours=9),
            "location": "Терренкур, Алматы",
            "sport_type": SportType.RUNNING,
            "difficulty": Difficulty.EASY,
            "distance": 5.0,
            "is_open": True,
        },
        {
            "title": "Интервалы на стадионе",
            "description": "Скоростная работа 10x400м. Разминка в 18:00.",
            "date": now + timedelta(days=4, hours=18),
            "location": "Центральный стадион, Алматы",
            "sport_type": SportType.RUNNING,
            "difficulty": Difficulty.MEDIUM,
            "distance": 8.0,
            "is_open": True,
        },
        {
            "title": "Лонг в горах",
            "description": "Длительная пробежка по горным тропам. Набор 500м.",
            "date": now + timedelta(days=6, hours=8),
            "location": "Медео - Шымбулак, Алматы",
            "sport_type": SportType.TRAIL,
            "difficulty": Difficulty.MEDIUM,
            "distance": 18.0,
            "is_open": True,
        },
    ]

    for data in nike_activities:
        activity = Activity(
            title=data["title"],
            description=data["description"],
            date=data["date"],
            location=data["location"],
            city="Almaty",
            club_id=open_club.id,
            creator_id=creator.id,
            sport_type=data["sport_type"],
            difficulty=data["difficulty"],
            distance=data["distance"],
            is_open=data["is_open"],
            visibility=ActivityVisibility.PUBLIC,
            status=ActivityStatus.UPCOMING,
            max_participants=30,
        )
        db.add(activity)
        db.flush()  # Get activity.id

        # Add creator as participant
        db.add(Participation(
            activity_id=activity.id,
            user_id=creator.id,
            status=ParticipationStatus.CONFIRMED,
            payment_status=PaymentStatus.NOT_REQUIRED
        ))
        activities_created += 1

    print(f"   [OK] Nike Club: 3 activities (OPEN)")

    # SRG Club (CLOSED) - 3 activities (should be closed too)
    srg_activities = [
        {
            "title": "Шымбулак - Нунатак 3500м",
            "description": "Восхождение через перевал к Нунатаку. Только для членов SRG!",
            "date": now + timedelta(days=3, hours=7),
            "location": "Шымбулак, Алматы",
            "sport_type": SportType.TRAIL,
            "difficulty": Difficulty.HARD,
            "distance": 12.0,
            "is_open": False,
        },
        {
            "title": "Пик Букреева - контрольная",
            "description": "Контрольная тренировка на пике Букреева. 1200 D+",
            "date": now + timedelta(days=7, hours=6),
            "location": "Пик Букреева, Алматы",
            "sport_type": SportType.TRAIL,
            "difficulty": Difficulty.HARD,
            "distance": 15.0,
            "is_open": False,
        },
        {
            "title": "Восхождение на Мынжылкы",
            "description": "Вершина Мынжылкы 3600м. Сложный маршрут.",
            "date": now + timedelta(days=10, hours=5),
            "location": "Мынжылкы, Алматы",
            "sport_type": SportType.TRAIL,
            "difficulty": Difficulty.HARD,
            "distance": 20.0,
            "is_open": False,
        },
    ]

    for data in srg_activities:
        activity = Activity(
            title=data["title"],
            description=data["description"],
            date=data["date"],
            location=data["location"],
            city="Almaty",
            club_id=closed_club.id,
            creator_id=creator.id,
            sport_type=data["sport_type"],
            difficulty=data["difficulty"],
            distance=data["distance"],
            is_open=data["is_open"],
            visibility=ActivityVisibility.PRIVATE_CLUB,
            status=ActivityStatus.UPCOMING,
            max_participants=15,
        )
        db.add(activity)
        db.flush()  # Get activity.id

        # Add creator as participant
        db.add(Participation(
            activity_id=activity.id,
            user_id=creator.id,
            status=ParticipationStatus.CONFIRMED,
            payment_status=PaymentStatus.NOT_REQUIRED
        ))
        activities_created += 1

    print(f"   [OK] SRG Club: 3 activities (CLOSED)")

    # Parkrun Group (OPEN) - 2 activities
    parkrun_activities = [
        {
            "title": "Parkrun Almaty #42",
            "description": "Еженедельный бесплатный забег 5 км. Старт в 9:00!",
            "date": now + timedelta(days=5, hours=9),
            "location": "Парк Горького, Алматы",
            "sport_type": SportType.RUNNING,
            "difficulty": Difficulty.EASY,
            "distance": 5.0,
            "is_open": True,
        },
        {
            "title": "Parkrun Almaty #43",
            "description": "Еженедельный бесплатный забег 5 км. Старт в 9:00!",
            "date": now + timedelta(days=12, hours=9),
            "location": "Парк Горького, Алматы",
            "sport_type": SportType.RUNNING,
            "difficulty": Difficulty.EASY,
            "distance": 5.0,
            "is_open": True,
        },
    ]

    for data in parkrun_activities:
        activity = Activity(
            title=data["title"],
            description=data["description"],
            date=data["date"],
            location=data["location"],
            city="Almaty",
            group_id=open_group.id,
            creator_id=creator.id,
            sport_type=data["sport_type"],
            difficulty=data["difficulty"],
            distance=data["distance"],
            is_open=data["is_open"],
            visibility=ActivityVisibility.PUBLIC,
            status=ActivityStatus.UPCOMING,
            max_participants=100,
        )
        db.add(activity)
        db.flush()  # Get activity.id

        # Add creator as participant
        db.add(Participation(
            activity_id=activity.id,
            user_id=creator.id,
            status=ParticipationStatus.CONFIRMED,
            payment_status=PaymentStatus.NOT_REQUIRED
        ))
        activities_created += 1

    print(f"   [OK] Parkrun Group: 2 activities (OPEN)")

    # SRG Мощные Group (CLOSED) - 2 activities
    powerful_activities = [
        {
            "title": "Тренировка для продвинутых - спринты",
            "description": "Скоростная работа в горах. Только для членов группы.",
            "date": now + timedelta(days=4, hours=7),
            "location": "Шымбулак, Алматы",
            "sport_type": SportType.TRAIL,
            "difficulty": Difficulty.HARD,
            "distance": 8.0,
            "is_open": False,
        },
        {
            "title": "Вертикальный километр",
            "description": "VK тренировка. 1000м набора за минимум времени.",
            "date": now + timedelta(days=8, hours=6),
            "location": "Чимбулак, Алматы",
            "sport_type": SportType.TRAIL,
            "difficulty": Difficulty.HARD,
            "distance": 5.0,
            "is_open": False,
        },
    ]

    for data in powerful_activities:
        activity = Activity(
            title=data["title"],
            description=data["description"],
            date=data["date"],
            location=data["location"],
            city="Almaty",
            group_id=closed_group.id,
            creator_id=creator.id,
            sport_type=data["sport_type"],
            difficulty=data["difficulty"],
            distance=data["distance"],
            is_open=data["is_open"],
            visibility=ActivityVisibility.PRIVATE_GROUP,
            status=ActivityStatus.UPCOMING,
            max_participants=10,
        )
        db.add(activity)
        db.flush()  # Get activity.id

        # Add creator as participant
        db.add(Participation(
            activity_id=activity.id,
            user_id=creator.id,
            status=ParticipationStatus.CONFIRMED,
            payment_status=PaymentStatus.NOT_REQUIRED
        ))
        activities_created += 1

    print(f"   [OK] SRG Powerful Group: 2 activities (CLOSED)")

    db.commit()
    print(f"\n[SUCCESS] Created {activities_created} activities total")


def seed_light():
    """Main function"""
    print("=" * 60)
    print("Light Seed - Minimal Test Data")
    print("Creator: @ray_mann")
    print("=" * 60)

    init_db()
    db = SessionLocal()

    try:
        # Clear data except users
        clear_data_except_users(db)

        # Get ray_mann
        creator = get_ray_mann(db)

        # Create clubs
        open_club, closed_club = create_clubs(db, creator)

        # Create groups
        open_group, closed_group = create_groups(db, creator, open_club, closed_club)

        # Create activities
        create_activities(db, creator, open_club, closed_club, open_group, closed_group)

        print("\n" + "=" * 60)
        print("[SUCCESS] Light seeding completed!")
        print("=" * 60)

        # Summary
        print("\nSummary:")
        print(f"   Users: {db.query(User).count()} (kept)")
        print(f"   Clubs: {db.query(Club).count()}")
        print(f"   Groups: {db.query(Group).count()}")
        print(f"   Activities: {db.query(Activity).count()}")
        print(f"   Memberships: {db.query(Membership).count()}")
        print(f"   Participations: {db.query(Participation).count()}")

        print("\nStructure:")
        print("   [OPEN]  Nike Running Club Almaty (3 activities)")
        print("   [CLOSED] SRG - Sky Running Group (3 activities)")
        print("   [OPEN]  Parkrun Almaty - standalone group (2 activities)")
        print("   [CLOSED] SRG Powerful - group in SRG (2 activities)")

    except Exception as e:
        print(f"\n[ERROR] Error during seeding: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_light()
