# Ayda Run v2

Telegram Mini App для организации спортивных активностей - бег, велоспорт, лыжи и другие виды спорта.

## Возможности

- **Создание активностей** - Организуй пробежки, велозаезды, лыжные походы
- **Клубы и группы** - Объединяй единомышленников
- **Участие** - Присоединяйся к активностям одним кликом
- **Фильтрация** - Просматривай только свои активности или все доступные
- **Недельный календарь** - Планируй тренировки на неделю вперед
- **Telegram интеграция** - Удобный доступ через Telegram Mini App

## Технологический стек

### Backend
- **FastAPI** - Современный async Python web framework
- **SQLAlchemy** - ORM для работы с базой данных
- **Pydantic** - Валидация данных и настройки
- **SlowAPI** - Rate limiting
- **pytest** - Тестирование (58% coverage)

### Frontend
- **React 18** - UI библиотека
- **React Router** - Навигация
- **React Query** - Server state management с кешированием
- **Tailwind CSS** - Utility-first CSS framework
- **Vite** - Быстрая сборка

### Database
- **SQLite** - Development
- **PostgreSQL** - Production ready

## Quick Start

### 1. Установка зависимостей

**Backend:**
```bash
pip install -r requirements.txt
```

**Frontend:**
```bash
cd webapp
npm install
```

### 2. Настройка окружения

```bash
cp .env.example .env
# Отредактируй .env с твоими настройками
```

**Основные переменные:**
```env
DEBUG=True                          # Dev mode (использует mock auth)
DATABASE_URL=sqlite:///./ayda_run.db
TELEGRAM_BOT_TOKEN=your_token_here
CORS_ORIGINS=["http://localhost:5173"]
RATE_LIMIT_GLOBAL=100/minute
```

### 3. Запуск локально

**Backend (Terminal 1):**
```bash
python api_server.py
# API доступен на http://localhost:8000
# Swagger docs на http://localhost:8000/docs
```

**Frontend (Terminal 2):**
```bash
cd webapp
npm run dev
# Webapp доступен на http://localhost:5173
```

### 4. Тестирование

```bash
# Запустить все тесты с coverage
python -m pytest tests/ -v --cov=app --cov=storage --cov-report=html

# Посмотреть coverage report
open htmlcov/index.html
```

## Структура проекта

```
├── app/                          # Backend application
│   ├── core/
│   │   └── dependencies.py       # Dependency injection (DB, auth, permissions)
│   └── routers/
│       ├── activities.py         # Activities CRUD (359 lines)
│       ├── clubs.py              # Clubs CRUD (180 lines)
│       └── groups.py             # Groups CRUD (362 lines)
├── storage/
│   ├── db.py                     # SQLAlchemy models (84% coverage)
│   └── base.py                   # Database initialization
├── webapp/                       # React frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── ui/              # Generic UI components (Button, Loading, Toast)
│   │   │   ├── shared/          # Domain components (ActivityCard, ClubCard)
│   │   │   └── home/            # Home-specific (DaySection, ModeToggle)
│   │   ├── screens/             # Page components
│   │   ├── hooks/               # React Query hooks
│   │   │   ├── useActivities.ts
│   │   │   ├── useClubs.ts
│   │   │   └── useGroups.ts
│   │   ├── utils/               # Helper functions
│   │   └── queryClient.ts       # React Query config
│   └── dist/                     # Production build
├── tests/                        # Test suite (58% coverage)
│   ├── test_api/                # API endpoint tests
│   ├── test_integration/        # Integration tests
│   └── test_models/             # Model & auth tests
├── docs/                         # Documentation
│   ├── REFACTORING_HISTORY.md   # История рефакторинга
│   ├── CODE_REVIEW_REPORT.md    # Code review отчет
│   ├── ARCHITECTURE.md          # Технические решения
│   └── DESIGN_SYSTEM.md         # UI/UX гайдлайны
├── schemas/                      # Pydantic schemas
├── auth.py                       # Authentication logic
├── permissions.py                # Authorization & RBAC
├── config.py                     # Pydantic Settings
└── api_server.py                 # FastAPI entry point (238 lines)
```

## Архитектура

### Backend Architecture

**Router-Based Structure:**
- Модульные роутеры для каждой domain area (activities, clubs, groups)
- Centralized dependency injection в `app/core/dependencies.py`
- Permissions через reusable FastAPI dependencies
- Без Service Layer (избежали over-engineering)

**Security:**
- ✅ Rate limiting (global + endpoint-specific)
- ✅ CORS configuration
- ✅ Input validation (Pydantic schemas)
- ✅ Dev mode bypass (только для разработки)
- ✅ Role-based access control (ADMIN > ORGANIZER > TRAINER > MEMBER)

**Performance:**
- ✅ Database indexes на часто используемых полях
- ✅ Eager loading для предотвращения N+1 queries
- ✅ Structured logging с middleware

### Frontend Architecture

**Component Organization:**
```
ui/         → Generic reusable UI (Button, Loading, Toast, FormInput)
shared/     → Domain-specific cards (ActivityCard, ClubCard, GroupCard)
home/       → Screen-specific components (DaySection, ModeToggle)
```

**State Management:**
- React Query для server state (auto caching, refetching, invalidation)
- Local state с useState для UI state
- 5-minute stale time для оптимального UX

**Key Features:**
- Weekly calendar view с группировкой активностей
- Collapsible past days для экономии места
- Real-time join/leave с optimistic updates
- Фильтрация "Мои/Все" активности

## API Endpoints

### Activities
```
GET    /api/activities          # List all activities
POST   /api/activities          # Create new activity
GET    /api/activities/{id}     # Get activity details
PATCH  /api/activities/{id}     # Update activity
DELETE /api/activities/{id}     # Delete activity
POST   /api/activities/{id}/join    # Join/leave activity
GET    /api/activities/{id}/participants  # List participants
```

### Clubs
```
GET    /api/clubs               # List all clubs
POST   /api/clubs               # Create new club
GET    /api/clubs/{id}          # Get club details
PATCH  /api/clubs/{id}          # Update club
DELETE /api/clubs/{id}          # Delete club
POST   /api/clubs/{id}/join     # Join/leave club
```

### Groups
```
GET    /api/groups              # List all groups
POST   /api/groups              # Create new group
GET    /api/groups/{id}         # Get group details
PATCH  /api/groups/{id}         # Update group
DELETE /api/groups/{id}         # Delete group
POST   /api/groups/{id}/join    # Join/leave group
```

### Other
```
GET    /api/health              # Health check
GET    /api/users/me            # Get current user
PATCH  /api/users/me/onboarding # Complete onboarding
```

**Swagger Docs:** `http://localhost:8000/docs`

## Тестирование

**Test Coverage: 58.08%** (19/20 tests passing)

```bash
# Run all tests
pytest tests/ -v

# With coverage report
pytest tests/ -v --cov=app --cov=storage --cov-report=html

# Run specific test file
pytest tests/test_api/test_validation.py -v
```

**Coverage breakdown:**
- `storage/db.py`: 84% ✅
- `app/routers/activities.py`: 68% ✅
- `app/routers/clubs.py`: 69% ✅
- `app/routers/groups.py`: 40%
- `permissions.py`: 38%
- `auth.py`: 32%

## Environment Variables

```env
# Application
DEBUG=True                                    # Enable dev mode
LOG_LEVEL=INFO                               # Logging level

# Database
DATABASE_URL=sqlite:///./ayda_run.db         # SQLite for dev
# DATABASE_URL=postgresql://user:pass@host/db  # PostgreSQL for production

# Security
TELEGRAM_BOT_TOKEN=your_bot_token_here       # From @BotFather
SECRET_KEY=your_secret_key_here              # For signing

# CORS
CORS_ORIGINS=["http://localhost:5173"]       # Allowed origins

# Rate Limiting
RATE_LIMIT_GLOBAL=100/minute                 # Global rate limit
RATE_LIMIT_WRITES=10/minute                  # Write operations limit
RATE_LIMIT_READS=50/minute                   # Read operations limit
```

## Deployment

### Production Checklist

1. **Environment:**
   ```bash
   DEBUG=False
   DATABASE_URL=postgresql://...
   CORS_ORIGINS=["https://your-domain.com"]
   ```

2. **Build frontend:**
   ```bash
   cd webapp
   npm run build
   ```

3. **Run migrations:**
   ```bash
   # SQLAlchemy автоматически создает таблицы при старте
   python api_server.py
   ```

4. **Start server:**
   ```bash
   uvicorn api_server:app --host 0.0.0.0 --port 8000
   ```

### Railway / Render

См. [docs/SETUP_GUIDE.md](docs/SETUP_GUIDE.md) для детальных инструкций.

## Документация

- **[REFACTORING_HISTORY.md](docs/REFACTORING_HISTORY.md)** - История рефакторинга, ключевые решения и выводы
- **[CODE_REVIEW_REPORT.md](docs/CODE_REVIEW_REPORT.md)** - Production readiness отчет
- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - Технические решения
- **[DESIGN_SYSTEM.md](docs/DESIGN_SYSTEM.md)** - UI/UX guidelines
- **[CODE_PATTERNS.md](docs/CODE_PATTERNS.md)** - Code examples
- **[docs/refactoring/MASTER.md](docs/refactoring/MASTER.md)** - Master план рефакторинга

## Рефакторинг

Проект прошел успешный рефакторинг (Phases 1-5):

**До рефакторинга:**
- api_server.py: >1000 lines (монолит)
- Test coverage: 0%
- Security: 5 critical issues
- Frontend: Large monolithic components

**После рефакторинга:**
- api_server.py: 238 lines (-76%) ✅
- Test coverage: 58% ✅
- Security: 0 critical issues ✅
- Frontend: Modular components ✅

**Детали:** См. [REFACTORING_HISTORY.md](docs/REFACTORING_HISTORY.md)

## Contributing

При внесении изменений:
1. Создай feature branch
2. Напиши тесты для новой функциональности
3. Убедись что coverage не упал
4. Запусти `pytest tests/ -v`
5. Создай Pull Request

## License

MIT

## Credits

Создано на основе архитектуры [ayda_think](https://github.com/renatmannanov/ayda_think)

---

**Status:** ✅ Production Ready
**Last Updated:** December 2025
**Maintainer:** [@renatmannanov](https://github.com/renatmannanov)
