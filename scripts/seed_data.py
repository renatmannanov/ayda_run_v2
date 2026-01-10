"""
Seed data script for Ayda Run application

Generates test data:
- 30 users with Telegram-like data
- 3 clubs (SRG, Nike Running Club, Climbing club)
- 2 standalone groups
- Multiple activities
- Memberships and participations

Usage:
    python seed_data.py
"""

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from storage.db import (
    SessionLocal, init_db,
    User, Club, Group, Activity, Membership, Participation,
    UserRole, SportType, Difficulty, ActivityVisibility, ActivityStatus,
    ParticipationStatus, PaymentStatus
)
import random

# Placeholder avatar URLs (similar size to Telegram avatars)
AVATAR_PLACEHOLDERS = [
    f"https://i.pravatar.cc/150?img={i}" for i in range(1, 71)
]

# Sample user data (Telegram-like)
SAMPLE_USERS = [
    {"telegram_id": 5414820474, "username": "admin", "first_name": "Ренат", "last_name": "Маннанов"},
    {"telegram_id": 123456789, "username": "alexrunner", "first_name": "Александр", "last_name": "Петров"},
    {"telegram_id": 234567890, "username": "marinasky", "first_name": "Марина", "last_name": "Иванова"},
    {"telegram_id": 345678901, "username": "dmitry_trail", "first_name": "Дмитрий", "last_name": "Соколов"},
    {"telegram_id": 456789012, "username": "olga_mountain", "first_name": "Ольга", "last_name": "Сидорова"},
    {"telegram_id": 567890123, "username": "ivan_skyrunner", "first_name": "Иван", "last_name": "Кузнецов"},
    {"telegram_id": 678901234, "username": "elena_peak", "first_name": "Елена", "last_name": "Смирнова"},
    {"telegram_id": 789012345, "username": "sergey_ultra", "first_name": "Сергей", "last_name": "Морозов"},
    {"telegram_id": 890123456, "username": "natalia_run", "first_name": "Наталья", "last_name": "Новикова"},
    {"telegram_id": 901234567, "username": "andrey_climb", "first_name": "Андрей", "last_name": "Волков"},
    {"telegram_id": 112345678, "username": "julia_hike", "first_name": "Юлия", "last_name": "Федорова"},
    {"telegram_id": 223456789, "username": "maxim_speed", "first_name": "Максим", "last_name": "Михайлов"},
    {"telegram_id": 334567890, "username": "anna_fitness", "first_name": "Анна", "last_name": "Борисова"},
    {"telegram_id": 445678901, "username": "pavel_marathon", "first_name": "Павел", "last_name": "Орлов"},
    {"telegram_id": 556789012, "username": "victoria_sport", "first_name": "Виктория", "last_name": "Григорьева"},
    {"telegram_id": 667890123, "username": "roman_active", "first_name": "Роман", "last_name": "Степанов"},
    {"telegram_id": 778901234, "username": "svetlana_run", "first_name": "Светлана", "last_name": "Николаева"},
    {"telegram_id": 889012345, "username": "denis_trail", "first_name": "Денис", "last_name": "Захаров"},
    {"telegram_id": 990123456, "username": "irina_outdoor", "first_name": "Ирина", "last_name": "Романова"},
    {"telegram_id": 101234567, "username": "artem_summit", "first_name": "Артем", "last_name": "Васильев"},
    {"telegram_id": 202345678, "username": "ksenia_runner", "first_name": "Ксения", "last_name": "Павлова"},
    {"telegram_id": 303456789, "username": "vladislav_sky", "first_name": "Владислав", "last_name": "Семенов"},
    {"telegram_id": 404567890, "username": "daria_peak", "first_name": "Дарья", "last_name": "Егорова"},
    {"telegram_id": 505678901, "username": "nikolay_ultra", "first_name": "Николай", "last_name": "Козлов"},
    {"telegram_id": 606789012, "username": "alina_sport", "first_name": "Алина", "last_name": "Виноградова"},
    {"telegram_id": 707890123, "username": "kirill_run", "first_name": "Кирилл", "last_name": "Лебедев"},
    {"telegram_id": 808901234, "username": "ekaterina_hike", "first_name": "Екатерина", "last_name": "Макарова"},
    {"telegram_id": 909012345, "username": "timur_climb", "first_name": "Тимур", "last_name": "Беляев"},
    {"telegram_id": 110123456, "username": "polina_trail", "first_name": "Полина", "last_name": "Попова"},
    {"telegram_id": 220234567, "username": "stanislav_mountain", "first_name": "Станислав", "last_name": "Соловьев"},
]


def clear_database(db: Session):
    """Clear all data from database"""
    print("[CLEAR] Clearing existing data...")
    db.query(Participation).delete()
    db.query(Activity).delete()
    db.query(Membership).delete()
    db.query(Group).delete()
    db.query(Club).delete()
    db.query(User).delete()
    db.commit()
    print("[SUCCESS] Database cleared")


def create_users(db: Session) -> dict:
    """Create 30 users"""
    print("\n[USERS] Creating users...")
    users = {}

    for user_data in SAMPLE_USERS:
        user = User(
            telegram_id=user_data["telegram_id"],
            username=user_data.get("username"),
            first_name=user_data["first_name"],
            # Note: We don't store last_name and photo_url in DB yet,
            # but they would come from Telegram WebApp API
        )
        db.add(user)
        users[user_data["telegram_id"]] = user

    db.commit()
    print(f"[SUCCESS] Created {len(users)} users")
    return users


def create_srg_club(db: Session, users: dict) -> tuple:
    """Create SRG club with 3 groups"""
    print("\n[SRG] Creating SRG - Sky Running Group...")

    # Create club
    admin_user = users[5414820474]
    club = Club(
        name="SRG - Sky Running Group",
        description="Команда скайраннеров Алматы. Тренировки в горах, восхождения, trail running. Только по приглашениям.",
        creator_id=admin_user.id,
        is_paid=False,
        telegram_chat_id=None  # Could be set if integrated with TG group
    )
    db.add(club)
    db.commit()
    db.refresh(club)

    # Create 3 groups
    group_novice = Group(
        name="Новички",
        description="Группа для начинающих скайраннеров",
        club_id=club.id,
        is_open=False
    )

    group_amateur = Group(
        name="Любители",
        description="Группа для опытных любителей",
        club_id=club.id,
        is_open=False
    )

    group_advanced = Group(
        name="Мощные",
        description="Группа для продвинутых спортсменов",
        club_id=club.id,
        is_open=False
    )

    db.add_all([group_novice, group_amateur, group_advanced])
    db.commit()
    db.refresh(group_novice)
    db.refresh(group_amateur)
    db.refresh(group_advanced)

    # Add members (15 total)
    # Admin as organizer at club level
    db.add(Membership(user_id=admin_user.id, club_id=club.id, role=UserRole.ORGANIZER))

    # 2 organizers total (admin + 1 more)
    organizer = users[123456789]
    db.add(Membership(user_id=organizer.id, club_id=club.id, role=UserRole.ORGANIZER))

    # Distribute remaining 13 members across groups with trainers
    novice_members = [234567890, 345678901, 456789012, 567890123, 678901234]  # 5 members
    amateur_members = [789012345, 890123456, 901234567, 112345678, 223456789]  # 5 members
    advanced_members = [334567890, 445678901, 556789012]  # 3 members

    # All group members need to be club members too
    all_group_members = novice_members + amateur_members + advanced_members

    # Add all group members to club (as regular members)
    for tid in all_group_members:
        db.add(Membership(user_id=users[tid].id, club_id=club.id, role=UserRole.MEMBER))

    # Add trainer to each group
    db.add(Membership(user_id=users[234567890].id, group_id=group_novice.id, role=UserRole.TRAINER))
    db.add(Membership(user_id=users[789012345].id, group_id=group_amateur.id, role=UserRole.TRAINER))
    db.add(Membership(user_id=users[334567890].id, group_id=group_advanced.id, role=UserRole.TRAINER))

    # Add regular members to groups (excluding trainers)
    for tid in novice_members[1:]:
        db.add(Membership(user_id=users[tid].id, group_id=group_novice.id, role=UserRole.MEMBER))

    for tid in amateur_members[1:]:
        db.add(Membership(user_id=users[tid].id, group_id=group_amateur.id, role=UserRole.MEMBER))

    for tid in advanced_members[1:]:
        db.add(Membership(user_id=users[tid].id, group_id=group_advanced.id, role=UserRole.MEMBER))

    db.commit()

    print(f"[SUCCESS] Created SRG club with {club.id}")
    print(f"   - Group 'Novice': {len(novice_members)} members")
    print(f"   - Group 'Amateur': {len(amateur_members)} members")
    print(f"   - Group 'Advanced': {len(advanced_members)} members")

    return club, [group_novice, group_amateur, group_advanced]


def create_srg_activities(db: Session, club: Club, groups: list, users: dict):
    """Create SRG activities for 2025-2026"""
    print("\n[ACTIVITIES] Creating SRG activities...")

    admin_user = users[5414820474]

    activities_data = [
        # 2025
        {
            "title": "Межклубная контрольная тренировка пик Букреева и SKY",
            "date": datetime(2025, 12, 7, 8, 0),
            "description": "Контрольная тренировка с клубом SKY на пике Букреева",
            "location": "Пик Букреева, Алматы",
            "distance": 12.0,
            "difficulty": Difficulty.HARD,
            "sport_type": SportType.TRAIL,
            "max_participants": 20,
        },
        {
            "title": "Шымбулак – перевал 3200 – Нунатак 3500 (Октябрьская пещера)",
            "date": datetime(2025, 12, 13, 9, 0),
            "description": "Восхождение через перевал к Нунатаку с посещением Октябрьской пещеры",
            "location": "Шымбулак, Алматы",
            "distance": 9.0,
            "difficulty": Difficulty.HARD,
            "sport_type": SportType.TRAIL,
            "max_participants": 15,
        },
        {
            "title": "Шымбулак – вершина Мынжылкы 3600 м",
            "date": datetime(2025, 12, 21, 8, 30),
            "description": "Восхождение на вершину Мынжылкы 3600 м",
            "location": "Шымбулак, Алматы",
            "distance": 14.0,
            "difficulty": Difficulty.HARD,
            "sport_type": SportType.TRAIL,
            "max_participants": 12,
        },
        {
            "title": "Малыш 3840 м / пещера Дельфин",
            "date": datetime(2025, 12, 28, 8, 0),
            "description": "Малыш 3840 м 20 km 1600 D+ или пещера Дельфин 19 km 1230 D+ (по погодным условиям)",
            "location": "Алматы",
            "distance": 20.0,
            "difficulty": Difficulty.HARD,
            "sport_type": SportType.TRAIL,
            "max_participants": 10,
        },
        # 2026
        {
            "title": "Шымбулак - озеро Маншук Маметовой 3600 м",
            "date": datetime(2026, 1, 3, 9, 0),
            "description": "Двухдневное восхождение к озеру Маншук Маметовой",
            "location": "Шымбулак, Алматы",
            "distance": 16.0,
            "difficulty": Difficulty.HARD,
            "sport_type": SportType.TRAIL,
            "duration": 480,  # 8 hours
            "max_participants": 12,
        },
        {
            "title": "Акклиматизация Бастион Амангельды 3900 м",
            "date": datetime(2026, 1, 11, 8, 0),
            "description": "Акклиматизационная тренировка на высоте",
            "location": "Бастион Амангельды, Алматы",
            "distance": 15.0,
            "difficulty": Difficulty.HARD,
            "sport_type": SportType.TRAIL,
            "max_participants": 15,
        },
        {
            "title": "Амангельды рэйс",
            "date": datetime(2026, 1, 17, 7, 0),
            "description": "Соревновательный забег Амангельды рэйс (2 дня)",
            "location": "Алматы",
            "distance": 42.0,
            "difficulty": Difficulty.HARD,
            "sport_type": SportType.TRAIL,
            "duration": 600,
            "max_participants": 30,
        },
        {
            "title": "SRG выезд (Кольсай, Кетмень)",
            "date": datetime(2026, 1, 24, 6, 0),
            "description": "Выездная тренировка в Кольсай и Кетмень (2 дня)",
            "location": "Кольсай, Кетмень",
            "distance": 35.0,
            "difficulty": Difficulty.HARD,
            "sport_type": SportType.TRAIL,
            "duration": 720,
            "max_participants": 15,
        },
        {
            "title": "Поляна Шукур + БАО",
            "date": datetime(2026, 1, 30, 8, 30),
            "description": "Поляна Шукур + БАО 20 km 1200 D+",
            "location": "Поляна Шукур, Алматы",
            "distance": 20.0,
            "difficulty": Difficulty.MEDIUM,
            "sport_type": SportType.TRAIL,
            "max_participants": 20,
        },
    ]

    created_activities = []
    for activity_data in activities_data:
        # Determine if past or upcoming
        status = ActivityStatus.COMPLETED if activity_data["date"] < datetime.now() else ActivityStatus.UPCOMING

        activity = Activity(
            title=activity_data["title"],
            description=activity_data.get("description"),
            date=activity_data["date"],
            location=activity_data["location"],
            club_id=club.id,
            creator_id=admin_user.id,
            sport_type=activity_data.get("sport_type", SportType.RUNNING),
            difficulty=activity_data.get("difficulty", Difficulty.MEDIUM),
            distance=activity_data.get("distance"),
            duration=activity_data.get("duration"),
            max_participants=activity_data.get("max_participants"),
            visibility=ActivityVisibility.PRIVATE_CLUB,
            status=status
        )
        db.add(activity)
        created_activities.append(activity)

    db.commit()
    print(f"[SUCCESS] Created {len(created_activities)} SRG activities")
    return created_activities


def create_nike_club(db: Session, users: dict) -> Club:
    """Create Nike Running Club"""
    print("\n[NIKE] Creating Nike Running Club...")

    admin_user = users[5414820474]
    club = Club(
        name="Nike Running Club",
        description="Открытый беговой клуб Nike. Регулярные тренировки для всех уровней подготовки. Присоединяйтесь!",
        creator_id=admin_user.id,
        is_paid=False,
    )
    db.add(club)
    db.commit()
    db.refresh(club)

    # Add admin as organizer
    db.add(Membership(user_id=admin_user.id, club_id=club.id, role=UserRole.ORGANIZER))

    # Add 1 more organizer
    db.add(Membership(user_id=users[667890123].id, club_id=club.id, role=UserRole.ORGANIZER))

    # Add 18 more members (total 20, can overlap with other clubs)
    member_ids = [
        234567890, 345678901, 456789012, 567890123, 778901234,
        889012345, 990123456, 101234567, 202345678, 303456789,
        404567890, 505678901, 606789012, 707890123, 808901234,
        909012345, 110123456, 220234567
    ]

    for tid in member_ids:
        db.add(Membership(user_id=users[tid].id, club_id=club.id, role=UserRole.MEMBER))

    db.commit()
    print(f"[SUCCESS] Created Nike Running Club with {len(member_ids) + 2} members")
    return club


def create_nike_recurring_activities(db: Session, club: Club, users: dict):
    """Create recurring Nike activities (every week for next 6 months)"""
    print("\n[NIKE] Creating Nike recurring activities...")

    admin_user = users[5414820474]
    start_date = datetime(2025, 12, 12)  # Today
    end_date = start_date + timedelta(days=180)  # 6 months

    activities_created = 0
    current_date = start_date

    while current_date <= end_date:
        weekday = current_date.weekday()

        # Tuesday - Terracourse
        if weekday == 1:  # Tuesday
            activity = Activity(
                title="Пробежка на терренкуре",
                description="Легкая восстановительная пробежка на терренкуре",
                date=current_date.replace(hour=18, minute=0),
                location="Терренкур, Алматы",
                club_id=club.id,
                creator_id=admin_user.id,
                sport_type=SportType.RUNNING,
                difficulty=Difficulty.EASY,
                distance=5.0,
                duration=45,
                visibility=ActivityVisibility.PUBLIC,
                status=ActivityStatus.COMPLETED if current_date < datetime.now() else ActivityStatus.UPCOMING
            )
            db.add(activity)
            activities_created += 1

        # Thursday - Intervals
        elif weekday == 3:  # Thursday
            activity = Activity(
                title="Интервалы на центральном стадионе",
                description="Интервальная тренировка для развития скорости",
                date=current_date.replace(hour=18, minute=30),
                location="Центральный стадион, Алматы",
                club_id=club.id,
                creator_id=admin_user.id,
                sport_type=SportType.RUNNING,
                difficulty=Difficulty.MEDIUM,
                distance=8.0,
                duration=60,
                visibility=ActivityVisibility.PUBLIC,
                status=ActivityStatus.COMPLETED if current_date < datetime.now() else ActivityStatus.UPCOMING
            )
            db.add(activity)
            activities_created += 1

        # Saturday - Long run
        elif weekday == 5:  # Saturday
            activity = Activity(
                title="Лонг в парке Первого Президента",
                description="Длительная пробежка в парке",
                date=current_date.replace(hour=9, minute=0),
                location="Парк Первого Президента, Алматы",
                club_id=club.id,
                creator_id=admin_user.id,
                sport_type=SportType.RUNNING,
                difficulty=Difficulty.MEDIUM,
                distance=15.0,
                duration=120,
                visibility=ActivityVisibility.PUBLIC,
                status=ActivityStatus.COMPLETED if current_date < datetime.now() else ActivityStatus.UPCOMING
            )
            db.add(activity)
            activities_created += 1

        current_date += timedelta(days=1)

    db.commit()
    print(f"[SUCCESS] Created {activities_created} Nike recurring activities")


def create_climbing_club(db: Session, users: dict) -> Club:
    """Create climbing club with unique members"""
    print("\n[CLIMBING] Creating Almaty Alpine Club...")

    # Pick a unique creator
    creator = users[667890123]

    club = Club(
        name="Almaty Alpine Club",
        description="Клуб альпинистов Алматы. Восхождения, скалолазание, альпинистские экспедиции. Закрытый клуб.",
        creator_id=creator.id,
        is_paid=False,
    )
    db.add(club)
    db.commit()
    db.refresh(club)

    # Add creator as admin
    db.add(Membership(user_id=creator.id, club_id=club.id, role=UserRole.ADMIN))

    # Add 1 organizer
    db.add(Membership(user_id=users[778901234].id, club_id=club.id, role=UserRole.ORGANIZER))

    # Add unique members (not in other clubs)
    unique_members = [889012345, 990123456, 101234567, 202345678]

    for tid in unique_members:
        db.add(Membership(user_id=users[tid].id, club_id=club.id, role=UserRole.MEMBER))

    db.commit()
    print(f"[SUCCESS] Created Almaty Alpine Club with {len(unique_members) + 2} members")

    # Create some activities
    print("   Creating climbing activities...")
    activities_data = [
        {
            "title": "Восхождение на пик Комсомола",
            "date": datetime(2026, 1, 15, 6, 0),
            "description": "Альпинистское восхождение на пик Комсомола (4376 м)",
            "location": "Пик Комсомола, Алматы",
            "distance": 18.0,
            "difficulty": Difficulty.HARD,
            "sport_type": SportType.HIKING,
            "max_participants": 8,
        },
        {
            "title": "Скалолазание на Арасане",
            "date": datetime(2026, 2, 1, 10, 0),
            "description": "Тренировка на скалах Арасана",
            "location": "Арасан, Алматы",
            "distance": 3.0,
            "difficulty": Difficulty.MEDIUM,
            "sport_type": SportType.HIKING,
            "max_participants": 10,
        },
    ]

    for activity_data in activities_data:
        activity = Activity(
            title=activity_data["title"],
            description=activity_data["description"],
            date=activity_data["date"],
            location=activity_data["location"],
            club_id=club.id,
            creator_id=creator.id,
            sport_type=activity_data["sport_type"],
            difficulty=activity_data["difficulty"],
            distance=activity_data.get("distance"),
            max_participants=activity_data.get("max_participants"),
            visibility=ActivityVisibility.PRIVATE_CLUB,
            status=ActivityStatus.UPCOMING
        )
        db.add(activity)

    db.commit()
    print(f"   [SUCCESS] Created {len(activities_data)} climbing activities")

    return club


def create_standalone_groups(db: Session, users: dict):
    """Create 2 standalone groups"""
    print("\n[GROUPS] Creating standalone groups...")

    # Closed group with 10 unique members
    closed_group_creator = users[303456789]
    closed_group = Group(
        name="Trail Running Almaty",
        description="Закрытая группа любителей трейлраннинга",
        club_id=None,
        is_open=False
    )
    db.add(closed_group)
    db.commit()
    db.refresh(closed_group)

    # Add organizer
    db.add(Membership(user_id=closed_group_creator.id, group_id=closed_group.id, role=UserRole.ORGANIZER))

    # Add 9 unique members
    closed_members = [404567890, 505678901, 606789012, 707890123, 808901234,
                      909012345, 110123456, 220234567, 123456789]
    for tid in closed_members:
        db.add(Membership(user_id=users[tid].id, group_id=closed_group.id, role=UserRole.MEMBER))

    db.commit()
    print(f"[SUCCESS] Created closed group 'Trail Running Almaty' with {len(closed_members) + 1} members")

    # Create activity for closed group
    activity = Activity(
        title="Трейл на Кок-Жайляу",
        description="Вечерний трейл на Кок-Жайляу",
        date=datetime(2025, 12, 20, 17, 0),
        location="Кок-Жайляу, Алматы",
        group_id=closed_group.id,
        creator_id=closed_group_creator.id,
        sport_type=SportType.TRAIL,
        difficulty=Difficulty.MEDIUM,
        distance=12.0,
        max_participants=15,
        visibility=ActivityVisibility.PRIVATE_GROUP,
        status=ActivityStatus.UPCOMING
    )
    db.add(activity)
    db.commit()

    # Open group with 5 members (any)
    open_group_creator = users[112345678]
    open_group = Group(
        name="Parkrun Almaty",
        description="Открытая группа для паркранов по субботам",
        club_id=None,
        is_open=True
    )
    db.add(open_group)
    db.commit()
    db.refresh(open_group)

    # Add organizer
    db.add(Membership(user_id=open_group_creator.id, group_id=open_group.id, role=UserRole.ORGANIZER))

    # Add 4 members (can be from other groups)
    open_members = [234567890, 345678901, 456789012, 567890123]
    for tid in open_members:
        db.add(Membership(user_id=users[tid].id, group_id=open_group.id, role=UserRole.MEMBER))

    db.commit()
    print(f"[SUCCESS] Created open group 'Parkrun Almaty' with {len(open_members) + 1} members")

    # Create activities for open group (recurring Saturday parkruns)
    print("   Creating parkrun activities...")
    start_date = datetime(2025, 12, 14)  # Next Saturday
    for i in range(12):  # 12 weeks
        activity_date = start_date + timedelta(weeks=i)
        activity = Activity(
            title="Parkrun Almaty",
            description="Еженедельный бесплатный забег 5 км",
            date=activity_date.replace(hour=9, minute=0),
            location="Парк Горького, Алматы",
            group_id=open_group.id,
            creator_id=open_group_creator.id,
            sport_type=SportType.RUNNING,
            difficulty=Difficulty.EASY,
            distance=5.0,
            duration=30,
            visibility=ActivityVisibility.PUBLIC,
            status=ActivityStatus.UPCOMING
        )
        db.add(activity)

    db.commit()
    print(f"   [SUCCESS] Created 12 parkrun activities")


def create_participations(db: Session):
    """Register 30% of users to activities based on their memberships"""
    print("\n[PARTICIPATIONS] Creating participations...")

    activities = db.query(Activity).all()
    total_participations = 0

    for activity in activities:
        # Get eligible users based on activity visibility
        eligible_users = []

        if activity.club_id:
            # Club activity - get club members
            memberships = db.query(Membership).filter(
                Membership.club_id == activity.club_id
            ).all()
            eligible_users = [m.user_id for m in memberships]
        elif activity.group_id:
            # Group activity - get group members
            memberships = db.query(Membership).filter(
                Membership.group_id == activity.group_id
            ).all()
            eligible_users = [m.user_id for m in memberships]
        else:
            # Public/standalone activity - all users
            all_users = db.query(User).all()
            eligible_users = [u.id for u in all_users]

        # Register 30% of eligible users
        num_participants = max(1, int(len(eligible_users) * 0.3))
        selected_users = random.sample(eligible_users, min(num_participants, len(eligible_users)))

        for user_id in selected_users:
            # Check if already registered
            existing = db.query(Participation).filter(
                Participation.activity_id == activity.id,
                Participation.user_id == user_id
            ).first()

            if not existing:
                # Determine status based on activity status
                if activity.status == ActivityStatus.COMPLETED:
                    part_status = ParticipationStatus.COMPLETED
                    attended = random.choice([True, True, True, False])  # 75% attended
                else:
                    part_status = ParticipationStatus.REGISTERED
                    attended = False

                participation = Participation(
                    activity_id=activity.id,
                    user_id=user_id,
                    status=part_status,
                    attended=attended,
                    payment_status=PaymentStatus.NOT_REQUIRED
                )
                db.add(participation)
                total_participations += 1

    db.commit()
    print(f"[SUCCESS] Created {total_participations} participations")


def seed_all():
    """Main function to seed all data"""
    print("=" * 60)
    print("Starting Ayda Run Database Seeding")
    print("=" * 60)

    # Initialize database
    init_db()

    # Create session
    db = SessionLocal()

    try:
        # Clear existing data
        clear_database(db)

        # Create users
        users = create_users(db)

        # Create SRG club
        srg_club, srg_groups = create_srg_club(db, users)
        srg_activities = create_srg_activities(db, srg_club, srg_groups, users)

        # Create Nike club
        nike_club = create_nike_club(db, users)
        create_nike_recurring_activities(db, nike_club, users)

        # Create climbing club
        climbing_club = create_climbing_club(db, users)

        # Create standalone groups
        create_standalone_groups(db, users)

        # Create participations
        create_participations(db)

        print("\n" + "=" * 60)
        print("[SUCCESS] Database seeding completed successfully!")
        print("=" * 60)

        # Summary
        print("\nSummary:")
        print(f"   Users: {db.query(User).count()}")
        print(f"   Clubs: {db.query(Club).count()}")
        print(f"   Groups: {db.query(Group).count()}")
        print(f"   Activities: {db.query(Activity).count()}")
        print(f"   Memberships: {db.query(Membership).count()}")
        print(f"   Participations: {db.query(Participation).count()}")

    except Exception as e:
        print(f"\n[ERROR] Error during seeding: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_all()
