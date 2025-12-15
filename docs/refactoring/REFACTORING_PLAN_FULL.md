# План рефакторинга Ayda Run v2

**Дата:** 15.12.2025
**Цель:** Подготовить кодовую базу к production и масштабированию
**Текущее состояние:** MVP 6/10, готовность к production 60%

---

## Общая стратегия

### Принципы рефакторинга

1. **Безопасность превыше всего** - каждый шаг должен быть обратимым
2. **Постепенность** - маленькие commits, частое тестирование
3. **Тесты сначала** - добавляем тесты перед рефакторингом
4. **Не ломаем API** - backward compatibility для frontend
5. **Документируем изменения** - обновляем docs после каждого этапа

### Последовательность выполнения

```
Phase 1: Подготовка и безопасность (2-3 дня)
   ↓
Phase 2: Структурный рефакторинг Backend (3-4 дня)
   ↓
Phase 3: Оптимизация Frontend (2-3 дня)
   ↓
Phase 4: Performance и Testing (3-4 дня)
   ↓
Phase 5: Финальная проверка (1-2 дня)
```

**Общее время:** 11-16 дней (с запасом)

---

## Phase 1: Подготовка и безопасность (2-3 дня)

### Цель
Создать безопасную базу для рефакторинга и устранить критические уязвимости.

### 1.1 Настройка окружения тестирования (0.5 дня)

**Задачи:**

- [ ] Создать тестовую ветку `refactor/phase-1-security`
- [ ] Настроить pre-commit hooks (black, flake8, pylint)
- [ ] Добавить `.editorconfig` для консистентности кода
- [ ] Создать `pytest.ini` и базовую структуру тестов

**Структура тестов:**
```
tests/
├── __init__.py
├── conftest.py              # Fixtures
├── test_api/
│   ├── __init__.py
│   ├── test_activities.py
│   ├── test_clubs.py
│   ├── test_groups.py
│   └── test_auth.py
├── test_services/
│   └── __init__.py
└── test_models/
    ├── __init__.py
    └── test_permissions.py
```

**Файлы:**
- `pytest.ini`
- `.editorconfig`
- `.pre-commit-config.yaml`
- `tests/conftest.py` - базовые fixtures (test DB, test client)

**Проверка:** `pytest tests/ -v` должен запуститься

---

### 1.2 Исправление критических security issues (1 день)

**Задачи:**

#### A. Исправить dev mode bypass в auth.py

**Проблема:**
```python
# auth.py:90-98
if not x_telegram_init_data:
    from storage.db import SessionLocal, User
    session = SessionLocal()
    # Создает mock user без проверки окружения
```

**Решение:**
```python
# auth.py
import logging
logger = logging.getLogger(__name__)

def get_current_user(
    x_telegram_init_data: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> User:
    """Get current user from Telegram WebApp initData"""

    if not x_telegram_init_data:
        # ONLY allow dev mode in development environment
        if not settings.debug:
            logger.error("Missing Telegram auth header in production")
            raise HTTPException(
                status_code=401,
                detail="Authentication required"
            )

        logger.warning("⚠️  Using DEV MODE authentication")
        return get_dev_user(db)

    # ... rest of validation
```

**Тесты:**
- [ ] `test_auth_dev_mode_only_in_debug()`
- [ ] `test_auth_rejects_missing_header_in_prod()`

**Файлы:** `auth.py`

---

#### B. Добавить rate limiting

**Установить:**
```bash
pip install slowapi
```

**Реализация:**
```python
# api_server.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Применить к критичным endpoints
@app.post("/api/activities")
@limiter.limit("10/minute")  # 10 создания активностей в минуту
async def create_activity(...):
    pass

@app.post("/api/clubs")
@limiter.limit("5/minute")
async def create_club(...):
    pass
```

**Файлы:** `api_server.py`, `requirements.txt`

---

#### C. Улучшить CORS настройки

**Проблема:**
```python
# api_server.py:29
allow_origins=["*"]  # Небезопасно!
```

**Решение:**
```python
# config.py
class Settings(BaseSettings):
    # ... existing fields
    cors_origins: list[str] = Field(
        default=["http://localhost:5173"],  # Vite dev server
        description="Allowed CORS origins"
    )

    @field_validator('cors_origins')
    @classmethod
    def validate_cors_origins(cls, v: list[str]) -> list[str]:
        if "*" in v and not cls.debug:
            raise ValueError("Wildcard CORS not allowed in production")
        return v

# api_server.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["*"],
)
```

**Env:**
```bash
# .env
CORS_ORIGINS=["https://your-domain.com","https://t.me"]
```

**Файлы:** `config.py`, `api_server.py`, `.env.example`

---

#### D. Добавить input validation

**Задачи:**

- [ ] Создать Pydantic schemas для всех request/response models
- [ ] Заменить Query параметры на validated schemas
- [ ] Добавить custom validators для специфичных полей

**Структура:**
```python
# schemas/
schemas/
├── __init__.py
├── activity.py
├── club.py
├── group.py
└── user.py
```

**Пример:**
```python
# schemas/activity.py
from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional

class ActivityCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    date: datetime
    location: str = Field(..., min_length=2, max_length=200)
    sport_type: str = Field(..., regex="^(running|trail|hiking|cycling|other)$")
    difficulty: str = Field(..., regex="^(easy|medium|hard)$")
    distance: Optional[float] = Field(None, ge=0, le=500)  # 0-500km
    duration: Optional[int] = Field(None, ge=1, le=1440)   # 1min-24h
    max_participants: Optional[int] = Field(None, ge=1, le=1000)
    club_id: Optional[int] = None
    group_id: Optional[int] = None

    @validator('date')
    def date_must_be_future(cls, v):
        if v < datetime.now():
            raise ValueError('Activity date must be in the future')
        return v

    @validator('club_id', 'group_id')
    def cannot_have_both_club_and_group(cls, v, values):
        if v and values.get('club_id') and values.get('group_id'):
            raise ValueError('Activity cannot belong to both club and group')
        return v

class ActivityResponse(BaseModel):
    id: int
    title: str
    date: datetime
    # ... all fields
    participants_count: int
    is_joined: bool

    class Config:
        from_attributes = True  # для ORM models
```

**Использование:**
```python
# api_server.py
from schemas.activity import ActivityCreate, ActivityResponse

@app.post("/api/activities", response_model=ActivityResponse)
async def create_activity(
    activity_data: ActivityCreate,  # Автоматическая валидация
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # activity_data уже провалидирован
    new_activity = Activity(**activity_data.dict(), creator_id=current_user.id)
    # ...
```

**Тесты:**
- [ ] `test_activity_validation_rejects_past_date()`
- [ ] `test_activity_validation_rejects_invalid_sport_type()`
- [ ] `test_activity_validation_max_length()`

**Файлы:** `schemas/*.py`, обновить все endpoints

---

#### E. Убрать debug prints и добавить logging

**Проблема:**
```python
# api_server.py:296, 315, 318
print(f"[DEBUG] ...")
```

**Решение:**
```python
# api_server.py (в начале файла)
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Заменить все print() на:
logger.info(f"Processing {len(activities)} activities")
logger.debug(f"Activity {activity_id}: club_name='{club_name}'")
```

**Также добавить logging middleware:**
```python
from starlette.middleware.base import BaseHTTPMiddleware
import time

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start_time = time.time()

        # Process request
        response = await call_next(request)

        # Log request
        process_time = time.time() - start_time
        logger.info(
            f"{request.method} {request.url.path} "
            f"- {response.status_code} "
            f"- {process_time:.2f}s"
        )

        return response

app.add_middleware(LoggingMiddleware)
```

**Файлы:** `api_server.py`, `groups_clubs_api.py`

---

### 1.3 Создать базовые тесты для критичного функционала (0.5-1 день)

**Задачи:**

- [ ] Тесты для authentication
- [ ] Тесты для permissions
- [ ] Тесты для основных CRUD operations

**Пример:**
```python
# tests/test_api/test_auth.py
import pytest
from fastapi.testclient import TestClient

def test_auth_requires_header_in_production(client, monkeypatch):
    """Test that missing auth header is rejected in production"""
    # Set production mode
    monkeypatch.setenv("DEBUG", "false")

    response = client.get("/api/users/me")
    assert response.status_code == 401
    assert "Authentication required" in response.json()["detail"]

def test_auth_allows_dev_mode_in_debug(client, monkeypatch):
    """Test that dev mode works when DEBUG=true"""
    monkeypatch.setenv("DEBUG", "true")

    response = client.get("/api/users/me")
    assert response.status_code == 200
    assert response.json()["username"] == "admin"

def test_telegram_auth_validation():
    """Test Telegram initData signature validation"""
    # TODO: implement with mock Telegram data
    pass
```

```python
# tests/test_models/test_permissions.py
from permissions import can_manage_club, UserRole

def test_admin_can_manage_any_club(db_session, test_user, test_club):
    """Test that ADMIN role can manage any club"""
    test_user.role = UserRole.ADMIN

    assert can_manage_club(test_user.id, test_club.id) == True

def test_member_cannot_manage_club(db_session, test_user, test_club):
    """Test that MEMBER role cannot manage club"""
    # Create membership with MEMBER role
    membership = Membership(
        user_id=test_user.id,
        club_id=test_club.id,
        role=UserRole.MEMBER
    )
    db_session.add(membership)

    assert can_manage_club(test_user.id, test_club.id) == False
```

**Минимальное покрытие:** 30% (фокус на критичных частях)

**Файлы:** `tests/test_api/*`, `tests/test_models/*`

---

### 1.4 Commit и review Phase 1

**Checklist:**

- [ ] Все тесты проходят (`pytest tests/ -v`)
- [ ] Security issues исправлены
- [ ] Logging настроен
- [ ] Rate limiting добавлен
- [ ] CORS правильно настроен
- [ ] Input validation работает
- [ ] Нет breaking changes для frontend

**Git:**
```bash
git add .
git commit -m "feat(security): phase 1 - security hardening and test infrastructure

- Add dev mode env check in auth
- Implement rate limiting (slowapi)
- Fix CORS configuration
- Add Pydantic request/response schemas
- Replace print() with logging
- Add logging middleware
- Create test infrastructure (pytest, fixtures)
- Add basic auth and permissions tests

🤖 Generated with Claude Code
Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

git push origin refactor/phase-1-security
```

**Review checkpoint:** Протестировать на локальном окружении 1-2 дня

---

## Phase 2: Структурный рефакторинг Backend (3-4 дня)

### Цель
Разделить монолитный `api_server.py` на модульную структуру с разделением ответственности.

### 2.1 Создать модульную структуру API (1 день)

**Новая структура:**
```
api/
├── __init__.py
├── dependencies.py      # Shared dependencies (get_db, get_current_user)
├── routers/
│   ├── __init__.py
│   ├── activities.py    # Activity endpoints
│   ├── clubs.py         # Club endpoints
│   ├── groups.py        # Group endpoints
│   └── users.py         # User endpoints
├── services/
│   ├── __init__.py
│   ├── activity_service.py
│   ├── club_service.py
│   ├── group_service.py
│   └── membership_service.py
└── utils/
    ├── __init__.py
    └── query_helpers.py
```

**Задачи:**

#### A. Создать dependencies.py

```python
# api/dependencies.py
from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from storage.db import SessionLocal, User
from auth import verify_telegram_webapp_data, get_dev_user
from config import settings
import logging

logger = logging.getLogger(__name__)

def get_db():
    """Database session dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(
    x_telegram_init_data: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user"""
    # Move from auth.py
    # ... (код из auth.py)

def get_current_user_optional(
    x_telegram_init_data: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get current user or None"""
    # ... (код из auth.py)
```

**Файлы:** `api/dependencies.py`

---

#### B. Создать services layer

**Идея:** Вынести бизнес-логику из handlers в service functions.

**Пример:**
```python
# api/services/activity_service.py
from sqlalchemy.orm import Session, joinedload, selectinload
from storage.db import Activity, Participation, User, Club, Group
from schemas.activity import ActivityCreate, ActivityUpdate
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

class ActivityService:
    """Business logic for activities"""

    @staticmethod
    def get_activities_with_filters(
        db: Session,
        user: Optional[User] = None,
        club_id: Optional[int] = None,
        group_id: Optional[int] = None,
        sport_type: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Activity]:
        """Get activities with filters and eager loading"""

        query = db.query(Activity).options(
            joinedload(Activity.club),
            joinedload(Activity.group),
            joinedload(Activity.creator),
            selectinload(Activity.participations)
        )

        # Apply filters
        if club_id:
            query = query.filter(Activity.club_id == club_id)
        if group_id:
            query = query.filter(Activity.group_id == group_id)
        if sport_type:
            query = query.filter(Activity.sport_type == sport_type)
        if date_from:
            query = query.filter(Activity.date >= date_from)
        if date_to:
            query = query.filter(Activity.date <= date_to)

        # Order and paginate
        query = query.order_by(Activity.date.asc())
        query = query.limit(limit).offset(offset)

        activities = query.all()

        # Enrich with computed fields
        for activity in activities:
            activity.participants_count = len(activity.participations)
            if user:
                activity.is_joined = any(
                    p.user_id == user.id for p in activity.participations
                )
            else:
                activity.is_joined = False

            # Set club/group names
            activity.club_name = activity.club.name if activity.club else None
            activity.group_name = activity.group.name if activity.group else None

        logger.info(f"Fetched {len(activities)} activities with filters")
        return activities

    @staticmethod
    def create_activity(
        db: Session,
        activity_data: ActivityCreate,
        creator: User
    ) -> Activity:
        """Create new activity with permissions check"""

        # Check permissions
        if activity_data.club_id:
            from permissions import can_create_activity_in_club
            if not can_create_activity_in_club(creator.id, activity_data.club_id):
                raise PermissionError("Cannot create activity in this club")

        if activity_data.group_id:
            from permissions import can_create_activity_in_group
            if not can_create_activity_in_group(creator.id, activity_data.group_id):
                raise PermissionError("Cannot create activity in this group")

        # Create activity
        new_activity = Activity(
            **activity_data.dict(),
            creator_id=creator.id
        )
        db.add(new_activity)
        db.commit()
        db.refresh(new_activity)

        logger.info(f"Created activity {new_activity.id} by user {creator.id}")
        return new_activity

    @staticmethod
    def join_activity(
        db: Session,
        activity_id: int,
        user: User
    ) -> dict:
        """Join user to activity"""

        activity = db.query(Activity).get(activity_id)
        if not activity:
            raise ValueError("Activity not found")

        # Check if already joined
        existing = db.query(Participation).filter(
            Participation.activity_id == activity_id,
            Participation.user_id == user.id
        ).first()

        if existing:
            # Leave
            db.delete(existing)
            db.commit()
            logger.info(f"User {user.id} left activity {activity_id}")
            return {"status": "left"}
        else:
            # Join
            # Check max participants
            if activity.max_participants:
                current_count = db.query(Participation).filter(
                    Participation.activity_id == activity_id
                ).count()
                if current_count >= activity.max_participants:
                    raise ValueError("Activity is full")

            participation = Participation(
                activity_id=activity_id,
                user_id=user.id
            )
            db.add(participation)
            db.commit()
            logger.info(f"User {user.id} joined activity {activity_id}")
            return {"status": "joined"}
```

**Аналогично создать:**
- `club_service.py` - логика для клубов
- `group_service.py` - логика для групп
- `membership_service.py` - логика для membership

**Файлы:** `api/services/*.py`

---

#### C. Создать routers

**Пример:**
```python
# api/routers/activities.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from api.dependencies import get_db, get_current_user, get_current_user_optional
from api.services.activity_service import ActivityService
from schemas.activity import ActivityCreate, ActivityUpdate, ActivityResponse
from storage.db import User

router = APIRouter(prefix="/api/activities", tags=["activities"])

@router.get("", response_model=list[ActivityResponse])
async def list_activities(
    club_id: Optional[int] = Query(None),
    group_id: Optional[int] = Query(None),
    sport_type: Optional[str] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    limit: int = Query(100, le=200),
    offset: int = Query(0, ge=0),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """List activities with filters"""

    activities = ActivityService.get_activities_with_filters(
        db=db,
        user=current_user,
        club_id=club_id,
        group_id=group_id,
        sport_type=sport_type,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        offset=offset
    )

    return activities

@router.post("", response_model=ActivityResponse, status_code=201)
async def create_activity(
    activity_data: ActivityCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new activity"""

    try:
        activity = ActivityService.create_activity(db, activity_data, current_user)
        return activity
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{activity_id}/join")
async def join_activity(
    activity_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Join or leave activity"""

    try:
        result = ActivityService.join_activity(db, activity_id, current_user)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# ... остальные endpoints
```

**Аналогично создать:**
- `clubs.py`
- `groups.py`
- `users.py`

**Файлы:** `api/routers/*.py`

---

#### D. Обновить api_server.py

```python
# api_server.py (сильно упрощенный)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter
from config import settings
from api.routers import activities, clubs, groups, users
import logging

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create app
app = FastAPI(
    title="Ayda Run API",
    version="2.0.0",
    docs_url="/api/docs" if settings.debug else None
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["*"],
)

# Rate limiting
limiter = Limiter(key_func=lambda: "global")  # TODO: use user-based key
app.state.limiter = limiter

# Include routers
app.include_router(activities.router)
app.include_router(clubs.router)
app.include_router(groups.router)
app.include_router(users.router)

# Static files (frontend)
app.mount("/", StaticFiles(directory="webapp/dist", html=True), name="webapp")

# Startup
@app.on_event("startup")
async def startup():
    logger.info("Starting Ayda Run API")
    # Initialize DB tables
    from storage.db import init_db
    init_db()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**Файлы:** `api_server.py` (переписать)

---

### 2.2 Рефакторинг permissions.py (0.5 дня)

**Проблемы:**
- Дублирование `role_hierarchy`
- Создание сессий внутри функций

**Решение:**

```python
# permissions.py (refactored)
from enum import Enum
from typing import Optional
from sqlalchemy.orm import Session
from storage.db import User, Club, Group, Membership, UserRole
import logging

logger = logging.getLogger(__name__)

# Constants
ROLE_HIERARCHY = {
    UserRole.MEMBER: 0,
    UserRole.TRAINER: 1,
    UserRole.ORGANIZER: 2,
    UserRole.ADMIN: 3
}

def has_higher_or_equal_role(role1: UserRole, role2: UserRole) -> bool:
    """Check if role1 >= role2 in hierarchy"""
    return ROLE_HIERARCHY[role1] >= ROLE_HIERARCHY[role2]

def get_user_role_in_club(db: Session, user_id: int, club_id: int) -> Optional[UserRole]:
    """Get user's role in club"""
    membership = db.query(Membership).filter(
        Membership.user_id == user_id,
        Membership.club_id == club_id
    ).first()

    return membership.role if membership else None

def get_user_role_in_group(db: Session, user_id: int, group_id: int) -> Optional[UserRole]:
    """Get user's role in group"""
    membership = db.query(Membership).filter(
        Membership.user_id == user_id,
        Membership.group_id == group_id
    ).first()

    return membership.role if membership else None

def can_manage_club(db: Session, user_id: int, club_id: int) -> bool:
    """Check if user can manage club (ORGANIZER+)"""
    role = get_user_role_in_club(db, user_id, club_id)
    if not role:
        return False

    return has_higher_or_equal_role(role, UserRole.ORGANIZER)

def can_create_activity_in_club(db: Session, user_id: int, club_id: int) -> bool:
    """Check if user can create activity in club (ORGANIZER+)"""
    return can_manage_club(db, user_id, club_id)

def can_create_activity_in_group(
    db: Session,
    user_id: int,
    group_id: int
) -> bool:
    """Check if user can create activity in group"""

    group = db.query(Group).get(group_id)
    if not group:
        return False

    # If group belongs to club, need ORGANIZER role in club
    if group.club_id:
        return can_manage_club(db, user_id, group.club_id)

    # Standalone group - need TRAINER role in group
    role = get_user_role_in_group(db, user_id, group_id)
    if not role:
        return False

    return has_higher_or_equal_role(role, UserRole.TRAINER)

# ... остальные функции аналогично
```

**Изменения:**
- Убрать создание `SessionLocal()` внутри функций
- Принимать `db: Session` как параметр
- Вынести `role_hierarchy` в константу `ROLE_HIERARCHY`
- Добавить helper функции
- Добавить logging

**Файлы:** `permissions.py`

---

### 2.3 Оптимизировать database queries (1 день)

**Задачи:**

#### A. Добавить eager loading

**Проблема:** N+1 queries при получении списка активностей

**Решение:**
```python
# В activity_service.py уже реализовано
query = query.options(
    joinedload(Activity.club),
    joinedload(Activity.group),
    selectinload(Activity.participations)
)
```

#### B. Добавить database indexes

```python
# storage/db.py
class Activity(Base):
    __tablename__ = "activities"

    # ... existing fields

    # Add indexes
    __table_args__ = (
        Index('ix_activity_date', 'date'),
        Index('ix_activity_club_id', 'club_id'),
        Index('ix_activity_group_id', 'group_id'),
        Index('ix_activity_sport_type', 'sport_type'),
        Index('ix_activity_creator_id', 'creator_id'),
    )

class Participation(Base):
    __tablename__ = "participations"

    # ... existing fields

    __table_args__ = (
        Index('ix_participation_activity_user', 'activity_id', 'user_id'),
        Index('ix_participation_user_id', 'user_id'),
    )

class Membership(Base):
    __tablename__ = "memberships"

    # ... existing fields

    __table_args__ = (
        Index('ix_membership_user_club', 'user_id', 'club_id'),
        Index('ix_membership_user_group', 'user_id', 'group_id'),
    )
```

**Migration:**
```bash
alembic revision --autogenerate -m "add_database_indexes"
alembic upgrade head
```

**Файлы:** `storage/db.py`, новая миграция

#### C. Добавить pagination helpers

```python
# api/utils/query_helpers.py
from sqlalchemy.orm import Query
from typing import TypeVar, Generic, List
from pydantic import BaseModel

T = TypeVar('T')

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    limit: int
    offset: int
    has_more: bool

def paginate_query(
    query: Query,
    limit: int = 50,
    offset: int = 0
) -> PaginatedResponse:
    """Paginate SQLAlchemy query"""

    total = query.count()
    items = query.limit(limit).offset(offset).all()
    has_more = (offset + limit) < total

    return PaginatedResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
        has_more=has_more
    )
```

**Использование:**
```python
# В routers
@router.get("", response_model=PaginatedResponse[ActivityResponse])
async def list_activities(...):
    query = ActivityService.build_query(db, filters)
    return paginate_query(query, limit, offset)
```

**Файлы:** `api/utils/query_helpers.py`

---

### 2.4 Удалить дублирующийся код в groups_clubs_api.py (0.5 дня)

**Стратегия:** Создать generic CRUD service

```python
# api/services/base_service.py
from typing import TypeVar, Generic, Type, List, Optional
from sqlalchemy.orm import Session
from pydantic import BaseModel

ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

class CRUDService(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Generic CRUD operations"""

    def __init__(self, model: Type[ModelType]):
        self.model = model

    def get(self, db: Session, id: int) -> Optional[ModelType]:
        return db.query(self.model).get(id)

    def get_multi(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100
    ) -> List[ModelType]:
        return db.query(self.model).offset(skip).limit(limit).all()

    def create(
        self,
        db: Session,
        obj_in: CreateSchemaType,
        **kwargs
    ) -> ModelType:
        obj_data = obj_in.dict()
        obj_data.update(kwargs)
        db_obj = self.model(**obj_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self,
        db: Session,
        db_obj: ModelType,
        obj_in: UpdateSchemaType
    ) -> ModelType:
        obj_data = obj_in.dict(exclude_unset=True)
        for field, value in obj_data.items():
            setattr(db_obj, field, value)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, id: int) -> None:
        obj = db.query(self.model).get(id)
        db.delete(obj)
        db.commit()
```

**Использование:**
```python
# api/services/club_service.py
from api.services.base_service import CRUDService
from storage.db import Club
from schemas.club import ClubCreate, ClubUpdate

class ClubService(CRUDService[Club, ClubCreate, ClubUpdate]):
    def __init__(self):
        super().__init__(Club)

    # Add club-specific methods
    def get_club_members(self, db: Session, club_id: int):
        # ...
        pass
```

**Файлы:** `api/services/base_service.py`, рефакторить `club_service.py`, `group_service.py`

---

### 2.5 Тесты для Phase 2 (0.5-1 день)

**Задачи:**

- [ ] Тесты для каждого service
- [ ] Тесты для каждого router
- [ ] Integration tests для полных flows

**Пример:**
```python
# tests/test_services/test_activity_service.py
import pytest
from datetime import datetime, timedelta
from api.services.activity_service import ActivityService
from schemas.activity import ActivityCreate

def test_create_activity(db_session, test_user):
    """Test activity creation"""

    activity_data = ActivityCreate(
        title="Morning Run",
        description="Easy 5k",
        date=datetime.now() + timedelta(days=1),
        location="Central Park",
        sport_type="running",
        difficulty="easy",
        distance=5.0
    )

    activity = ActivityService.create_activity(
        db=db_session,
        activity_data=activity_data,
        creator=test_user
    )

    assert activity.id is not None
    assert activity.title == "Morning Run"
    assert activity.creator_id == test_user.id

def test_join_activity_success(db_session, test_activity, test_user):
    """Test joining activity"""

    result = ActivityService.join_activity(
        db=db_session,
        activity_id=test_activity.id,
        user=test_user
    )

    assert result["status"] == "joined"

    # Verify in DB
    from storage.db import Participation
    participation = db_session.query(Participation).filter(
        Participation.activity_id == test_activity.id,
        Participation.user_id == test_user.id
    ).first()

    assert participation is not None

def test_join_full_activity_fails(db_session, test_activity, test_user):
    """Test joining full activity fails"""

    test_activity.max_participants = 1
    # Join first user
    ActivityService.join_activity(db_session, test_activity.id, test_user)

    # Try to join second user
    from storage.db import User
    user2 = User(telegram_id=999, username="user2")
    db_session.add(user2)
    db_session.commit()

    with pytest.raises(ValueError, match="Activity is full"):
        ActivityService.join_activity(db_session, test_activity.id, user2)
```

**Файлы:** `tests/test_services/*`, `tests/test_api/*`

---

### 2.6 Commit и review Phase 2

**Checklist:**

- [ ] Модульная структура API создана
- [ ] Services layer работает
- [ ] Routers разделены по ресурсам
- [ ] Нет дублирующегося кода
- [ ] Database queries оптимизированы
- [ ] Indexes добавлены
- [ ] Тесты проходят (coverage 40%+)
- [ ] API обратно совместим с frontend

**Git:**
```bash
git add .
git commit -m "refactor(backend): phase 2 - modular architecture

- Split api_server.py into routers and services
- Create service layer for business logic
- Refactor permissions.py (remove session creation)
- Add database indexes for performance
- Implement generic CRUD service
- Add pagination helpers
- Remove duplicate code in groups_clubs_api
- Add service and router tests

🤖 Generated with Claude Code
Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

git push origin refactor/phase-2-backend
```

---

## Phase 3: Оптимизация Frontend (2-3 дня)

### Цель
Упростить сложные компоненты, улучшить переиспользование кода, добавить React Query.

### 3.1 Интеграция TanStack Query (React Query) (1 день)

**Установка:**
```bash
cd webapp
npm install @tanstack/react-query
npm install @tanstack/react-query-devtools
```

**Настройка:**
```jsx
// webapp/src/main.jsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'

const queryClient = new QueryClient({
    defaultOptions: {
        queries: {
            staleTime: 1000 * 60 * 5,  // 5 minutes
            cacheTime: 1000 * 60 * 30, // 30 minutes
            retry: 1,
            refetchOnWindowFocus: false,
        },
    },
})

ReactDOM.createRoot(document.getElementById('root')).render(
    <React.StrictMode>
        <QueryClientProvider client={queryClient}>
            <App />
            <ReactQueryDevtools initialIsOpen={false} />
        </QueryClientProvider>
    </React.StrictMode>
)
```

**Рефакторинг hooks:**
```javascript
// webapp/src/hooks/useActivities.js (новая версия с React Query)
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { activitiesApi } from '../api'

export function useActivities(filters = {}) {
    return useQuery({
        queryKey: ['activities', filters],
        queryFn: () => activitiesApi.list(filters),
    })
}

export function useActivity(id) {
    return useQuery({
        queryKey: ['activity', id],
        queryFn: () => activitiesApi.get(id),
        enabled: !!id,
    })
}

export function useJoinActivity() {
    const queryClient = useQueryClient()

    return useMutation({
        mutationFn: (activityId) => activitiesApi.join(activityId),
        onSuccess: (data, activityId) => {
            // Invalidate activities list
            queryClient.invalidateQueries({ queryKey: ['activities'] })
            // Update specific activity
            queryClient.invalidateQueries({ queryKey: ['activity', activityId] })
        },
    })
}

export function useCreateActivity() {
    const queryClient = useQueryClient()

    return useMutation({
        mutationFn: (data) => activitiesApi.create(data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['activities'] })
        },
    })
}

// ... аналогично для остальных
```

**Обновить компоненты:**
```jsx
// webapp/src/screens/Home.jsx (упрощенная версия)
import { useActivities } from '../hooks/useActivities'
import { useJoinActivity } from '../hooks/useActivities'

export default function Home() {
    const [mode, setMode] = useState('all')
    const [currentWeekIndex, setCurrentWeekIndex] = useState(null)

    // React Query вместо useApi
    const { data: activities = [], isLoading, error } = useActivities()
    const joinActivity = useJoinActivity()

    const handleJoinToggle = (activityId) => {
        joinActivity.mutate(activityId)
    }

    // ... rest of component

    if (isLoading) return <Loading />
    if (error) return <ErrorMessage error={error} />

    // ... render
}
```

**Преимущества:**
- ✅ Автоматический cache
- ✅ Автоматический refetch
- ✅ Optimistic updates
- ✅ DevTools для debugging
- ✅ Меньше boilerplate кода

**Файлы:** обновить `hooks/*`, все screens

---

### 3.2 Рефакторинг Home.jsx (1 день)

**Текущие проблемы:**
- 342 строки
- 5+ useState
- Большие inline компоненты

**Решение:**

#### A. Вынести DaySection в отдельный компонент

```jsx
// webapp/src/components/DaySection.jsx
import React from 'react'
import { ActivityCard } from './ActivityCard'
import { dayNames } from '../data/sample_data'

export function DaySection({
    weekNumber,
    dayOfWeek,
    activities,
    expandedDays,
    onToggleExpand,
    onJoinToggle
}) {
    const hasActivities = activities && activities.length > 0
    const now = new Date()
    const isTodayDay = new Date().getDay() === dayOfWeek

    // Логика сворачивания
    const isCurrentWeek = weekNumber === 0
    const isPastWeek = weekNumber < 0
    const currentDayOfWeek = now.getDay()

    const dayOrder = dayOfWeek === 0 ? 7 : dayOfWeek
    const currentDayOrder = currentDayOfWeek === 0 ? 7 : currentDayOfWeek

    const isPastDay = isPastWeek || (isCurrentWeek && dayOrder < currentDayOrder)
    const expandKey = `${weekNumber}-${dayOfWeek}`
    const isExpanded = expandedDays[expandKey] || false

    const activityCount = hasActivities ? activities.length : 0

    return (
        <div className="mb-4">
            {/* Day Header */}
            <div className="flex items-center gap-2 mb-3">
                {isPastDay ? (
                    <button
                        onClick={() => onToggleExpand(weekNumber, dayOfWeek)}
                        className="flex items-center gap-2 text-sm text-gray-400 hover:text-gray-600"
                    >
                        <span>{dayNames[dayOfWeek]}</span>
                        <span className={`text-xs transition-transform ${isExpanded ? 'rotate-180' : ''}`}>
                            ▾
                        </span>
                    </button>
                ) : (
                    <span className={`text-sm font-medium ${isTodayDay ? 'text-gray-800' : 'text-gray-500'}`}>
                        {isTodayDay ? `Сегодня, ${dayNames[dayOfWeek].toLowerCase()}` : dayNames[dayOfWeek]}
                    </span>
                )}
                <div className="flex-1 border-b border-gray-200" />
                <span className="text-xs text-gray-400">{activityCount}</span>
            </div>

            {/* Activities */}
            {isPastDay ? (
                isExpanded && <ActivityList activities={activities} onJoinToggle={onJoinToggle} />
            ) : (
                <ActivityList activities={activities} onJoinToggle={onJoinToggle} />
            )}
        </div>
    )
}

function ActivityList({ activities, onJoinToggle }) {
    const now = new Date()

    if (!activities || activities.length === 0) {
        return <p className="text-sm text-gray-300 mb-3 pl-1">В этот день нет активностей</p>
    }

    return (
        <div className="space-y-3">
            {activities.map(activity => {
                const isPast = new Date(activity.date) < now
                return (
                    <div key={activity.id} className={isPast ? 'opacity-50' : ''}>
                        <ActivityCard
                            activity={activity}
                            onJoinToggle={onJoinToggle}
                        />
                    </div>
                )
            })}
        </div>
    )
}
```

**Файлы:** `webapp/src/components/DaySection.jsx`

#### B. Создать custom hook для week navigation

```javascript
// webapp/src/hooks/useWeekNavigation.js
import { useState, useEffect, useCallback } from 'react'
import { getWeekNumber, getWeekStart, getWeekEnd } from '../data/sample_data'

export function useWeekNavigation(activities, mode) {
    const [currentWeekIndex, setCurrentWeekIndex] = useState(null)

    // Group activities by week and day
    const allWeeks = useCallback(() => {
        if (!activities) return []

        // Filter based on mode
        let filtered = activities
        if (mode === 'my') {
            filtered = activities.filter(a => a.isJoined)
        }

        // Group by week
        const weekMap = {}
        const today = new Date()

        filtered.forEach(activity => {
            const activityDate = new Date(activity.date)
            const weekNum = getWeekNumber(activityDate, today)

            if (!weekMap[weekNum]) {
                weekMap[weekNum] = {
                    weekNumber: weekNum,
                    weekStart: getWeekStart(activityDate),
                    weekEnd: getWeekEnd(activityDate),
                    days: {}
                }
            }

            const dayOfWeek = activityDate.getDay()
            if (!weekMap[weekNum].days[dayOfWeek]) {
                weekMap[weekNum].days[dayOfWeek] = []
            }

            weekMap[weekNum].days[dayOfWeek].push(activity)
        })

        // Sort activities within each day
        Object.values(weekMap).forEach(week => {
            Object.values(week.days).forEach(dayActivities => {
                dayActivities.sort((a, b) => new Date(a.date) - new Date(b.date))
            })
        })

        // Convert to array and sort
        return Object.values(weekMap).sort((a, b) => a.weekNumber - b.weekNumber)
    }, [activities, mode])()

    // Set initial week to current week
    useEffect(() => {
        if (currentWeekIndex === null && allWeeks.length > 0) {
            const currentWeekIdx = allWeeks.findIndex(w => w.weekNumber === 0)
            setCurrentWeekIndex(currentWeekIdx >= 0 ? currentWeekIdx : 0)
        }
    }, [allWeeks, currentWeekIndex])

    const displayedWeek = currentWeekIndex !== null && allWeeks[currentWeekIndex]
        ? allWeeks[currentWeekIndex]
        : null

    const goToPreviousWeek = () => {
        if (currentWeekIndex > 0) {
            setCurrentWeekIndex(currentWeekIndex - 1)
        }
    }

    const goToNextWeek = () => {
        if (currentWeekIndex < allWeeks.length - 1) {
            setCurrentWeekIndex(currentWeekIndex + 1)
        }
    }

    const canGoPrevious = currentWeekIndex > 0
    const canGoNext = currentWeekIndex < allWeeks.length - 1

    return {
        displayedWeek,
        goToPreviousWeek,
        goToNextWeek,
        canGoPrevious,
        canGoNext
    }
}
```

**Файлы:** `webapp/src/hooks/useWeekNavigation.js`

#### C. Упростить Home.jsx

```jsx
// webapp/src/screens/Home.jsx (упрощенная версия - ~150 строк)
import React, { useState } from 'react'
import { useActivities, useJoinActivity } from '../hooks/useActivities'
import { useWeekNavigation } from '../hooks/useWeekNavigation'
import { DaySection } from '../components/DaySection'
import { BottomNav, CreateMenu, Loading, ErrorMessage, EmptyState } from '../components'

export default function Home() {
    const [mode, setMode] = useState('all') // 'my' | 'all'
    const [showCreateMenu, setShowCreateMenu] = useState(false)
    const [expandedDays, setExpandedDays] = useState({})

    // Fetch data with React Query
    const { data: activities = [], isLoading, error } = useActivities()
    const joinActivity = useJoinActivity()

    // Week navigation logic
    const {
        displayedWeek,
        goToPreviousWeek,
        goToNextWeek,
        canGoPrevious,
        canGoNext
    } = useWeekNavigation(activities, mode)

    // Handlers
    const handleJoinToggle = (activityId) => {
        joinActivity.mutate(activityId)
    }

    const toggleDayExpansion = (weekNum, dayOfWeek) => {
        const key = `${weekNum}-${dayOfWeek}`
        setExpandedDays(prev => ({
            ...prev,
            [key]: !prev[key]
        }))
    }

    // Calculate totals
    const totalCount = displayedWeek
        ? Object.values(displayedWeek.days).reduce((sum, dayActivities) =>
            sum + dayActivities.length, 0)
        : 0

    const hasActivities = totalCount > 0

    // Format week range
    const getWeekRangeText = (week) => {
        if (!week) return ''
        const start = week.weekStart
        const end = week.weekEnd
        const formatDay = (date) => date.toLocaleDateString('ru-RU', {
            day: 'numeric', month: 'short'
        })
        return `${formatDay(start)} - ${formatDay(end)}`
    }

    if (isLoading) return <Loading text="Загружаем тренировки..." />
    if (error) return <ErrorMessage message={error.message} />

    return (
        <div className="min-h-screen bg-gray-50 flex flex-col pb-20">
            {/* Header */}
            <div className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between sticky top-0 z-10">
                <Toggle mode={mode} setMode={setMode} />
                <span className="text-sm text-gray-400">{totalCount}</span>
            </div>

            {/* Week Navigation */}
            {displayedWeek && (
                <WeekNavigationBar
                    week={displayedWeek}
                    onPrevious={goToPreviousWeek}
                    onNext={goToNextWeek}
                    canGoPrevious={canGoPrevious}
                    canGoNext={canGoNext}
                    getWeekRangeText={getWeekRangeText}
                />
            )}

            {/* Content */}
            <div className="flex-1 overflow-auto px-4 py-4">
                {hasActivities && displayedWeek ? (
                    <div className="mb-6">
                        {[1, 2, 3, 4, 5, 6, 0].map(dayOfWeek => (
                            <DaySection
                                key={`${displayedWeek.weekNumber}-${dayOfWeek}`}
                                weekNumber={displayedWeek.weekNumber}
                                dayOfWeek={dayOfWeek}
                                activities={displayedWeek.days[dayOfWeek]}
                                expandedDays={expandedDays}
                                onToggleExpand={toggleDayExpansion}
                                onJoinToggle={handleJoinToggle}
                            />
                        ))}
                    </div>
                ) : (
                    <EmptyState
                        icon="📅"
                        title="Пока пусто"
                        description="Нет предстоящих тренировок"
                        actionText={mode === 'my' ? "Смотреть все" : null}
                        onAction={() => setMode('all')}
                    />
                )}
            </div>

            {/* Bottom Navigation */}
            <div className="fixed bottom-0 left-0 right-0 max-w-md mx-auto">
                <BottomNav onCreateClick={() => setShowCreateMenu(true)} />
            </div>

            {/* Create Menu */}
            <CreateMenu
                isOpen={showCreateMenu}
                onClose={() => setShowCreateMenu(false)}
            />
        </div>
    )
}

// Helper components
function Toggle({ mode, setMode }) {
    return (
        <div className="flex items-center gap-1 text-sm">
            <button
                onClick={() => setMode('my')}
                className={`transition-colors ${mode === 'my'
                    ? 'text-gray-900 font-medium'
                    : 'text-gray-400 hover:text-gray-600'
                }`}
            >
                Мои
            </button>
            <span className="text-gray-300">/</span>
            <button
                onClick={() => setMode('all')}
                className={`transition-colors ${mode === 'all'
                    ? 'text-gray-900 font-medium'
                    : 'text-gray-400 hover:text-gray-600'
                }`}
            >
                Все
            </button>
        </div>
    )
}

function WeekNavigationBar({ week, onPrevious, onNext, canGoPrevious, canGoNext, getWeekRangeText }) {
    return (
        <div className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between sticky top-[52px] z-10">
            <button
                onClick={onPrevious}
                disabled={!canGoPrevious}
                className={`text-2xl ${canGoPrevious ? 'text-gray-700 hover:text-gray-900' : 'text-gray-300'}`}
            >
                ‹
            </button>
            <div className="text-center">
                <div className="text-sm font-medium text-gray-900">
                    {week.weekNumber === 0 ? 'Текущая неделя' :
                        week.weekNumber > 0 ? `+${week.weekNumber} неделя` :
                            `${week.weekNumber} неделя`}
                </div>
                <div className="text-xs text-gray-500">
                    {getWeekRangeText(week)}
                </div>
            </div>
            <button
                onClick={onNext}
                disabled={!canGoNext}
                className={`text-2xl ${canGoNext ? 'text-gray-700 hover:text-gray-900' : 'text-gray-300'}`}
            >
                ›
            </button>
        </div>
    )
}
```

**Результат:**
- ✅ Сокращено с 342 до ~150 строк
- ✅ Вынесены 3 компонента (DaySection, Toggle, WeekNavigationBar)
- ✅ Создан custom hook useWeekNavigation
- ✅ Улучшена читаемость

**Файлы:** `webapp/src/screens/Home.jsx` (refactored)

---

### 3.3 Создать переиспользуемые компоненты (0.5-1 день)

**Задачи:**

#### A. Shared DetailPage component

```jsx
// webapp/src/components/DetailPage.jsx
import React from 'react'
import { useNavigate } from 'react-router-dom'
import { Loading, ErrorMessage, Button } from './ui'

export function DetailPage({
    title,
    subtitle,
    loading,
    error,
    headerActions,
    children,
    backButton = true
}) {
    const navigate = useNavigate()

    if (loading) return <Loading />
    if (error) return <ErrorMessage message={error.message} />

    return (
        <div className="min-h-screen bg-gray-50">
            {/* Header */}
            <div className="bg-white border-b border-gray-200 px-4 py-3 sticky top-0 z-10">
                <div className="flex items-center justify-between">
                    {backButton && (
                        <button
                            onClick={() => navigate(-1)}
                            className="text-gray-700 hover:text-gray-900"
                        >
                            ← Назад
                        </button>
                    )}
                    <div className="flex gap-2">
                        {headerActions}
                    </div>
                </div>
                {title && (
                    <div className="mt-3">
                        <h1 className="text-lg font-semibold text-gray-900">{title}</h1>
                        {subtitle && <p className="text-sm text-gray-500">{subtitle}</p>}
                    </div>
                )}
            </div>

            {/* Content */}
            <div className="px-4 py-4">
                {children}
            </div>
        </div>
    )
}
```

**Использование:**
```jsx
// ActivityDetail.jsx (упрощенная версия)
export default function ActivityDetail() {
    const { id } = useParams()
    const { data: activity, isLoading, error } = useActivity(id)

    return (
        <DetailPage
            title={activity?.title}
            subtitle={formatDate(activity?.date)}
            loading={isLoading}
            error={error}
            headerActions={
                <>
                    <Button onClick={handleEdit}>Изменить</Button>
                    <Button onClick={handleDelete} variant="danger">Удалить</Button>
                </>
            }
        >
            {/* Activity content */}
            <ActivityInfo activity={activity} />
            <ParticipantsList activityId={id} />
        </DetailPage>
    )
}
```

**Файлы:** `webapp/src/components/DetailPage.jsx`

#### B. Shared ParticipantsList component

```jsx
// webapp/src/components/ParticipantsList.jsx
import React, { useState } from 'react'
import { useActivityParticipants } from '../hooks/useActivities'

export function ParticipantsList({ activityId, limit = 5 }) {
    const [showAll, setShowAll] = useState(false)
    const { data: participants = [], isLoading } = useActivityParticipants(activityId)

    if (isLoading) return <div>Загрузка участников...</div>
    if (participants.length === 0) return <div>Нет участников</div>

    const displayedParticipants = showAll ? participants : participants.slice(0, limit)

    return (
        <div className="bg-white rounded-xl border border-gray-200 p-4">
            <div className="flex items-center justify-between mb-3">
                <h3 className="font-medium text-gray-900">
                    Участники ({participants.length})
                </h3>
            </div>

            <div className="space-y-2">
                {displayedParticipants.map(participant => (
                    <div key={participant.id} className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center">
                            {participant.first_name?.[0] || '?'}
                        </div>
                        <div>
                            <div className="text-sm font-medium text-gray-900">
                                {participant.first_name || participant.username}
                            </div>
                            <div className="text-xs text-gray-500">
                                @{participant.username}
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            {participants.length > limit && !showAll && (
                <button
                    onClick={() => setShowAll(true)}
                    className="mt-3 text-sm text-gray-600 hover:text-gray-900"
                >
                    Показать всех ({participants.length})
                </button>
            )}
        </div>
    )
}
```

**Файлы:** `webapp/src/components/ParticipantsList.jsx`

---

### 3.4 Добавить form validation (0.5 дня)

**Установка:**
```bash
npm install react-hook-form zod @hookform/resolvers
```

**Создать validation schemas:**
```javascript
// webapp/src/validation/activitySchema.js
import { z } from 'zod'

export const activitySchema = z.object({
    title: z.string()
        .min(3, 'Название должно быть не менее 3 символов')
        .max(200, 'Название слишком длинное'),
    description: z.string()
        .max(2000, 'Описание слишком длинное')
        .optional(),
    date: z.date({
        required_error: 'Укажите дату',
    }),
    location: z.string()
        .min(2, 'Укажите место проведения'),
    sportType: z.enum(['running', 'trail', 'hiking', 'cycling', 'other'], {
        required_error: 'Выберите вид спорта',
    }),
    difficulty: z.enum(['easy', 'medium', 'hard'], {
        required_error: 'Выберите сложность',
    }),
    distance: z.number()
        .min(0, 'Дистанция не может быть отрицательной')
        .max(500, 'Слишком большая дистанция')
        .optional(),
    duration: z.number()
        .min(1, 'Минимум 1 минута')
        .max(1440, 'Максимум 24 часа')
        .optional(),
    maxParticipants: z.number()
        .min(1, 'Минимум 1 участник')
        .max(1000, 'Слишком много участников')
        .optional(),
})
```

**Использование:**
```jsx
// webapp/src/screens/ActivityCreate.jsx
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { activitySchema } from '../validation/activitySchema'

export default function ActivityCreate() {
    const {
        register,
        handleSubmit,
        formState: { errors },
    } = useForm({
        resolver: zodResolver(activitySchema),
    })

    const createActivity = useCreateActivity()

    const onSubmit = (data) => {
        createActivity.mutate(data, {
            onSuccess: () => {
                // Navigate to activity detail
            },
        })
    }

    return (
        <form onSubmit={handleSubmit(onSubmit)}>
            <div>
                <label>Название</label>
                <input {...register('title')} />
                {errors.title && <span className="error">{errors.title.message}</span>}
            </div>

            <div>
                <label>Дата</label>
                <input type="datetime-local" {...register('date', { valueAsDate: true })} />
                {errors.date && <span className="error">{errors.date.message}</span>}
            </div>

            {/* ... остальные поля */}

            <button type="submit" disabled={createActivity.isLoading}>
                {createActivity.isLoading ? 'Создание...' : 'Создать'}
            </button>
        </form>
    )
}
```

**Файлы:** `webapp/src/validation/*`, обновить формы

---

### 3.5 Тесты для Frontend (опционально, 0.5 дня)

**Установка:**
```bash
npm install -D vitest @testing-library/react @testing-library/jest-dom @testing-library/user-event
```

**Конфигурация:**
```javascript
// vite.config.js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
    plugins: [react()],
    test: {
        globals: true,
        environment: 'jsdom',
        setupFiles: './src/test/setup.js',
    },
})
```

**Примеры тестов:**
```javascript
// webapp/src/components/__tests__/ActivityCard.test.jsx
import { render, screen } from '@testing-library/react'
import { ActivityCard } from '../ActivityCard'

describe('ActivityCard', () => {
    const mockActivity = {
        id: 1,
        title: 'Morning Run',
        date: '2025-12-16T06:00:00',
        location: 'Central Park',
        distance: 5,
        participants: 10,
        isJoined: false,
    }

    it('renders activity title', () => {
        render(<ActivityCard activity={mockActivity} />)
        expect(screen.getByText('Morning Run')).toBeInTheDocument()
    })

    it('shows join button when not joined', () => {
        render(<ActivityCard activity={mockActivity} />)
        expect(screen.getByText('Записаться')).toBeInTheDocument()
    })

    it('calls onJoinToggle when button clicked', () => {
        const handleJoin = vi.fn()
        render(<ActivityCard activity={mockActivity} onJoinToggle={handleJoin} />)

        screen.getByText('Записаться').click()
        expect(handleJoin).toHaveBeenCalledWith(1)
    })
})
```

**Файлы:** `webapp/src/**/__tests__/*.test.jsx`

---

### 3.6 Commit и review Phase 3

**Checklist:**

- [ ] React Query интегрирован
- [ ] Home.jsx упрощен (<200 строк)
- [ ] Создан useWeekNavigation hook
- [ ] DaySection вынесен в компонент
- [ ] Созданы shared компоненты (DetailPage, ParticipantsList)
- [ ] Form validation добавлен
- [ ] Тесты написаны (опционально)
- [ ] Приложение работает без регрессий

**Git:**
```bash
git add .
git commit -m "refactor(frontend): phase 3 - component optimization

- Integrate TanStack Query (React Query)
- Refactor Home.jsx (342 → 150 lines)
- Extract DaySection component
- Create useWeekNavigation custom hook
- Add shared DetailPage component
- Add shared ParticipantsList component
- Implement form validation (react-hook-form + zod)
- Add frontend tests (Vitest)

🤖 Generated with Claude Code
Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

git push origin refactor/phase-3-frontend
```

---

## Phase 4: Performance и Testing (3-4 дня)

### Цель
Оптимизировать производительность, добавить полное тестовое покрытие, настроить мониторинг.

### 4.1 Backend performance optimization (1 день)

#### A. Database connection pooling

```python
# storage/db.py
from sqlalchemy.pool import QueuePool

engine = create_engine(
    settings.database_url,
    poolclass=QueuePool,
    pool_size=5,          # Количество постоянных соединений
    max_overflow=10,      # Дополнительные соединения при нагрузке
    pool_timeout=30,      # Timeout для получения соединения
    pool_recycle=3600,    # Recycled каждый час
    echo=settings.debug   # SQL logging только в debug
)
```

#### B. Add caching

**Установка:**
```bash
pip install aiocache
```

**Реализация:**
```python
# api/utils/cache.py
from aiocache import Cache
from aiocache.serializers import JsonSerializer

cache = Cache(
    Cache.MEMORY,
    serializer=JsonSerializer(),
    namespace="ayda_run"
)

# Декоратор для кэширования
from functools import wraps

def cached(ttl=300):
    """Cache decorator with TTL in seconds"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"

            # Check cache
            result = await cache.get(cache_key)
            if result is not None:
                return result

            # Call function
            result = await func(*args, **kwargs)

            # Store in cache
            await cache.set(cache_key, result, ttl=ttl)
            return result
        return wrapper
    return decorator
```

**Использование:**
```python
# api/routers/activities.py
from api.utils.cache import cached

@router.get("")
@cached(ttl=60)  # Cache for 1 minute
async def list_activities(...):
    # ...
```

#### C. Add request compression

```python
# api_server.py
from fastapi.middleware.gzip import GZIPMiddleware

app.add_middleware(GZIPMiddleware, minimum_size=1000)
```

#### D. Optimize serialization

```python
# schemas/activity.py
from pydantic import BaseModel, ConfigDict

class ActivityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    # Use Pydantic v2 computed fields
    @computed_field
    @property
    def participants_count(self) -> int:
        return len(self.participations) if self.participations else 0
```

**Файлы:** `storage/db.py`, `api/utils/cache.py`, обновить schemas

---

### 4.2 Frontend performance optimization (0.5 дня)

#### A. Code splitting

```jsx
// webapp/src/App.jsx
import { lazy, Suspense } from 'react'

// Lazy load screens
const Home = lazy(() => import('./screens/Home'))
const ActivityDetail = lazy(() => import('./screens/ActivityDetail'))
const ActivityCreate = lazy(() => import('./screens/ActivityCreate'))
const ClubsGroups = lazy(() => import('./screens/ClubsGroups'))
const Profile = lazy(() => import('./screens/Profile'))

function App() {
    return (
        <Suspense fallback={<Loading />}>
            <Routes>
                <Route path="/" element={<Home />} />
                <Route path="/activity/:id" element={<ActivityDetail />} />
                {/* ... */}
            </Routes>
        </Suspense>
    )
}
```

#### B. Мемоизация компонентов

```jsx
// webapp/src/components/ActivityCard.jsx
import { memo } from 'react'

export const ActivityCard = memo(function ActivityCard({ activity, onJoinToggle }) {
    // Component code
}, (prevProps, nextProps) => {
    // Custom comparison
    return prevProps.activity.id === nextProps.activity.id &&
           prevProps.activity.isJoined === nextProps.activity.isJoined
})
```

#### C. Virtual scrolling (для больших списков)

```bash
npm install @tanstack/react-virtual
```

```jsx
// Для списков с >100 элементов
import { useVirtualizer } from '@tanstack/react-virtual'

function LargeList({ items }) {
    const parentRef = useRef()

    const virtualizer = useVirtualizer({
        count: items.length,
        getScrollElement: () => parentRef.current,
        estimateSize: () => 100, // Примерная высота элемента
    })

    return (
        <div ref={parentRef} style={{ height: '600px', overflow: 'auto' }}>
            <div style={{ height: `${virtualizer.getTotalSize()}px` }}>
                {virtualizer.getVirtualItems().map(virtualItem => (
                    <div key={virtualItem.index} style={{
                        position: 'absolute',
                        top: 0,
                        left: 0,
                        width: '100%',
                        transform: `translateY(${virtualItem.start}px)`,
                    }}>
                        <ActivityCard activity={items[virtualItem.index]} />
                    </div>
                ))}
            </div>
        </div>
    )
}
```

**Файлы:** обновить компоненты

---

### 4.3 Comprehensive testing (2 дня)

#### A. Backend tests (покрытие 60%+)

**Структура:**
```
tests/
├── conftest.py          # Fixtures
├── test_api/
│   ├── test_activities.py
│   ├── test_clubs.py
│   ├── test_groups.py
│   ├── test_users.py
│   └── test_auth.py
├── test_services/
│   ├── test_activity_service.py
│   ├── test_club_service.py
│   └── test_membership_service.py
├── test_models/
│   └── test_permissions.py
└── test_integration/
    └── test_full_flow.py
```

**Примеры:**

```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from storage.db import Base, User, Activity, Club, Group
from api_server import app
from api.dependencies import get_db

# Test database
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    """Create test database and session"""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(db_session):
    """Test client with database override"""
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def test_user(db_session):
    """Create test user"""
    user = User(telegram_id=12345, username="testuser", first_name="Test")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def test_activity(db_session, test_user):
    """Create test activity"""
    from datetime import datetime, timedelta
    activity = Activity(
        title="Test Run",
        date=datetime.now() + timedelta(days=1),
        location="Test Park",
        sport_type="running",
        difficulty="easy",
        creator_id=test_user.id
    )
    db_session.add(activity)
    db_session.commit()
    db_session.refresh(activity)
    return activity
```

```python
# tests/test_api/test_activities.py
import pytest
from datetime import datetime, timedelta

def test_create_activity_success(client, test_user):
    """Test creating activity"""
    activity_data = {
        "title": "Morning Run",
        "description": "Easy 5k",
        "date": (datetime.now() + timedelta(days=1)).isoformat(),
        "location": "Central Park",
        "sport_type": "running",
        "difficulty": "easy",
        "distance": 5.0,
    }

    response = client.post(
        "/api/activities",
        json=activity_data,
        headers={"X-Telegram-Init-Data": "mock"}  # Mock auth
    )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Morning Run"
    assert data["creator_id"] == test_user.id

def test_create_activity_past_date_fails(client):
    """Test that creating activity with past date fails"""
    activity_data = {
        "title": "Past Run",
        "date": (datetime.now() - timedelta(days=1)).isoformat(),
        "location": "Park",
        "sport_type": "running",
        "difficulty": "easy",
    }

    response = client.post("/api/activities", json=activity_data)
    assert response.status_code == 422  # Validation error

def test_list_activities_with_filters(client, db_session, test_user):
    """Test listing activities with filters"""
    # Create multiple activities
    activities = [
        Activity(
            title=f"Run {i}",
            date=datetime.now() + timedelta(days=i),
            location="Park",
            sport_type="running" if i % 2 == 0 else "cycling",
            difficulty="easy",
            creator_id=test_user.id
        )
        for i in range(1, 6)
    ]
    db_session.add_all(activities)
    db_session.commit()

    # Filter by sport_type
    response = client.get("/api/activities?sport_type=running")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3  # Only running activities

    # Filter by date range
    date_from = (datetime.now() + timedelta(days=2)).isoformat()
    date_to = (datetime.now() + timedelta(days=4)).isoformat()
    response = client.get(f"/api/activities?date_from={date_from}&date_to={date_to}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3

def test_join_activity_success(client, test_activity, test_user):
    """Test joining activity"""
    response = client.post(
        f"/api/activities/{test_activity.id}/join",
        headers={"X-Telegram-Init-Data": "mock"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "joined"

def test_join_full_activity_fails(client, db_session, test_activity, test_user):
    """Test that joining full activity fails"""
    # Set max participants
    test_activity.max_participants = 1
    db_session.commit()

    # Join first user
    client.post(f"/api/activities/{test_activity.id}/join")

    # Try to join second user (should fail)
    user2 = User(telegram_id=99999, username="user2")
    db_session.add(user2)
    db_session.commit()

    # Mock auth for user2
    response = client.post(
        f"/api/activities/{test_activity.id}/join",
        headers={"X-Telegram-Init-Data": "user2_mock"}
    )

    assert response.status_code == 400
    assert "full" in response.json()["detail"].lower()
```

```python
# tests/test_integration/test_full_flow.py
def test_full_activity_lifecycle(client, db_session, test_user):
    """Test complete activity lifecycle"""

    # 1. Create activity
    activity_data = {
        "title": "Integration Test Run",
        "date": (datetime.now() + timedelta(days=1)).isoformat(),
        "location": "Test Park",
        "sport_type": "running",
        "difficulty": "easy",
    }
    response = client.post("/api/activities", json=activity_data)
    assert response.status_code == 201
    activity_id = response.json()["id"]

    # 2. Get activity details
    response = client.get(f"/api/activities/{activity_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "Integration Test Run"

    # 3. Join activity
    response = client.post(f"/api/activities/{activity_id}/join")
    assert response.status_code == 200
    assert response.json()["status"] == "joined"

    # 4. Get participants
    response = client.get(f"/api/activities/{activity_id}/participants")
    assert response.status_code == 200
    participants = response.json()
    assert len(participants) == 1
    assert participants[0]["username"] == "testuser"

    # 5. Leave activity
    response = client.post(f"/api/activities/{activity_id}/join")
    assert response.status_code == 200
    assert response.json()["status"] == "left"

    # 6. Delete activity
    response = client.delete(f"/api/activities/{activity_id}")
    assert response.status_code == 204

    # 7. Verify deleted
    response = client.get(f"/api/activities/{activity_id}")
    assert response.status_code == 404
```

**Запуск:**
```bash
pytest tests/ -v --cov=api --cov=storage --cov-report=html
```

**Файлы:** `tests/**/*.py`

---

#### B. Frontend tests (покрытие 40%+)

**Примеры:**

```javascript
// webapp/src/hooks/__tests__/useWeekNavigation.test.js
import { renderHook, act } from '@testing-library/react'
import { useWeekNavigation } from '../useWeekNavigation'

describe('useWeekNavigation', () => {
    const mockActivities = [
        {
            id: 1,
            date: '2025-12-15T10:00:00',  // Current week
            isJoined: true,
        },
        {
            id: 2,
            date: '2025-12-22T10:00:00',  // Next week
            isJoined: false,
        },
    ]

    it('initializes with current week', () => {
        const { result } = renderHook(() => useWeekNavigation(mockActivities, 'all'))

        expect(result.current.displayedWeek).not.toBeNull()
        expect(result.current.displayedWeek.weekNumber).toBe(0)
    })

    it('filters by mode', () => {
        const { result, rerender } = renderHook(
            ({ activities, mode }) => useWeekNavigation(activities, mode),
            { initialProps: { activities: mockActivities, mode: 'all' } }
        )

        // 'all' mode shows both
        expect(Object.keys(result.current.displayedWeek.days).length).toBeGreaterThan(0)

        // 'my' mode shows only joined
        rerender({ activities: mockActivities, mode: 'my' })
        // Should have fewer activities
    })

    it('navigates to next week', () => {
        const { result } = renderHook(() => useWeekNavigation(mockActivities, 'all'))

        act(() => {
            result.current.goToNextWeek()
        })

        expect(result.current.displayedWeek.weekNumber).toBe(1)
    })
})
```

**Запуск:**
```bash
npm run test
npm run test:coverage
```

**Файлы:** `webapp/src/**/__tests__/*.test.jsx`

---

### 4.4 Настройка мониторинга (0.5 дня)

#### A. Add Sentry (error tracking)

**Установка:**
```bash
pip install sentry-sdk[fastapi]
npm install @sentry/react
```

**Backend:**
```python
# api_server.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

if not settings.debug:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        integrations=[FastApiIntegration()],
        traces_sample_rate=0.1,
        environment="production",
    )
```

**Frontend:**
```javascript
// webapp/src/main.jsx
import * as Sentry from "@sentry/react"

if (import.meta.env.PROD) {
    Sentry.init({
        dsn: import.meta.env.VITE_SENTRY_DSN,
        integrations: [
            new Sentry.BrowserTracing(),
            new Sentry.Replay(),
        ],
        tracesSampleRate: 0.1,
        replaysSessionSampleRate: 0.1,
        replaysOnErrorSampleRate: 1.0,
    })
}
```

#### B. Add health check endpoint

```python
# api/routers/health.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from api.dependencies import get_db

router = APIRouter(tags=["health"])

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "2.0.0"}

@router.get("/health/db")
async def database_health(db: Session = Depends(get_db)):
    """Database health check"""
    try:
        # Simple query
        db.execute("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": str(e)}
```

**Файлы:** `api/routers/health.py`, обновить `config.py`

---

### 4.5 Commit и review Phase 4

**Checklist:**

- [ ] Database pooling настроен
- [ ] Caching добавлен
- [ ] Request compression включен
- [ ] Frontend code splitting реализован
- [ ] Backend test coverage 60%+
- [ ] Frontend test coverage 40%+
- [ ] Integration tests написаны
- [ ] Sentry настроен
- [ ] Health checks добавлены

**Git:**
```bash
git add .
git commit -m "feat(performance): phase 4 - optimization and testing

Backend:
- Add database connection pooling
- Implement caching with aiocache
- Add GZIP compression
- Optimize serialization

Frontend:
- Implement code splitting
- Add component memoization
- Add virtual scrolling for large lists

Testing:
- Backend test coverage 60%+
- Frontend test coverage 40%+
- Integration tests for full flows
- E2E critical paths

Monitoring:
- Integrate Sentry error tracking
- Add health check endpoints

🤖 Generated with Claude Code
Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

git push origin refactor/phase-4-performance
```

---

## Phase 5: Финальная проверка (1-2 дня)

### Цель
Убедиться, что все работает корректно, документация обновлена, готовность к production.

### 5.1 Code review checklist (0.5 дня)

**Backend:**

- [ ] Все endpoints имеют Pydantic schemas
- [ ] Все endpoints логируют действия
- [ ] Rate limiting применен к критичным endpoints
- [ ] Auth работает корректно (dev mode только в DEBUG)
- [ ] CORS настроен правильно
- [ ] Database queries оптимизированы (нет N+1)
- [ ] Indexes добавлены
- [ ] Нет debug prints
- [ ] Secrets в environment variables
- [ ] Error handling везде реализован

**Frontend:**

- [ ] React Query используется для всех API calls
- [ ] Forms имеют validation
- [ ] Loading states везде
- [ ] Error states везде
- [ ] Нет console.log в production коде
- [ ] Code splitting реализован
- [ ] Компоненты переиспользуются

**Tests:**

- [ ] Backend coverage 60%+
- [ ] Frontend coverage 40%+
- [ ] Integration tests проходят
- [ ] Все тесты проходят

---

### 5.2 Обновить документацию (0.5 дня)

**Обновить:**

- [ ] `README.md` - новая архитектура
- [ ] `docs/ARCHITECTURE.md` - модульная структура
- [ ] `docs/API_DOCS.md` - все endpoints (создать если нет)
- [ ] `docs/DEPLOYMENT.md` - production deployment guide
- [ ] Добавить `CHANGELOG.md`

**Создать:**
```markdown
# CHANGELOG.md

## [2.0.0] - 2025-12-XX

### Added
- Modular API architecture (routers, services)
- Pydantic request/response validation
- Rate limiting
- Logging middleware
- Database indexes
- React Query integration
- Form validation (react-hook-form + zod)
- Comprehensive test suite
- Sentry error tracking
- Health check endpoints

### Changed
- Refactored Home.jsx (342 → 150 lines)
- Improved auth security (dev mode check)
- Optimized database queries
- Better CORS configuration

### Removed
- Debug print statements
- Duplicate code in groups/clubs APIs

### Fixed
- N+1 query problems
- Dev mode auth bypass in production
```

**Файлы:** обновить `docs/*`, создать `CHANGELOG.md`

---

### 5.3 Production deployment checklist (0.5 дня)

**Environment variables:**

```bash
# .env.production
TELEGRAM_BOT_TOKEN=<production_token>
WEB_APP_URL=<production_url>
DATABASE_URL=<postgresql_url>
CORS_ORIGINS=["https://your-domain.com","https://t.me"]
DEBUG=false
LOG_LEVEL=INFO
SENTRY_DSN=<sentry_dsn>
```

**Database migrations:**
```bash
# Убедиться что все миграции применены
alembic upgrade head
```

**Build frontend:**
```bash
cd webapp
npm run build
# Проверить dist/
```

**Test production build локально:**
```bash
# Set production env
export DEBUG=false
export DATABASE_URL=postgresql://...

# Run
python api_server.py

# Test
curl http://localhost:8000/health
curl http://localhost:8000/health/db
```

**Checklist:**

- [ ] Environment variables настроены
- [ ] Database migrations применены
- [ ] Frontend собран (`dist/` готов)
- [ ] Sentry DSN настроен
- [ ] Health checks работают
- [ ] CORS правильно настроен для production
- [ ] Rate limiting работает
- [ ] Logging настроен

---

### 5.4 Performance testing (0.5 дня)

**Load testing с Locust:**

```bash
pip install locust
```

```python
# locustfile.py
from locust import HttpUser, task, between

class AydaRunUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def list_activities(self):
        self.client.get("/api/activities")

    @task(2)
    def get_activity_detail(self):
        self.client.get("/api/activities/1")

    @task(1)
    def join_activity(self):
        self.client.post("/api/activities/1/join")
```

**Запуск:**
```bash
locust -f locustfile.py --host=http://localhost:8000
```

**Метрики для проверки:**
- Response time < 200ms для большинства запросов
- Throughput > 100 req/s
- Error rate < 1%

---

### 5.5 Security audit (опционально, 0.5 дня)

**Checklist:**

- [ ] SQL injection защита (Pydantic + SQLAlchemy)
- [ ] XSS защита (React escaping)
- [ ] CSRF защита (SameSite cookies, не нужно для Telegram WebApp)
- [ ] Rate limiting работает
- [ ] Secrets не в коде
- [ ] Auth проверен
- [ ] Input validation везде
- [ ] Output encoding правильный
- [ ] HTTPS enforced (на production)
- [ ] CORS правильно настроен

**Инструменты:**
```bash
# Bandit (Python security)
pip install bandit
bandit -r api/ storage/ -f json -o security_report.json

# Safety (dependency vulnerabilities)
pip install safety
safety check

# npm audit (frontend)
cd webapp && npm audit
```

---

### 5.6 Final commit и merge

**Checklist:**

- [ ] Все tests проходят
- [ ] Coverage достигнут
- [ ] Документация обновлена
- [ ] CHANGELOG создан
- [ ] Production build успешен
- [ ] Performance приемлемый
- [ ] Security audit пройден

**Git:**
```bash
git add .
git commit -m "docs: phase 5 - final documentation and production readiness

- Update all documentation
- Create CHANGELOG.md
- Add production deployment guide
- Performance testing results
- Security audit passed

Ready for production deployment

🤖 Generated with Claude Code
Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

git push origin refactor/phase-5-final

# Create PR for review
gh pr create --title "Refactoring: Production-ready architecture" \
  --body "Complete refactoring with modular architecture, testing, and optimization. Ready for production deployment."
```

**Merge:**
```bash
# После code review
git checkout master
git merge refactor/phase-5-final
git push origin master

# Tag version
git tag -a v2.0.0 -m "Release 2.0.0 - Production-ready refactored architecture"
git push origin v2.0.0
```

---

## Общие рекомендации

### Работа с рефакторингом

1. **Никогда не рефакторьте без тестов**
   - Сначала tests, потом refactor
   - Запускайте тесты после каждого изменения

2. **Маленькие commits**
   - Один commit = одна логическая изменение
   - Легче откатить если что-то пошло не так

3. **Feature flags для больших изменений**
   ```python
   # config.py
   use_new_api_structure: bool = Field(default=False)

   # api_server.py
   if settings.use_new_api_structure:
       app.include_router(new_router)
   else:
       app.include_router(old_router)
   ```

4. **Parallel работа старого и нового кода**
   - Запускайте оба варианта параллельно
   - Сравнивайте результаты
   - Постепенно переключайте traffic

5. **Документируйте решения**
   - Почему выбрали этот подход
   - Какие альтернативы рассматривали
   - Что может сломаться

### Rollback план

Для каждой фазы иметь plan B:

```bash
# Phase 1 rollback
git revert <commit-hash>
git push origin master

# Phase 2 rollback (если merged)
# Используйте feature flag для отключения новых routers
export USE_NEW_API_STRUCTURE=false

# Database migration rollback
alembic downgrade -1
```

### Мониторинг после deploy

**Первые 24 часа:**
- [ ] Проверять Sentry каждые 2 часа
- [ ] Мониторить response times
- [ ] Проверять error rates
- [ ] Читать user feedback

**Первая неделя:**
- [ ] Daily Sentry review
- [ ] Performance metrics analysis
- [ ] Database query performance
- [ ] User retention metrics

---

## Итоговый Timeline

| Phase | Задачи | Время | Статус |
|-------|--------|-------|--------|
| 1 | Security & Testing Setup | 2-3 дня | ⏳ Pending |
| 2 | Backend Refactoring | 3-4 дня | ⏳ Pending |
| 3 | Frontend Optimization | 2-3 дня | ⏳ Pending |
| 4 | Performance & Testing | 3-4 дня | ⏳ Pending |
| 5 | Final Check & Deploy | 1-2 дня | ⏳ Pending |
| **TOTAL** | | **11-16 дней** | |

**Рекомендация:** Планируйте 14 дней (2 недели) с запасом на непредвиденные проблемы.

---

## Критерии успеха

**Code Quality:**
- ✅ Backend test coverage ≥ 60%
- ✅ Frontend test coverage ≥ 40%
- ✅ Нет критичных security issues
- ✅ Code complexity снижен на 40%+

**Performance:**
- ✅ API response time < 200ms (p95)
- ✅ Frontend load time < 2s
- ✅ Database queries оптимизированы (нет N+1)

**Maintainability:**
- ✅ Модульная архитектура
- ✅ Документация обновлена
- ✅ CI/CD pipeline работает
- ✅ Легко добавлять новые features

**Production Ready:**
- ✅ Все environment variables настроены
- ✅ Logging и monitoring работают
- ✅ Error tracking настроен
- ✅ Health checks работают
- ✅ Rollback план готов

---

## Контакты и помощь

**Вопросы по рефакторингу:**
- Используйте этот документ как чек-лист
- Каждую фазу можно делать независимо
- При проблемах - откатывайтесь на предыдущий commit

**Best practices:**
- Код ревью после каждой фазы
- Тестирование на staging перед production
- Мониторинг после каждого deploy

---

**Готово к старту!** 🚀
