# Phase 1.3: Добавить rate limiting

**Задача:** Защитить API от abuse и DDoS
**Время:** 0.5 дня (3-4 часа)
**Приоритет:** 🟡 Высокий (Security)

---

## Цель

Добавить rate limiting для защиты от:
- Spam создания активностей/клубов
- Brute force атак
- DDoS

---

## Решение

### 1. Установить slowapi

```bash
pip install slowapi

# Добавить в requirements.txt
echo "slowapi==0.1.9" >> requirements.txt
```

### 2. Настроить rate limiter в api_server.py

**Файл:** `api_server.py`

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

# Create limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200/minute"]  # Global limit
)

# Add to app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)
```

### 3. Применить к критичным endpoints

**Создание ресурсов (строгий лимит):**

```python
@app.post("/api/activities")
@limiter.limit("10/minute")  # Max 10 активностей в минуту
async def create_activity(
    request: Request,  # Нужен для limiter
    activity_data: ActivityCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # ... logic

@app.post("/api/clubs")
@limiter.limit("5/minute")  # Max 5 клубов в минуту
async def create_club(
    request: Request,
    club_data: ClubCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # ... logic

@app.post("/api/groups")
@limiter.limit("5/minute")
async def create_group(
    request: Request,
    group_data: GroupCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # ... logic
```

**Join/Leave operations (средний лимит):**

```python
@app.post("/api/activities/{activity_id}/join")
@limiter.limit("30/minute")  # Max 30 join/leave в минуту
async def join_activity(
    request: Request,
    activity_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # ... logic
```

**Read operations (мягкий лимит):**

```python
@app.get("/api/activities")
@limiter.limit("100/minute")  # Более мягкий лимит для чтения
async def list_activities(
    request: Request,
    # ... params
):
    # ... logic
```

### 4. Настроить rate limit по user_id (опционально)

Для более точного контроля можно лимитировать по user ID:

```python
from slowapi import Limiter

def get_user_id_key(request: Request) -> str:
    """Get rate limit key from user instead of IP"""
    # Try to get user from auth header
    try:
        init_data = request.headers.get("X-Telegram-Init-Data")
        if init_data:
            user_data = verify_telegram_webapp_data(init_data, settings.bot_token)
            return f"user:{user_data['id']}"
    except:
        pass
    # Fallback to IP
    return f"ip:{request.client.host}"

# Create user-based limiter
user_limiter = Limiter(key_func=get_user_id_key)

# Use in endpoints
@app.post("/api/activities")
@user_limiter.limit("10/minute")  # 10 per user per minute
async def create_activity(...):
    pass
```

---

## Настройка конфигурации

### 5. Добавить rate limit settings в config.py

**Файл:** `config.py`

```python
class Settings(BaseSettings):
    # ... existing fields

    # Rate limiting
    rate_limit_enabled: bool = Field(default=True, description="Enable rate limiting")
    rate_limit_global: str = Field(default="200/minute", description="Global rate limit")
    rate_limit_create: str = Field(default="10/minute", description="Create endpoints limit")
    rate_limit_read: str = Field(default="100/minute", description="Read endpoints limit")
```

**Использование:**

```python
if settings.rate_limit_enabled:
    @limiter.limit(settings.rate_limit_create)
    async def create_activity(...):
        pass
```

---

## Custom error response

### 6. Настроить кастомный response для rate limit

```python
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Custom rate limit error response"""
    return JSONResponse(
        status_code=429,
        content={
            "error": "Too Many Requests",
            "message": "Вы превысили лимит запросов. Пожалуйста, попробуйте позже.",
            "retry_after": exc.detail  # Seconds to wait
        },
        headers={
            "Retry-After": str(exc.detail)
        }
    )
```

---

## Тесты

### 7. Создать тесты для rate limiting

**Файл:** `tests/test_api/test_rate_limiting.py`

```python
"""
Tests for rate limiting
"""
import pytest
import time

def test_rate_limit_on_create_activity(client, auth_headers):
    """Test that creating too many activities triggers rate limit"""
    activity_data = {
        "title": "Test Activity",
        "date": "2025-12-20T10:00:00",
        "location": "Test",
        "sport_type": "running",
        "difficulty": "easy"
    }

    # Make requests up to limit
    for i in range(10):
        response = client.post(
            "/api/activities",
            json=activity_data,
            headers=auth_headers
        )
        # First 10 should succeed or fail for other reasons (not rate limit)
        if response.status_code == 429:
            pytest.fail(f"Rate limited at request {i+1}, expected at 11")

    # 11th request should be rate limited
    response = client.post(
        "/api/activities",
        json=activity_data,
        headers=auth_headers
    )
    assert response.status_code == 429
    data = response.json()
    assert "Too Many Requests" in data["error"]

def test_rate_limit_resets_after_window(client, auth_headers):
    """Test that rate limit resets after time window"""
    # Trigger rate limit
    for i in range(11):
        client.post("/api/activities", json={"title": "test"}, headers=auth_headers)

    # Should be limited
    response = client.post("/api/activities", json={"title": "test"}, headers=auth_headers)
    assert response.status_code == 429

    # Wait for window to reset (61 seconds for 1 minute window)
    time.sleep(61)

    # Should work again
    response = client.post("/api/activities", json={"title": "test"}, headers=auth_headers)
    assert response.status_code != 429  # Should not be rate limited

def test_rate_limit_different_for_read_endpoints(client):
    """Test that read endpoints have different limits"""
    # Read endpoints should have higher limits
    for i in range(50):
        response = client.get("/api/activities")
        assert response.status_code != 429, f"Rate limited at request {i+1}"

@pytest.mark.skip(reason="Slow test - only run manually")
def test_global_rate_limit(client):
    """Test global rate limit across all endpoints"""
    # Make 201 requests to trigger global limit (200/minute)
    for i in range(201):
        client.get("/api/activities")

    # Next request should be limited
    response = client.get("/api/activities")
    assert response.status_code == 429
```

---

## Проверка результата

### ✅ Checklist

- [ ] slowapi установлен
- [ ] Rate limiter настроен в api_server.py
- [ ] Применен к POST endpoints (create)
- [ ] Применен к join/leave endpoints
- [ ] Custom error handler настроен
- [ ] Config для rate limits добавлен
- [ ] Тесты написаны и проходят

### Ручная проверка

```bash
# Запустить сервер
python api_server.py

# В другом терминале - спам requests
for i in {1..15}; do
  curl -X POST http://localhost:8000/api/activities \
    -H "Content-Type: application/json" \
    -d '{"title":"Test","date":"2025-12-20T10:00:00","location":"Test","sport_type":"running","difficulty":"easy"}' \
    && echo " - Request $i"
  sleep 0.1
done

# После 10го запроса должны увидеть 429 Too Many Requests
```

---

## Коммит

```bash
git add api_server.py config.py requirements.txt tests/test_api/test_rate_limiting.py
git commit -m "feat(phase-1.3): add rate limiting protection

- Install and configure slowapi
- Add rate limits to create endpoints (10/min)
- Add rate limits to join/leave endpoints (30/min)
- Add softer limits to read endpoints (100/min)
- Configure global rate limit (200/min)
- Add custom 429 error handler
- Add rate limit configuration in settings
- Add comprehensive rate limit tests

Phase: 1.3 - Rate Limiting
Files: api_server.py, config.py, tests/test_api/test_rate_limiting.py
Tests: ✅ 3 rate limit tests
Security: 🔒 API protected from abuse

🤖 Generated with Claude Code
Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Следующая задача

👉 **`phase-1.4-cors-validation.md`** - CORS и input validation

---

## Production настройки

В production можно использовать Redis для distributed rate limiting:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address
import redis

redis_client = redis.Redis(host='localhost', port=6379, db=0)

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="redis://localhost:6379"
)
```

Это позволит rate limiting работать между несколькими инстансами API сервера.
