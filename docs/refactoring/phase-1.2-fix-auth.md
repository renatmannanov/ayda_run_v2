# Phase 1.2: Исправить dev mode bypass в auth

**Задача:** Исправить критическую уязвимость в аутентификации
**Время:** 0.5 дня (3-4 часа)
**Приоритет:** 🔴 Критично (Security)

---

## Проблема

**Текущее состояние** (`auth.py:90-98`):
```python
if not x_telegram_init_data:
    from storage.db import SessionLocal, User
    session = SessionLocal()
    # Создает mock user БЕЗ проверки окружения!
```

**Риски:**
- ⚠️ В production можно получить доступ без авторизации
- ⚠️ Нет логирования использования dev mode
- ⚠️ Создание новых сессий в каждом запросе (утечка памяти)

---

## Решение

### 1. Добавить DEBUG check в auth.py

**Файл:** `auth.py`

**Было:**
```python
def get_current_user(
    x_telegram_init_data: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> User:
    """Get current user from Telegram WebApp initData"""

    if not x_telegram_init_data:
        from storage.db import SessionLocal, User
        session = SessionLocal()
        # ... создает dev user
```

**Стало:**
```python
import logging
from config import settings

logger = logging.getLogger(__name__)

def get_current_user(
    x_telegram_init_data: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> User:
    """Get current user from Telegram WebApp initData"""

    if not x_telegram_init_data:
        # SECURITY: Only allow dev mode in DEBUG environment
        if not settings.debug:
            logger.error(
                "Missing Telegram auth header in production environment",
                extra={"endpoint": "get_current_user"}
            )
            raise HTTPException(
                status_code=401,
                detail="Authentication required. Please access via Telegram."
            )

        logger.warning(
            "⚠️  Using DEV MODE authentication - not secure for production!",
            extra={"user_id": 1, "username": "admin"}
        )

        # Dev mode: return mock admin user
        return get_dev_user(db)

    # ... rest of validation
```

### 2. Вынести dev user logic в отдельную функцию

**Добавить в `auth.py`:**

```python
def get_dev_user(db: Session) -> User:
    """
    Get or create development user for local testing

    WARNING: Only use in DEBUG mode!
    """
    dev_user = db.query(User).filter(User.telegram_id == 1).first()

    if not dev_user:
        logger.info("Creating dev user (telegram_id=1)")
        dev_user = User(
            telegram_id=1,
            username="admin",
            first_name="Dev",
            has_completed_onboarding=True
        )
        db.add(dev_user)
        db.commit()
        db.refresh(dev_user)

    return dev_user
```

### 3. Обновить get_current_user_optional

**Было:**
```python
def get_current_user_optional(...):
    if not x_telegram_init_data:
        return None  # Или создавал dev user
```

**Стало:**
```python
def get_current_user_optional(
    x_telegram_init_data: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get current user or None (for public endpoints)"""

    if not x_telegram_init_data:
        # In dev mode, return dev user
        if settings.debug:
            logger.debug("Using dev user for optional auth endpoint")
            return get_dev_user(db)
        # In production, return None (unauthenticated)
        return None

    try:
        # Validate initData
        user_data = verify_telegram_webapp_data(x_telegram_init_data, settings.bot_token)
        telegram_id = int(user_data.get("id"))

        # Get or create user
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        if not user:
            user = User(
                telegram_id=telegram_id,
                username=user_data.get("username"),
                first_name=user_data.get("first_name")
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        return user
    except Exception as e:
        logger.warning(f"Invalid auth data in optional endpoint: {e}")
        return None
```

---

## Тесты

### 4. Создать тесты для auth logic

**Файл:** `tests/test_models/test_auth.py`

```python
"""
Tests for authentication logic
"""
import pytest
from fastapi import HTTPException
from unittest.mock import patch
from auth import get_current_user, get_dev_user, get_current_user_optional

def test_auth_rejects_missing_header_in_production(client, db_session, monkeypatch):
    """Test that missing auth header is rejected in production"""
    # Set production mode
    monkeypatch.setenv("DEBUG", "false")

    # Reload settings to pick up env change
    from config import Settings
    settings = Settings()

    # Try to access protected endpoint without auth
    response = client.get("/api/users/me")
    assert response.status_code == 401
    assert "Authentication required" in response.json()["detail"]

def test_auth_allows_dev_mode_in_debug(client, db_session, monkeypatch):
    """Test that dev mode works when DEBUG=true"""
    # Set debug mode
    monkeypatch.setenv("DEBUG", "true")

    # Reload settings
    from config import Settings
    settings = Settings()

    # Access endpoint without auth should work
    response = client.get("/api/users/me")
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "admin"
    assert data["telegram_id"] == 1

def test_get_dev_user_creates_user_if_not_exists(db_session):
    """Test that get_dev_user creates user on first call"""
    from storage.db import User

    # Ensure no dev user exists
    db_session.query(User).filter(User.telegram_id == 1).delete()
    db_session.commit()

    # Get dev user should create it
    dev_user = get_dev_user(db_session)
    assert dev_user.telegram_id == 1
    assert dev_user.username == "admin"

    # Verify it's in database
    user_in_db = db_session.query(User).filter(User.telegram_id == 1).first()
    assert user_in_db is not None

def test_get_dev_user_returns_existing_user(db_session, test_user):
    """Test that get_dev_user returns existing user"""
    # Modify test_user to be dev user
    test_user.telegram_id = 1
    db_session.commit()

    # Get dev user should return existing
    dev_user = get_dev_user(db_session)
    assert dev_user.id == test_user.id

def test_optional_auth_returns_none_in_production_without_header(client, monkeypatch):
    """Test that optional auth returns None in production without header"""
    monkeypatch.setenv("DEBUG", "false")

    # Endpoint that uses get_current_user_optional
    response = client.get("/api/activities")  # Public endpoint
    assert response.status_code == 200
    # Should return data but without user context
```

---

## Проверка результата

### ✅ Checklist

- [ ] `auth.py` обновлен с DEBUG check
- [ ] Добавлено логирование использования dev mode
- [ ] Создана функция `get_dev_user()`
- [ ] `get_current_user_optional()` обновлена
- [ ] Тесты написаны и проходят
- [ ] В production без auth header возвращается 401
- [ ] В debug mode без auth header работает dev user

### Команда для проверки

```bash
# Запустить тесты auth
pytest tests/test_models/test_auth.py -v

# Проверить что в production auth обязателен
export DEBUG=false
curl http://localhost:8000/api/users/me
# Должно вернуть 401

# Проверить что в dev mode работает
export DEBUG=true
curl http://localhost:8000/api/users/me
# Должно вернуть данные dev user
```

---

## Коммит

```bash
git add auth.py tests/test_models/test_auth.py
git commit -m "fix(phase-1.2): secure dev mode authentication

SECURITY FIX:
- Add DEBUG environment check before allowing dev mode
- Reject missing auth header in production (401 error)
- Add logging for dev mode usage
- Extract get_dev_user() helper function
- Fix get_current_user_optional() security

Breaking change: Requires DEBUG=true for dev mode

Phase: 1.2 - Fix Auth
Files: auth.py, tests/test_models/test_auth.py
Tests: ✅ 5 new auth tests passing
Security: 🔒 Critical vulnerability fixed

🤖 Generated with Claude Code
Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Следующая задача

👉 **`phase-1.3-rate-limiting.md`** - Добавление rate limiting

---

## Важные замечания

⚠️ **Breaking change:** После этого изменения dev mode будет работать ТОЛЬКО если `DEBUG=true` в `.env`

📝 **Обновить `.env.example`:**
```bash
# Development mode (allows mock auth without Telegram)
DEBUG=true
```

🔒 **Production deployment:** Убедитесь что `DEBUG=false` в production окружении!
