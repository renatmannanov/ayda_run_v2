# -*- coding: utf-8 -*-
"""
Create test data for Groups & Clubs

This script creates:
- 2 test clubs (SRG и Nike Run Club)
- 3 groups (2 в SRG, 1 standalone)
- Memberships для пользователей
"""

from storage.db import (
    SessionLocal, User, Club, Group, Membership, UserRole
)

def create_clubs_groups_test_data():
    """Create test clubs and groups"""
    db = SessionLocal()
    
    try:
        # Get or create test user
        test_user = db.query(User).filter(User.telegram_id == 123456789).first()
        if not test_user:
            print("[ERROR] Test user not found. Run create_test_data.py first.")
            return
        
        print(f"[INFO] Using test user: {test_user.first_name}\n")
        
        # Club 1: SRG (Sochi Running Group) - Paid club
        club_srg = Club(
            name="Sochi Running Group",
            description="Беговой клуб Сочи. Тренировки для всех уровней подготовки. Профессиональные тренеры, системный подход, приятная атмосфера.",
            creator_id=test_user.id,
            is_paid=True,
            price_per_activity=500.0,
            telegram_chat_id=None
        )
        db.add(club_srg)
        db.commit()
        db.refresh(club_srg)
        
        # Add creator as admin to SRG
        membership_srg_admin = Membership(
            user_id=test_user.id,
            club_id=club_srg.id,
            role=UserRole.ADMIN
        )
        db.add(membership_srg_admin)
        
        print(f"[SUCCESS] Created club: {club_srg.name} (paid, 500 rub)")
        
        # Group 1: Новички (within SRG)
        group_beginners = Group(
            name="Новички",
            description="Группа для начинающих бегунов. Дистанции 3-5 км, комфортный темп.",
            club_id=club_srg.id,
            is_open=False  # Invite-only through club
        )
        db.add(group_beginners)
        db.commit()
        db.refresh(group_beginners)
        
        # Add trainer for beginners group
        membership_trainer1 = Membership(
            user_id=test_user.id,
            group_id=group_beginners.id,
            role=UserRole.TRAINER
        )
        db.add(membership_trainer1)
        
        print(f"  - Group: {group_beginners.name} (club group, trainer assigned)")
        
        # Group 2: Продвинутые (within SRG)
        group_advanced = Group(
            name="Продвинутые",
            description="Группа для опытных бегунов. Дистанции 10+ км, интервальные тренировки.",
            club_id=club_srg.id,
            is_open=False
        )
        db.add(group_advanced)
        db.commit()
        db.refresh(group_advanced)
        
        membership_trainer2 = Membership(
            user_id=test_user.id,
            group_id=group_advanced.id,
            role=UserRole.TRAINER
        )
        db.add(membership_trainer2)
        
        print(f"  - Group: {group_advanced.name} (club group, trainer assigned)")
        
        # Club 2: Nike Run Club - Free/Open club
        club_nike = Club(
            name="Nike Run Club Sochi",
            description="Бесплатные пробежки Nike. Открыты для всех! Каждую среду и субботу.",
            creator_id=test_user.id,
            is_paid=False,
            price_per_activity=None,
            telegram_chat_id=None
        )
        db.add(club_nike)
        db.commit()
        db.refresh(club_nike)
        
        membership_nike_admin = Membership(
            user_id=test_user.id,
            club_id=club_nike.id,
            role=UserRole.ORGANIZER
        )
        db.add(membership_nike_admin)
        
        print(f"\n[SUCCESS] Created club: {club_nike.name} (free)")
        
        # Group 3: Standalone group (not attached to club)
        group_standalone = Group(
            name="Воскресные походы",
            description="Неформальная группа любителей походов. Ходим в горы по воскресеньям.",
            club_id=None,  # Standalone
            is_open=True  # Anyone can join
        )
        db.add(group_standalone)
        db.commit()
        db.refresh(group_standalone)
        
        membership_standalone = Membership(
            user_id=test_user.id,
            group_id=group_standalone.id,
            role=UserRole.ADMIN
        )
        db.add(membership_standalone)
        
        print(f"\n[SUCCESS] Created standalone group: {group_standalone.name} (open)")
        
        db.commit()
        
        print(f"\n[SUCCESS] Test clubs and groups created!")
        print(f"\nYou can now test:")
        print(f"  - GET  http://localhost:8000/api/clubs")
        print(f"  - GET  http://localhost:8000/api/clubs/1")
        print(f"  - GET  http://localhost:8000/api/groups")
        print(f"  - GET  http://localhost:8000/api/groups?club_id=1")
        print(f"  - GET  http://localhost:8000/api/clubs/1/members")
        
    except Exception as e:
        print(f"[ERROR] Error creating test data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("Creating test clubs and groups...\n")
    create_clubs_groups_test_data()
