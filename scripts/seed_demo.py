"""
Demo Data Seeding Script for Ayda Run

Creates realistic demo data for showcasing the application:
- 60 demo users with different activity patterns
- 5 clubs (3 open, 2 closed)
- Activities from 2 weeks ago to 2 months forward
- Realistic attendance patterns (70% average)

Usage:
    python scripts/seed_demo.py
"""

import sys
import os

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from storage.db import (
    SessionLocal, init_db,
    User, Club, Group, Activity, Membership, Participation, RecurringTemplate,
    UserRole, SportType, Difficulty, ActivityVisibility, ActivityStatus,
    ParticipationStatus, PaymentStatus, MembershipSource
)
import random

# ============= CONFIGURATION =============

# Admin telegram_id - this user will be the creator of all demo clubs/activities
# Set this to your real Telegram ID for production
ADMIN_TELEGRAM_ID = 5414820474  # Your Telegram ID

# ============= DEMO USER DATA =============

DEMO_FIRST_NAMES = [
    "Александр", "Мария", "Дмитрий", "Анна", "Сергей", "Елена", "Иван", "Ольга",
    "Андрей", "Татьяна", "Михаил", "Наталья", "Алексей", "Ирина", "Владимир", "Екатерина",
    "Максим", "Светлана", "Роман", "Юлия", "Денис", "Виктория", "Павел", "Марина",
    "Николай", "Анастасия", "Артём", "Дарья", "Игорь", "Полина", "Олег", "Кристина",
    "Евгений", "Алина", "Антон", "Вероника", "Валерий", "Ксения", "Вячеслав", "Людмила",
    "Кирилл", "Валентина", "Григорий", "Нина", "Константин", "Оксана", "Леонид", "Галина",
    "Станислав", "Любовь", "Тимур", "Диана", "Владислав", "Регина", "Фёдор", "Лариса",
    "Арсений", "София", "Богдан", "Милана", "Матвей", "Камила"
]

DEMO_LAST_NAMES = [
    "Иванов", "Петров", "Сидоров", "Смирнов", "Кузнецов", "Попов", "Васильев", "Соколов",
    "Морозов", "Новиков", "Волков", "Федоров", "Михайлов", "Борисов", "Орлов", "Григорьев",
    "Степанов", "Николаев", "Захаров", "Романов", "Павлов", "Семенов", "Егоров", "Козлов",
    "Виноградов", "Лебедев", "Макаров", "Беляев", "Попова", "Соловьев", "Никитин", "Титов",
    "Алексеев", "Ковалев", "Белов", "Киселев", "Медведев", "Жуков", "Крылов", "Баранов",
    "Зайцев", "Комаров", "Филиппов", "Громов", "Дмитриев", "Максимов", "Тарасов", "Воробьев",
    "Гусев", "Андреев", "Калинин", "Карпов", "Власов", "Мельников", "Денисов", "Давыдов",
    "Фролов", "Ильин", "Кондратьев", "Афанасьев"
]

DEMO_USERNAMES = [
    "runner_almaty", "trail_master", "sky_runner", "mountain_lover", "active_life",
    "fit_zone", "outdoor_pro", "peak_hunter", "trail_wolf", "run_wild",
    "urban_runner", "nature_walk", "hike_more", "summit_seeker", "endurance_pro",
    "speed_demon", "long_distance", "marathon_man", "ultra_runner", "fast_feet",
    "climb_high", "explore_kz", "adventure_time", "outdoor_kz", "wild_almaty",
    "trail_blazer", "mountain_goat", "hill_runner", "valley_hiker", "ridge_walker",
    "fitness_life", "sport_almaty", "active_kz", "run_free", "move_more",
    "health_first", "strong_body", "power_run", "swift_runner", "agile_athlete",
    "peak_performance", "top_shape", "fit_forever", "wellness_kz", "vital_energy",
    "dynamic_life", "motion_master", "stride_strong", "pace_setter", "goal_crusher",
    "distance_king", "endurance_queen", "cardio_master", "stamina_pro", "power_athlete",
    "speed_king", "trail_queen", "mountain_master", "summit_pro", "alpine_athlete"
]

# User personas for realistic behavior
class UserPersona:
    SUPER_ACTIVE = {'ratio': 0.20, 'attendance': 0.90}  # 20% users, 90% attendance
    REGULAR = {'ratio': 0.40, 'attendance': 0.70}       # 40% users, 70% attendance
    CASUAL = {'ratio': 0.30, 'attendance': 0.40}        # 30% users, 40% attendance
    GHOST = {'ratio': 0.10, 'attendance': 0.10}         # 10% users, 10% attendance


def generate_demo_users(count=60):
    """Generate demo user data"""
    users = []
    used_names = set()

    for i in range(count):
        # Generate unique name combination
        while True:
            first = random.choice(DEMO_FIRST_NAMES)
            last = random.choice(DEMO_LAST_NAMES)
            name_key = f"{first}_{last}"
            if name_key not in used_names:
                used_names.add(name_key)
                break

        # Assign persona based on ratios
        rand = random.random()
        if rand < 0.20:
            persona = 'super_active'
        elif rand < 0.60:  # 0.20 + 0.40
            persona = 'regular'
        elif rand < 0.90:  # 0.60 + 0.30
            persona = 'casual'
        else:
            persona = 'ghost'

        users.append({
            'telegram_id': 900000000 + i,
            'username': DEMO_USERNAMES[i] if i < len(DEMO_USERNAMES) else f"demo_user_{i}",
            'first_name': first,
            'last_name': last,
            'persona': persona
        })

    return users


# ============= CLUB CONFIGURATIONS =============

CLUB_CONFIGS = [
    {
        'name': 'Mountain Trail Runners',
        'description': 'Трейловый клуб для бега в горах. Тренировки для разных уровней подготовки. Только по приглашениям.',
        'is_open': False,
        'has_groups': True,
        'groups': [
            {'name': 'Начинающие', 'description': 'Группа для начинающих трейлраннеров', 'size': 6},
            {'name': 'Средний уровень', 'description': 'Группа для опытных любителей', 'size': 6},
            {'name': 'Продвинутые', 'description': 'Группа для продвинутых спортсменов', 'size': 6},
        ],
        'total_members': 18,
        'recurring_activities': [
            {'day': 2, 'time': '06:00', 'title': 'Утренний бег + СБУ', 'sport': SportType.RUNNING,
             'difficulty': Difficulty.MEDIUM, 'distance': 8, 'location': 'Терренкур'},
            {'day': 2, 'time': '18:00', 'title': 'Вечерний бег + СБУ', 'sport': SportType.RUNNING,
             'difficulty': Difficulty.EASY, 'distance': 6, 'location': 'Парк'},
            {'day': 5, 'time': '08:00', 'title': 'Длинный трейл', 'sport': SportType.TRAIL,
             'difficulty': Difficulty.HARD, 'distance': 18, 'location': 'Горы'},
        ]
    },
    {
        'name': 'City Runners Club',
        'description': 'Городской беговой клуб для всех уровней. Открыт для всех желающих!',
        'is_open': True,
        'has_groups': False,
        'total_members': 20,
        'recurring_activities': [
            {'day': 1, 'time': '18:00', 'title': 'Пробежка 10 км', 'sport': SportType.RUNNING,
             'difficulty': Difficulty.MEDIUM, 'distance': 10, 'location': 'Парк Горького'},
            {'day': 3, 'time': '18:30', 'title': 'Стадион + СБУ', 'sport': SportType.RUNNING,
             'difficulty': Difficulty.MEDIUM, 'distance': 8, 'location': 'Центральный стадион'},
            {'day': 5, 'time': '09:00', 'title': 'Длинная пробежка 15 км', 'sport': SportType.RUNNING,
             'difficulty': Difficulty.MEDIUM, 'distance': 15, 'location': 'Парк Первого Президента'},
            {'day': 4, 'time': '19:00', 'title': 'Воркаут', 'sport': SportType.WORKOUT,
             'difficulty': Difficulty.EASY, 'duration': 60, 'location': 'Спортплощадка'},
            {'day': 6, 'time': '10:00', 'title': 'Йога для бегунов', 'sport': SportType.YOGA,
             'difficulty': Difficulty.EASY, 'duration': 75, 'location': 'Студия йоги'},
        ]
    },
    {
        'name': 'Almaty Hiking Community',
        'description': 'Сообщество любителей хайкинга и горных походов. Присоединяйтесь к нам!',
        'is_open': True,
        'has_groups': False,
        'total_members': 15,
        'recurring_activities': [
            {'day': 5, 'time': '08:00', 'title': 'Хайк средней сложности', 'sport': SportType.HIKING,
             'difficulty': Difficulty.MEDIUM, 'distance': 12, 'location': 'Кок-Жайляу'},
            {'day': 6, 'time': '09:00', 'title': 'Семейный хайк', 'sport': SportType.HIKING,
             'difficulty': Difficulty.EASY, 'distance': 8, 'location': 'Медео'},
        ]
    },
    {
        'name': 'Alpine Explorers',
        'description': 'Клуб для серьезных восхождений и альпинизма. Закрытый клуб.',
        'is_open': False,
        'has_groups': False,
        'total_members': 8,
        'recurring_activities': []  # Only special events
    },
    {
        'name': 'Trail Wolves',
        'description': 'Соревновательный трейл-клуб. Подготовка к ультрамарафонам. Закрытый.',
        'is_open': False,
        'has_groups': True,
        'groups': [
            {'name': 'Solo Runners', 'description': 'Индивидуальные тренировки', 'size': 6},
            {'name': 'Team Training', 'description': 'Командная подготовка', 'size': 6},
        ],
        'total_members': 12,
        'recurring_activities': [
            {'day': 6, 'time': '07:00', 'title': 'Длинный трейл', 'sport': SportType.TRAIL,
             'difficulty': Difficulty.HARD, 'distance': 25, 'location': 'Бутаковское ущелье'},
        ]
    },
]


# ============= MAIN SEEDING FUNCTIONS =============

def create_demo_users(db: Session, user_data: list) -> dict:
    """Create demo users"""
    print(f"\n[USERS] Creating {len(user_data)} demo users...")
    users = {}

    for data in user_data:
        user = User(
            telegram_id=data['telegram_id'],
            username=data['username'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            is_demo=True,  # Mark as demo
            has_completed_onboarding=True
        )
        db.add(user)
        users[data['telegram_id']] = {
            'user': user,
            'persona': data['persona']
        }

    db.commit()

    # Count personas
    personas = {'super_active': 0, 'regular': 0, 'casual': 0, 'ghost': 0}
    for u in users.values():
        personas[u['persona']] += 1

    print(f"[SUCCESS] Created {len(users)} demo users:")
    print(f"   - Super Active: {personas['super_active']} ({personas['super_active']/len(users)*100:.0f}%)")
    print(f"   - Regular: {personas['regular']} ({personas['regular']/len(users)*100:.0f}%)")
    print(f"   - Casual: {personas['casual']} ({personas['casual']/len(users)*100:.0f}%)")
    print(f"   - Ghost: {personas['ghost']} ({personas['ghost']/len(users)*100:.0f}%)")

    return users


def create_demo_clubs(db: Session, users: dict, admin_user: User):
    """Create all demo clubs with groups and members"""
    print(f"\n[CLUBS] Creating {len(CLUB_CONFIGS)} demo clubs...")

    clubs_created = []
    all_user_ids = list(users.keys())
    used_users = set()

    for config in CLUB_CONFIGS:
        print(f"\n  [{config['name']}]")

        # Create club
        club = Club(
            name=config['name'],
            description=config['description'],
            creator_id=admin_user.id,
            city='Almaty',  # Set default city
            is_paid=False,
            is_open=config['is_open'],
            is_demo=True  # Mark as demo
        )
        db.add(club)
        db.commit()
        db.refresh(club)

        # Add admin as organizer
        db.add(Membership(
            user_id=admin_user.id,
            club_id=club.id,
            role=UserRole.ORGANIZER,
            source=MembershipSource.MANUAL_REGISTRATION
        ))

        # Select members for this club (allow overlap)
        total_members = config['total_members']
        available_users = [uid for uid in all_user_ids if uid != 1]
        selected_users = random.sample(available_users, min(total_members, len(available_users)))

        if config['has_groups']:
            # Create groups and distribute members
            groups = []
            for group_config in config['groups']:
                group = Group(
                    name=group_config['name'],
                    description=group_config['description'],
                    club_id=club.id,
                    creator_id=admin_user.id,
                    city='Almaty',  # Set default city
                    is_open=False,
                    is_demo=True  # Mark as demo
                )
                db.add(group)
                db.commit()
                db.refresh(group)
                groups.append(group)

                # Assign members to group
                group_size = group_config['size']
                group_members = selected_users[:group_size]
                selected_users = selected_users[group_size:]

                # Add trainer
                if group_members:
                    trainer_id = group_members[0]
                    db.add(Membership(
                        user_id=users[trainer_id]['user'].id,
                        club_id=club.id,
                        role=UserRole.TRAINER,
                        source=MembershipSource.MANUAL_REGISTRATION
                    ))
                    db.add(Membership(
                        user_id=users[trainer_id]['user'].id,
                        group_id=group.id,
                        role=UserRole.TRAINER,
                        source=MembershipSource.MANUAL_REGISTRATION
                    ))

                    # Add regular members
                    for uid in group_members[1:]:
                        db.add(Membership(
                            user_id=users[uid]['user'].id,
                            club_id=club.id,
                            role=UserRole.MEMBER,
                            source=MembershipSource.MANUAL_REGISTRATION
                        ))
                        db.add(Membership(
                            user_id=users[uid]['user'].id,
                            group_id=group.id,
                            role=UserRole.MEMBER,
                            source=MembershipSource.MANUAL_REGISTRATION
                        ))

                print(f"     - Group '{group.name}': {len(group_members)} members")

            club.groups_list = groups
        else:
            # Add members directly to club
            for uid in selected_users:
                db.add(Membership(
                    user_id=users[uid]['user'].id,
                    club_id=club.id,
                    role=UserRole.MEMBER,
                    source=MembershipSource.MANUAL_REGISTRATION
                ))

            print(f"     - {len(selected_users)} members")

        db.commit()

        clubs_created.append({
            'club': club,
            'config': config,
            'groups': club.groups_list if config['has_groups'] else []
        })

        print(f"  [SUCCESS] Created {config['name']}")

    print(f"\n[SUCCESS] Created {len(clubs_created)} clubs")
    return clubs_created


def create_recurring_activities(db: Session, club_data: dict, users: dict, admin_user: User):
    """Create recurring activities for a club using RecurringTemplate"""
    club = club_data['club']
    config = club_data['config']

    if not config['recurring_activities']:
        return []

    print(f"\n  Creating recurring activities for {club.name}...")

    # Calculate date range: 2 weeks ago to 2 months forward
    start_date = datetime.now() - timedelta(weeks=2)
    end_date = datetime.now() + timedelta(weeks=8)  # 2 months

    activities_created = []

    for activity_config in config['recurring_activities']:
        day_of_week = activity_config['day']  # 0=Mon, 6=Sun
        time_str = activity_config['time']

        # Create RecurringTemplate first
        template = RecurringTemplate(
            title=activity_config['title'],
            day_of_week=day_of_week,
            time_of_day=time_str,
            frequency=4,  # Weekly
            total_occurrences=12,  # 3 months worth
            description=f"Регулярная тренировка {club.name}",
            location=activity_config['location'],
            sport_type=activity_config['sport'],
            difficulty=activity_config['difficulty'],
            distance=activity_config.get('distance'),
            duration=activity_config.get('duration'),
            club_id=club.id,
            creator_id=admin_user.id,
            is_demo=True  # Mark as demo
        )
        db.add(template)
        db.commit()
        db.refresh(template)

        # Find first occurrence
        hour, minute = map(int, time_str.split(':'))
        current_date = start_date
        while current_date.weekday() != day_of_week:
            current_date += timedelta(days=1)

        # Create weekly occurrences linked to template
        occurrence_count = 0
        sequence = 1
        while current_date <= end_date:
            activity_date = current_date.replace(hour=hour, minute=minute, second=0, microsecond=0)

            # Determine status
            if activity_date < datetime.now():
                status = ActivityStatus.COMPLETED
            else:
                status = ActivityStatus.UPCOMING

            activity = Activity(
                title=activity_config['title'],
                description=f"Регулярная тренировка {club.name}",
                date=activity_date,
                location=activity_config['location'],
                club_id=club.id,
                creator_id=admin_user.id,
                city='Almaty',
                sport_type=activity_config['sport'],
                difficulty=activity_config['difficulty'],
                distance=activity_config.get('distance'),
                duration=activity_config.get('duration'),
                visibility=ActivityVisibility.PUBLIC if club.is_open else ActivityVisibility.PRIVATE_CLUB,
                status=status,
                recurring_template_id=template.id,
                recurring_sequence=sequence,
                is_demo=True
            )
            db.add(activity)
            activities_created.append(activity)
            occurrence_count += 1
            sequence += 1

            # Next week
            current_date += timedelta(weeks=1)

        # Update template generated_count
        template.generated_count = occurrence_count

        print(f"     - {activity_config['title']}: {occurrence_count} occurrences (recurring)")

    db.commit()
    return activities_created


def create_participations_for_activities(db: Session, activities: list, users: dict, club: Club):
    """Create realistic participations for activities"""
    total_participations = 0

    # Get club members
    memberships = db.query(Membership).filter(Membership.club_id == club.id).all()
    member_ids = [m.user_id for m in memberships]

    for activity in activities:
        # Get eligible users (club members)
        eligible_user_data = [users[tid] for tid, data in users.items()
                             if data['user'].id in member_ids]

        if not eligible_user_data:
            continue

        # Each user decides to register based on persona
        for user_data_dict in eligible_user_data:
            user_obj = user_data_dict['user']
            persona = user_data_dict['persona']

            # 50% chance to register for upcoming, 70% for completed
            if activity.status == ActivityStatus.UPCOMING:
                register_chance = 0.5
            else:
                register_chance = 0.7

            if random.random() < register_chance:
                # Determine attendance based on persona
                if activity.status == ActivityStatus.COMPLETED:
                    attendance_rates = {
                        'super_active': 0.90,
                        'regular': 0.70,
                        'casual': 0.40,
                        'ghost': 0.10
                    }
                    attended = random.random() < attendance_rates[persona]
                    part_status = ParticipationStatus.ATTENDED if attended else ParticipationStatus.MISSED
                else:
                    attended = False
                    part_status = ParticipationStatus.REGISTERED

                participation = Participation(
                    activity_id=activity.id,
                    user_id=user_obj.id,
                    status=part_status,
                    attended=attended,
                    payment_status=PaymentStatus.NOT_REQUIRED
                )
                db.add(participation)
                total_participations += 1

    db.commit()
    return total_participations


def create_special_events(db: Session, clubs_data: list, users: dict, admin_user: User):
    """Create special one-time events for clubs"""
    print(f"\n[SPECIAL EVENTS] Creating special events...")

    events = []

    # Find Alpine Explorers
    alpine_club = None
    for club_data in clubs_data:
        if club_data['config']['name'] == 'Alpine Explorers':
            alpine_club = club_data['club']
            break

    if alpine_club:
        # Create special alpine events
        special_events = [
            {
                'title': 'Восхождение на пик Комсомола',
                'date': datetime.now() + timedelta(days=20),
                'description': 'Альпинистское восхождение на пик Комсомола (4376 м)',
                'location': 'Пик Комсомола',
                'distance': 18.0,
                'difficulty': Difficulty.HARD,
                'sport_type': SportType.HIKING,
            },
            {
                'title': 'Ледовые занятия на леднике',
                'date': datetime.now() + timedelta(days=35),
                'description': 'Техническая подготовка на леднике',
                'location': 'Туюксу',
                'distance': 10.0,
                'difficulty': Difficulty.HARD,
                'sport_type': SportType.HIKING,
            },
        ]

        for event_data in special_events:
            activity = Activity(
                title=event_data['title'],
                description=event_data['description'],
                date=event_data['date'],
                location=event_data['location'],
                club_id=alpine_club.id,
                creator_id=admin_user.id,
                city='Almaty',  # Set default city
                sport_type=event_data['sport_type'],
                difficulty=event_data['difficulty'],
                distance=event_data['distance'],
                visibility=ActivityVisibility.PRIVATE_CLUB,
                status=ActivityStatus.UPCOMING,
                is_demo=True
            )
            db.add(activity)
            events.append(activity)

        db.commit()
        print(f"  [SUCCESS] Created {len(events)} special events")

    return events


def seed_demo_data():
    """Main function to seed all demo data"""
    print("=" * 70)
    print(" " * 20 + "DEMO DATA SEEDING")
    print("=" * 70)

    # Initialize database
    init_db()
    db = SessionLocal()

    try:
        # Get or create admin user
        admin_user = db.query(User).filter(User.telegram_id == ADMIN_TELEGRAM_ID).first()
        if not admin_user:
            print(f"[INFO] Creating admin user (telegram_id={ADMIN_TELEGRAM_ID})...")
            admin_user = User(
                telegram_id=ADMIN_TELEGRAM_ID,
                username="admin",
                first_name="Admin",
                is_demo=False,  # Admin is NOT demo data
                has_completed_onboarding=True
            )
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)
            print(f"[SUCCESS] Admin user created with id={admin_user.id}")

        # Check if demo data already exists
        existing_demo = db.query(User).filter(User.is_demo == True).first()
        if existing_demo:
            print("\n[WARNING] Demo data already exists!")
            print("Please run 'python scripts/clear_demo.py' first to remove existing demo data.")
            return

        # Generate demo users
        user_data = generate_demo_users(60)
        users = create_demo_users(db, user_data)

        # Create clubs with groups
        clubs_data = create_demo_clubs(db, users, admin_user)

        # Create recurring activities for each club
        all_activities = []
        for club_data in clubs_data:
            activities = create_recurring_activities(db, club_data, users, admin_user)
            all_activities.extend(activities)

            # Create participations
            if activities:
                print(f"  Creating participations for {club_data['club'].name}...")
                total = create_participations_for_activities(db, activities, users, club_data['club'])
                print(f"     - Created {total} participations")

        # Create special events
        special_events = create_special_events(db, clubs_data, users, admin_user)
        if special_events:
            # Create participations for special events
            for event in special_events:
                activities = [event]
                club = db.query(Club).filter(Club.id == event.club_id).first()
                total = create_participations_for_activities(db, activities, users, club)

        print("\n" + "=" * 70)
        print(" " * 20 + "SEEDING COMPLETED!")
        print("=" * 70)

        # Summary
        print("\nSummary:")
        print(f"   Demo Users: {db.query(User).filter(User.is_demo == True).count()}")
        print(f"   Demo Clubs: {db.query(Club).filter(Club.is_demo == True).count()}")
        print(f"   Demo Groups: {db.query(Group).filter(Group.is_demo == True).count()}")
        print(f"   Demo Recurring Templates: {db.query(RecurringTemplate).filter(RecurringTemplate.is_demo == True).count()}")
        print(f"   Demo Activities: {db.query(Activity).filter(Activity.is_demo == True).count()}")
        print(f"   Total Participations: {db.query(Participation).count()}")

        print("\n[INFO] To remove demo data, run: python scripts/clear_demo.py")

    except Exception as e:
        print(f"\n[ERROR] Error during seeding: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_demo_data()
