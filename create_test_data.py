# -*- coding: utf-8 -*-
"""
Create test data for Ayda Run

This script creates:
- 1 test user
- 3 sample activities (running, hiking, cycling)
"""

from datetime import datetime, timedelta
from storage.db import (
    SessionLocal, User, Activity,
    SportType, Difficulty, ActivityVisibility, ActivityStatus
)

def create_test_data():
    """Create test user and activities"""
    db = SessionLocal()
    
    try:
        # Create test user
        test_user = db.query(User).filter(User.telegram_id == 123456789).first()
        if not test_user:
            test_user = User(
                telegram_id=123456789,
                username="test_user",
                first_name="Тестовый Пользователь"
            )
            db.add(test_user)
            db.commit()
            db.refresh(test_user)
            print(f"[SUCCESS] Created test user: {test_user.first_name} (@{test_user.username})")
        else:
            print(f"[INFO] Test user already exists: {test_user.first_name}")
        
        # Activity 1: Monday Morning Run
        activity1 = Activity(
            title="Утренняя пробежка в парке",
            description="Легкая пробежка по парку Победы. Темп комфортный, подходит для новичков. Встречаемся у главного входа.",
            date=datetime.now() + timedelta(days=1, hours=9),  # Tomorrow at 9 AM
            location="Парк Победы, главный вход",
            creator_id=test_user.id,
            sport_type=SportType.RUNNING,
            difficulty=Difficulty.EASY,
            distance=5.0,  # 5 km
            duration=35,  # 35 minutes
            max_participants=15,
            visibility=ActivityVisibility.PUBLIC,
            status=ActivityStatus.UPCOMING
        )
        
        # Activity 2:  Weekend Hiking
        activity2 = Activity(
            title="Поход в горы на выходных",
            description="Треккинг по маршруту «Красная поляна - Роза Хутор». Средняя сложность, требуется базовая физическая подготовка. С собой: вода, перекус, треккинговые палки.",
            date=datetime.now() + timedelta(days=5, hours=8),  # Next Saturday at 8 AM
            location="Красная поляна, встреча у канатной дороги",
            creator_id=test_user.id,
            sport_type=SportType.HIKING,
            difficulty=Difficulty.MEDIUM,
            distance=12.5,  # 12.5 km
            duration=240,  # 4 hours
            max_participants=20,
            visibility=ActivityVisibility.PUBLIC,
            status=ActivityStatus.UPCOMING
        )
        
        # Activity 3: Cycling Tour
        activity3 = Activity(
            title="Велопрогулка вдоль набережной",
            description="Спокойная велопрогулка по набережной. Маршрут: Олимпийский парк - Имеретинский порт - обратно. Подходит для всех уровней подготовки.",
            date=datetime.now() + timedelta(days=3, hours=17),  # In 3 days at 5 PM
            location="Олимпийский парк, фонтан",
            creator_id=test_user.id,
            sport_type=SportType.CYCLING,
            difficulty=Difficulty.EASY,
            distance=15.0,  # 15 km
            duration=90,  # 1.5 hours
            max_participants=25,
            visibility=ActivityVisibility.PUBLIC,
            status=ActivityStatus.UPCOMING
        )
        
        # Add to database
        db.add_all([activity1, activity2, activity3])
        db.commit()
        
        print(f"\n[SUCCESS] Created 3 test activities:")
        print(f"  1. {activity1.title} - {activity1.date.strftime('%d.%m.%Y %H:%M')}")
        print(f"  2. {activity2.title} - {activity2.date.strftime('%d.%m.%Y %H:%M')}")
        print(f"  3. {activity3.title} - {activity3.date.strftime('%d.%m.%Y %H:%M')}")
        
        print(f"\n[SUCCESS] Test data created successfully!")
        print(f"\nYou can now:")
        print(f"  - GET  http://localhost:8000/api/activities")
        print(f"  - GET  http://localhost:8000/api/activities/1")
        print(f"  - POST http://localhost:8000/api/activities (with auth)")
        
    except Exception as e:
        print(f"[ERROR] Error creating test data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("Creating test data for Ayda Run...\n")
    create_test_data()
