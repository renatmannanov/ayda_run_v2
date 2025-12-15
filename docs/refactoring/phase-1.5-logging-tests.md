# Phase 1.5: Logging и финальные тесты Phase 1

**Задача:** Настроить logging, убрать print(), добавить базовые тесты
**Время:** 0.5-1 день
**Приоритет:** 🟡 Высокий

---

## Часть 1: Настроить Logging (2-3 часа)

### 1. Убрать все print() statements

**Найти все print():**
```bash
grep -r "print(" --include="*.py" api_server.py groups_clubs_api.py
```

**Заменить на logging:**

**Файл:** `api_server.py`

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Console
        logging.FileHandler('app.log')  # File
    ]
)

logger = logging.getLogger(__name__)

# Заменить все:
# print(f"[DEBUG] ...") → logger.debug("...")
# print(f"[INFO] ...") → logger.info("...")
# print(f"[ERROR] ...") → logger.error("...")
```

**Примеры замены:**

```python
# Было:
print(f"[DEBUG] Processing {len(activities)} activities")

# Стало:
logger.debug(f"Processing {len(activities)} activities")

# Было:
print(f"[DEBUG] Activity {activity_id}: Set club_name='{club_name}'")

# Стало:
logger.debug(f"Activity {activity_id}: Set club_name='{club_name}'", extra={
    "activity_id": activity_id,
    "club_name": club_name
})
```

### 2. Добавить logging middleware

**Файл:** `api_server.py`

```python
from starlette.middleware.base import BaseHTTPMiddleware
import time

class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all HTTP requests"""

    async def dispatch(self, request, call_next):
        # Start timer
        start_time = time.time()

        # Log request
        logger.info(
            f"Request started",
            extra={
                "method": request.method,
                "path": request.url.path,
                "client": request.client.host if request.client else None
            }
        )

        # Process request
        try:
            response = await call_next(request)

            # Calculate duration
            process_time = time.time() - start_time

            # Log response
            logger.info(
                f"Request completed",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": round(process_time * 1000, 2)
                }
            )

            return response

        except Exception as e:
            # Log error
            logger.error(
                f"Request failed: {str(e)}",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "error": str(e)
                },
                exc_info=True
            )
            raise

# Add middleware
app.add_middleware(LoggingMiddleware)
```

### 3. Настроить log levels по environment

**Файл:** `config.py`

```python
class Settings(BaseSettings):
    # ... existing fields

    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR)"
    )
```

**Использование:**

```python
# api_server.py
import logging
from config import settings

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

---

## Часть 2: Базовые тесты (3-4 часа)

### 4. Тесты для permissions

**Файл:** `tests/test_models/test_permissions.py`

```python
"""
Tests for permissions logic
"""
import pytest
from storage.db import User, Club, Group, Membership, UserRole
from permissions import (
    can_manage_club,
    can_create_activity_in_club,
    can_manage_group
)

def test_admin_can_manage_any_club(db_session, test_user):
    """Test that ADMIN role can manage any club"""
    # Create club
    club = Club(name="Test Club", creator_id=test_user.id)
    db_session.add(club)
    db_session.commit()

    # Create ADMIN membership
    membership = Membership(
        user_id=test_user.id,
        club_id=club.id,
        role=UserRole.ADMIN
    )
    db_session.add(membership)
    db_session.commit()

    # Test
    assert can_manage_club(db_session, test_user.id, club.id) == True

def test_member_cannot_manage_club(db_session, test_user):
    """Test that MEMBER role cannot manage club"""
    club = Club(name="Test Club", creator_id=999)
    db_session.add(club)
    db_session.commit()

    # MEMBER membership
    membership = Membership(
        user_id=test_user.id,
        club_id=club.id,
        role=UserRole.MEMBER
    )
    db_session.add(membership)
    db_session.commit()

    # Test
    assert can_manage_club(db_session, test_user.id, club.id) == False

def test_non_member_cannot_manage_club(db_session, test_user):
    """Test that non-member cannot manage club"""
    club = Club(name="Test Club", creator_id=999)
    db_session.add(club)
    db_session.commit()

    # No membership
    assert can_manage_club(db_session, test_user.id, club.id) == False
```

### 5. Integration tests для основных flows

**Файл:** `tests/test_integration/test_activity_flow.py`

```python
"""
Integration tests for activity lifecycle
"""
import pytest
from datetime import datetime, timedelta

def test_create_and_join_activity_flow(client, auth_headers, test_user):
    """Test complete flow: create → join → leave → delete"""

    # 1. Create activity
    activity_data = {
        "title": "Integration Test Run",
        "date": (datetime.now() + timedelta(days=1)).isoformat(),
        "location": "Test Park",
        "sport_type": "running",
        "difficulty": "easy"
    }

    response = client.post(
        "/api/activities",
        json=activity_data,
        headers=auth_headers
    )
    assert response.status_code == 201
    activity = response.json()
    activity_id = activity["id"]

    # 2. Get activity details
    response = client.get(f"/api/activities/{activity_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "Integration Test Run"

    # 3. Join activity
    response = client.post(
        f"/api/activities/{activity_id}/join",
        headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["status"] == "joined"

    # 4. Check participants
    response = client.get(f"/api/activities/{activity_id}/participants")
    assert response.status_code == 200
    participants = response.json()
    assert len(participants) == 1
    assert participants[0]["id"] == test_user.id

    # 5. Leave activity
    response = client.post(
        f"/api/activities/{activity_id}/join",
        headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["status"] == "left"

    # 6. Delete activity
    response = client.delete(
        f"/api/activities/{activity_id}",
        headers=auth_headers
    )
    assert response.status_code == 204

    # 7. Verify deleted
    response = client.get(f"/api/activities/{activity_id}")
    assert response.status_code == 404
```

---

## Проверка результата

### ✅ Checklist

- [ ] Все `print()` заменены на `logger.*`
- [ ] Logging middleware добавлен
- [ ] Log level настраивается через config
- [ ] Permissions tests написаны (3+ tests)
- [ ] Integration tests написаны (1+ flow)
- [ ] Все тесты проходят
- [ ] Test coverage >= 30%

### Команды для проверки

```bash
# Проверить что нет print()
grep -r "print(" --include="*.py" api_server.py groups_clubs_api.py
# Не должно найти ничего

# Запустить все тесты
pytest tests/ -v

# Проверить coverage
pytest tests/ --cov --cov-report=term-missing

# Coverage должен быть >= 30%
```

---

## Коммит Phase 1 Complete

```bash
git add api_server.py groups_clubs_api.py tests/
git commit -m "feat(phase-1.5): logging and comprehensive tests

Logging:
- Replace all print() with structured logging
- Add LoggingMiddleware for request/response tracking
- Configure log levels via environment
- Add log file output (app.log)

Testing:
- Add permissions tests (RBAC logic)
- Add integration tests (full activity flow)
- Achieve 30%+ test coverage

Phase: 1.5 - Logging & Tests
Files: api_server.py, tests/*
Tests: ✅ 15+ tests passing, 30%+ coverage
Logging: ✅ Structured logging configured

🤖 Generated with Claude Code
Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## 🎉 Phase 1 Complete!

**Achievements:**
- ✅ Test infrastructure готов
- ✅ Auth security исправлен
- ✅ Rate limiting добавлен
- ✅ CORS настроен правильно
- ✅ Input validation через Pydantic
- ✅ Logging настроен
- ✅ Test coverage 30%+

### Статистика Phase 1

| Метрика | До | После |
|---------|----|----|
| Security issues | 3 критичных | 0 |
| Test coverage | 0% | 30%+ |
| Logging | print() | Structured logging |
| Rate limiting | Нет | ✅ Настроен |
| Input validation | Минимальная | ✅ Pydantic schemas |

---

## Merge и следующие шаги

```bash
# Merge Phase 1
git checkout master
git merge refactor/phase-1-security
git push origin master

# Tag
git tag -a phase-1-complete -m "Phase 1: Security & Testing - Complete"
git push origin phase-1-complete

# Создать ветку для Phase 2
git checkout -b refactor/phase-2-backend
```

---

## Следующая фаза

👉 **Phase 2: Структурный рефакторинг Backend**

См. файлы:
- `phase-2.1-api-structure.md`
- `phase-2.2-dependencies.md`
- ... и т.д.

Или вернитесь к `MASTER.md` для обновления статусов.
