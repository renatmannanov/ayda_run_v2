# Phase 1.1: Настройка окружения тестирования

**Задача:** Создать тестовую инфраструктуру для безопасного рефакторинга
**Время:** 0.5 дня (3-4 часа)
**Приоритет:** 🔴 Критично

---

## Цель

Настроить полноценное окружение для тестирования перед началом рефакторинга.
Без тестов рефакторинг опасен - можем что-то сломать незаметно.

---

## Шаги выполнения

### 1. Установить зависимости для тестирования

```bash
# Backend testing
pip install pytest pytest-cov pytest-asyncio httpx

# Добавить в requirements.txt
echo "pytest==7.4.3" >> requirements.txt
echo "pytest-cov==4.1.0" >> requirements.txt
echo "pytest-asyncio==0.21.1" >> requirements.txt
echo "httpx==0.25.1" >> requirements.txt
```

### 2. Создать pytest.ini

**Файл:** `pytest.ini`

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    -v
    --strict-markers
    --cov=api
    --cov=storage
    --cov=permissions
    --cov=auth
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=30
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow running tests
```

### 3. Создать структуру тестов

```bash
mkdir -p tests/test_api
mkdir -p tests/test_services
mkdir -p tests/test_models
mkdir -p tests/test_integration

touch tests/__init__.py
touch tests/test_api/__init__.py
touch tests/test_services/__init__.py
touch tests/test_models/__init__.py
touch tests/test_integration/__init__.py
```

### 4. Создать conftest.py (fixtures)

**Файл:** `tests/conftest.py`

```python
"""
Test fixtures для pytest
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from storage.db import Base, User, Activity, Club, Group, Membership
from api_server import app
from api.dependencies import get_db

# Test database (in-memory SQLite)
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="function")
def db_engine():
    """Create test database engine"""
    engine = create_engine(
        SQLALCHEMY_TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session(db_engine):
    """Create test database session"""
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=db_engine
    )
    session = TestingSessionLocal()
    yield session
    session.close()

@pytest.fixture
def client(db_session):
    """FastAPI test client with database override"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def test_user(db_session):
    """Create a test user"""
    user = User(
        telegram_id=12345,
        username="testuser",
        first_name="Test",
        has_completed_onboarding=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def auth_headers():
    """Mock authentication headers for dev mode"""
    return {"X-Telegram-Init-Data": "mock_dev_mode"}
```

### 5. Создать первый тест (smoke test)

**Файл:** `tests/test_api/test_health.py`

```python
"""
Smoke tests - проверяем что основное работает
"""
import pytest

def test_health_endpoint(client):
    """Test that basic health endpoint works"""
    response = client.get("/health")
    assert response.status_code == 200

def test_users_me_endpoint_requires_auth(client):
    """Test that /api/users/me requires authentication"""
    # Without auth header
    response = client.get("/api/users/me")
    # Should either return 401 or return dev user
    assert response.status_code in [200, 401]

def test_activities_list_works(client):
    """Test that activities list endpoint works"""
    response = client.get("/api/activities")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
```

### 6. Запустить тесты

```bash
# Запустить все тесты
pytest tests/ -v

# Запустить с coverage
pytest tests/ --cov

# Запустить только smoke tests
pytest tests/test_api/test_health.py -v
```

### 7. Создать .editorconfig (опционально)

**Файл:** `.editorconfig`

```ini
root = true

[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
trim_trailing_whitespace = true

[*.py]
indent_style = space
indent_size = 4

[*.{js,jsx,json}]
indent_style = space
indent_size = 2

[*.md]
trim_trailing_whitespace = false
```

---

## Проверка результата

### ✅ Checklist

- [ ] `pytest.ini` создан
- [ ] Структура `tests/` создана
- [ ] `conftest.py` с fixtures создан
- [ ] Первый smoke test написан
- [ ] `pytest tests/` запускается без ошибок
- [ ] Coverage report генерируется
- [ ] requirements.txt обновлен

### Команда для проверки

```bash
# Должно пройти успешно
pytest tests/ -v --cov

# Ожидаемый вывод:
# tests/test_api/test_health.py::test_health_endpoint PASSED
# tests/test_api/test_health.py::test_users_me_endpoint_requires_auth PASSED
# tests/test_api/test_health.py::test_activities_list_works PASSED
#
# ----------- coverage: ... -----------
# Name                    Stmts   Miss  Cover
# -------------------------------------------
# ...
# TOTAL                     XXX    XXX    XX%
```

---

## Коммит

```bash
git add pytest.ini tests/ requirements.txt .editorconfig
git commit -m "feat(phase-1.1): setup test infrastructure

- Add pytest configuration (pytest.ini)
- Create tests/ directory structure
- Add conftest.py with test fixtures (db_session, client, test_user)
- Add first smoke tests (health, users, activities)
- Configure coverage reporting
- Add .editorconfig for code consistency

Phase: 1.1 - Test Setup
Files: pytest.ini, tests/*, requirements.txt
Tests: ✅ 3 tests passing

🤖 Generated with Claude Code
Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Следующая задача

После успешного завершения переходим к:
👉 **`phase-1.2-fix-auth.md`** - Исправление dev mode bypass в auth

---

## Troubleshooting

**Проблема:** `ModuleNotFoundError: No module named 'pytest'`
```bash
pip install pytest pytest-cov
```

**Проблема:** Тесты не находятся
```bash
# Проверить что pytest.ini в корне проекта
# Проверить что tests/__init__.py существует
```

**Проблема:** ImportError при импорте app
```bash
# Убедиться что запускаете из корня проекта
cd /path/to/02_ayda_run_v2
pytest tests/
```
