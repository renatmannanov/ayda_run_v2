# Phase 1.4: CORS и Input Validation

**Задача:** Правильная настройка CORS и добавление Pydantic schemas
**Время:** 1 день
**Приоритет:** 🔴 Критично (Security)

---

## Часть 1: Исправить CORS (2-3 часа)

### Проблема

```python
# api_server.py:29
allow_origins=["*"]  # 🚨 Небезопасно!
```

### Решение

#### 1. Добавить CORS settings в config.py

**Файл:** `config.py`

```python
from typing import List

class Settings(BaseSettings):
    # ... existing fields

    # CORS
    cors_origins: List[str] = Field(
        default_factory=lambda: ["http://localhost:5173"],
        description="Allowed CORS origins"
    )

    @field_validator('cors_origins')
    @classmethod
    def validate_cors_origins(cls, v: List[str], info) -> List[str]:
        """Validate CORS origins - no wildcards in production"""
        # Get debug value from config
        debug = info.data.get('debug', False)

        if "*" in v and not debug:
            raise ValueError(
                "Wildcard CORS origins (*) are not allowed in production. "
                "Please specify exact origins."
            )
        return v
```

#### 2. Обновить CORS middleware в api_server.py

```python
# api_server.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "PUT"],
    allow_headers=["Content-Type", "X-Telegram-Init-Data"],
    max_age=600,  # Cache preflight requests for 10 minutes
)
```

#### 3. Обновить .env.example

```bash
# .env.example

# CORS Origins (comma-separated)
# Development:
CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]

# Production:
# CORS_ORIGINS=["https://your-domain.com","https://t.me"]
```

---

## Часть 2: Input Validation (4-5 часов)

### Создать Pydantic schemas

#### 4. Структура schemas/

```bash
mkdir -p schemas
touch schemas/__init__.py
touch schemas/activity.py
touch schemas/club.py
touch schemas/group.py
touch schemas/user.py
touch schemas/common.py
```

#### 5. Создать base schemas

**Файл:** `schemas/common.py`

```python
"""
Common Pydantic schemas and validators
"""
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
from enum import Enum

class SportType(str, Enum):
    RUNNING = "running"
    TRAIL = "trail"
    HIKING = "hiking"
    CYCLING = "cycling"
    OTHER = "other"

class Difficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

class UserRole(str, Enum):
    MEMBER = "member"
    TRAINER = "trainer"
    ORGANIZER = "organizer"
    ADMIN = "admin"

# Base response model
class BaseResponse(BaseModel):
    """Base response with common fields"""
    id: int
    created_at: datetime

    class Config:
        from_attributes = True  # For SQLAlchemy models
```

#### 6. Activity schemas

**Файл:** `schemas/activity.py`

```python
from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional
from .common import SportType, Difficulty, BaseResponse

class ActivityCreate(BaseModel):
    """Schema for creating activity"""
    title: str = Field(..., min_length=3, max_length=200, description="Activity title")
    description: Optional[str] = Field(None, max_length=2000)
    date: datetime = Field(..., description="Activity date and time")
    location: str = Field(..., min_length=2, max_length=200)
    sport_type: SportType
    difficulty: Difficulty
    distance: Optional[float] = Field(None, ge=0, le=500, description="Distance in km")
    duration: Optional[int] = Field(None, ge=1, le=1440, description="Duration in minutes")
    max_participants: Optional[int] = Field(None, ge=1, le=1000)
    club_id: Optional[int] = None
    group_id: Optional[int] = None

    @validator('date')
    def date_must_be_future(cls, v):
        """Activity date must be in the future"""
        if v < datetime.now():
            raise ValueError('Activity date must be in the future')
        return v

    @validator('group_id')
    def cannot_have_both_club_and_group(cls, v, values):
        """Activity cannot belong to both club and group"""
        if v and values.get('club_id'):
            raise ValueError('Activity cannot belong to both club and group')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Утренняя пробежка",
                "description": "Легкая пробежка в парке",
                "date": "2025-12-20T07:00:00",
                "location": "Центральный парк",
                "sport_type": "running",
                "difficulty": "easy",
                "distance": 5.0,
                "duration": 30,
                "max_participants": 10
            }
        }

class ActivityUpdate(BaseModel):
    """Schema for updating activity"""
    title: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    date: Optional[datetime] = None
    location: Optional[str] = Field(None, min_length=2, max_length=200)
    sport_type: Optional[SportType] = None
    difficulty: Optional[Difficulty] = None
    distance: Optional[float] = Field(None, ge=0, le=500)
    duration: Optional[int] = Field(None, ge=1, le=1440)
    max_participants: Optional[int] = Field(None, ge=1, le=1000)

    @validator('date')
    def date_must_be_future(cls, v):
        if v and v < datetime.now():
            raise ValueError('Activity date must be in the future')
        return v

class ActivityResponse(BaseResponse):
    """Schema for activity response"""
    title: str
    description: Optional[str]
    date: datetime
    location: str
    sport_type: str
    difficulty: str
    distance: Optional[float]
    duration: Optional[int]
    max_participants: Optional[int]
    club_id: Optional[int]
    group_id: Optional[int]
    creator_id: int

    # Computed fields
    participants_count: int = 0
    is_joined: bool = False
    club_name: Optional[str] = None
    group_name: Optional[str] = None
```

#### 7. Club schemas

**Файл:** `schemas/club.py`

```python
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional
from .common import BaseResponse

class ClubCreate(BaseModel):
    """Schema for creating club"""
    name: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    is_paid: bool = Field(default=False)
    price_per_activity: Optional[float] = Field(None, ge=0, le=10000)
    telegram_chat_id: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Беговой клуб Алматы",
                "description": "Дружеский беговой клуб для всех уровней",
                "is_paid": False
            }
        }

class ClubUpdate(BaseModel):
    """Schema for updating club"""
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    is_paid: Optional[bool] = None
    price_per_activity: Optional[float] = Field(None, ge=0, le=10000)

class ClubResponse(BaseResponse):
    """Schema for club response"""
    name: str
    description: Optional[str]
    is_paid: bool
    price_per_activity: Optional[float]
    telegram_chat_id: Optional[str]
    creator_id: int

    # Computed
    members_count: int = 0
    is_member: bool = False
    user_role: Optional[str] = None
```

#### 8. Обновить endpoints с schemas

**Файл:** `api_server.py`

```python
from schemas.activity import ActivityCreate, ActivityUpdate, ActivityResponse

@app.post("/api/activities", response_model=ActivityResponse, status_code=201)
async def create_activity(
    activity_data: ActivityCreate,  # Автоматическая валидация!
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new activity"""
    # activity_data уже провалидирован Pydantic
    new_activity = Activity(**activity_data.dict(), creator_id=current_user.id)
    db.add(new_activity)
    db.commit()
    db.refresh(new_activity)

    # Enrich response
    new_activity.participants_count = 0
    new_activity.is_joined = False

    return new_activity

@app.get("/api/activities", response_model=list[ActivityResponse])
async def list_activities(...):
    # Return will be auto-validated
    return activities
```

---

## Тесты

#### 9. Тесты для validation

**Файл:** `tests/test_api/test_validation.py`

```python
"""
Tests for input validation
"""
import pytest
from datetime import datetime, timedelta

def test_activity_validation_rejects_past_date(client, auth_headers):
    """Test that past date is rejected"""
    data = {
        "title": "Test",
        "date": (datetime.now() - timedelta(days=1)).isoformat(),
        "location": "Test",
        "sport_type": "running",
        "difficulty": "easy"
    }

    response = client.post("/api/activities", json=data, headers=auth_headers)
    assert response.status_code == 422
    assert "future" in response.json()["detail"][0]["msg"].lower()

def test_activity_validation_rejects_invalid_sport_type(client, auth_headers):
    """Test that invalid sport type is rejected"""
    data = {
        "title": "Test",
        "date": (datetime.now() + timedelta(days=1)).isoformat(),
        "location": "Test",
        "sport_type": "invalid",  # Not in enum
        "difficulty": "easy"
    }

    response = client.post("/api/activities", json=data, headers=auth_headers)
    assert response.status_code == 422

def test_activity_validation_title_too_short(client, auth_headers):
    """Test that short title is rejected"""
    data = {
        "title": "AB",  # Too short
        "date": (datetime.now() + timedelta(days=1)).isoformat(),
        "location": "Test",
        "sport_type": "running",
        "difficulty": "easy"
    }

    response = client.post("/api/activities", json=data, headers=auth_headers)
    assert response.status_code == 422

def test_club_validation_rejects_negative_price(client, auth_headers):
    """Test that negative price is rejected"""
    data = {
        "name": "Test Club",
        "is_paid": True,
        "price_per_activity": -100  # Negative
    }

    response = client.post("/api/clubs", json=data, headers=auth_headers)
    assert response.status_code == 422
```

---

## Проверка результата

### ✅ Checklist

- [ ] CORS настроен без wildcards в production
- [ ] CORS validator добавлен в config
- [ ] schemas/ директория создана
- [ ] Activity, Club, Group schemas созданы
- [ ] Endpoints обновлены с schemas
- [ ] Validation tests написаны и проходят
- [ ] .env.example обновлен

### Проверка

```bash
# Тесты validation
pytest tests/test_api/test_validation.py -v

# Проверить что валидация работает
curl -X POST http://localhost:8000/api/activities \
  -H "Content-Type: application/json" \
  -d '{"title":"AB","date":"2025-12-20T10:00:00","location":"Test","sport_type":"running","difficulty":"easy"}'

# Должен вернуть 422 Validation Error
```

---

## Коммит

```bash
git add config.py api_server.py schemas/ tests/test_api/test_validation.py .env.example
git commit -m "feat(phase-1.4): CORS security and input validation

CORS Security:
- Remove wildcard CORS (security risk)
- Add CORS origins validation
- Configure production-safe CORS

Input Validation:
- Create Pydantic schemas for all models
- Add ActivityCreate/Update/Response schemas
- Add ClubCreate/Update/Response schemas
- Add validation for dates, lengths, ranges
- Add comprehensive validation tests

Phase: 1.4 - CORS & Validation
Files: config.py, schemas/*, api_server.py
Tests: ✅ 4 validation tests
Security: 🔒 CORS hardened, Input validated

🤖 Generated with Claude Code
Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Следующая задача

👉 **`phase-1.5-logging-tests.md`** - Logging и финальные тесты Phase 1
