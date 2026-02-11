# Claude Code Guidelines for Ayda Run

## Git Workflow

### ВАЖНО: Никогда не коммитить напрямую в master!

### Перед КАЖДЫМ коммитом:
1. Проверить текущую ветку: `git branch --show-current`
2. Если в `master` - СТОП! Перейти в dev или создать feature-ветку

### Порядок работы с новой фичей/фиксом:

```
1. git checkout dev
2. git pull origin dev
3. git checkout -b feature/название-фичи   # или fix/название-бага
4. ... делаем изменения ...
5. git add . && git commit -m "описание"
6. git push origin feature/название-фичи
7. git checkout dev
8. git merge feature/название-фичи
9. git push origin dev
10. Тестируем на dev
11. git checkout master && git merge dev && git push origin master
```

### Если случайно сделал изменения в master (не закоммитил):
```bash
git stash                    # сохранить изменения
git checkout dev             # перейти в dev
git stash pop                # восстановить изменения
# теперь коммитить в dev
```

### Если случайно закоммитил в master:
```bash
git branch backup-branch     # сохранить коммиты в отдельную ветку
git reset --hard origin/master  # откатить master
git checkout dev
git cherry-pick <commit-hash>   # перенести коммиты в dev
```

### Структура веток:
- `master` - продакшн, только проверенный код
- `dev` - разработка, тестирование перед продакшном
- `feature/*` - новые фичи
- `fix/*` - баг-фиксы

## Язык

- Комментарии в коде: английский
- Коммит-сообщения: английский
- Общение с пользователем: русский (если пользователь пишет на русском)

## Quick Reference

| What | Where |
|------|-------|
| Models & Enums | `storage/db.py` |
| API routes | `app/routers/` |
| Bot handlers | `bot/` |
| Permissions | `permissions.py` |
| Auth | `auth.py` |
| Config | `config.py`, `app_config/constants.py` |
| Timezone utils | `app/core/timezone.py` |

## Commands

```bash
# Run API + Bot (production)
python api_server.py

# Run bot only (polling mode, for testing)
python main.py

# Run tests
pytest tests/

# Run tests with coverage
pytest tests/ --cov=. --cov-report=html
```

## Key Patterns

- Database: PostgreSQL, SQLAlchemy 2.0, UUID primary keys
- API: FastAPI + Pydantic v2, dependency injection
- Bot: python-telegram-bot 20+, ConversationHandler for flows
- Frontend: React 18 + React Query + Tailwind
- Timezone: Store naive UTC in DB, convert on output

## Critical Rules

### Alembic Migrations: Enum values MUST use .name (UPPERCASE)
SQLAlchemy `Enum(MyEnum)` sends `.name` (e.g. `SENT`) to PostgreSQL, NOT `.value` (e.g. `sent`).
When writing Alembic migrations with `sa.Enum(...)`, always use uppercase names matching the Python Enum member names:
```python
# CORRECT - matches SQLAlchemy behavior
sa.Enum('SENT', 'LINK_SUBMITTED', name='myenum')

# WRONG - will cause "invalid input value for enum" in production
sa.Enum('sent', 'link_submitted', name='myenum')
```
Note: `create_all()` generates correct uppercase values automatically, so dev may work while prod (using migrations) breaks.

### Telegram Notifications: Always commit DB BEFORE sending messages
Never send Telegram messages inside a transaction that hasn't been committed yet.
If the commit fails, messages are already sent and can't be unsent — causing spam loops.
```python
# CORRECT pattern:
# 1. Prepare all DB changes (add to session)
# 2. session.commit()
# 3. Send Telegram messages

# WRONG pattern:
# 1. Send Telegram message
# 2. Add DB record
# 3. session.commit() -> if this fails, messages already sent = spam
```

### No test values in default parameters
Never leave test/debug values (like `check_interval=30`) as defaults in service constructors.
Production defaults must always be production-ready. Use env vars or config for overrides.

### Background services: Always mark processed records
When a background service iterates over records (e.g. activities needing summary),
mark ALL records as processed — even if they have no actionable data (e.g. no participants).
Otherwise, unprocessable records are re-checked on every cycle forever.

### N+1 queries: Use batch loading for list endpoints
On Railway/cloud, each DB query has network latency (~10-50ms). An N+1 pattern
(1 query per item in a list) causes multi-second response times. Always batch-load
related data with `IN()` clauses and dict lookup in Python.

### Log critical config at startup
Always log important configuration values (API keys present/missing, service URLs, feature flags)
at application startup. This saves hours of debugging when env vars are missing on deploy.

### URL fields in Settings: Always add a validator
Every URL field in `config.py` Settings (like `base_url`, `app_url`) MUST have a `@field_validator`
that ensures `https://` prefix. Without it, Railway env vars without scheme (e.g. `myapp.railway.app`)
produce broken URLs in OAuth redirects, webhooks, etc.
```python
# When adding a new URL field to Settings:
my_url: Optional[str] = Field(None, alias="MY_URL")

# ALWAYS add a validator:
@field_validator('my_url')
@classmethod
def ensure_my_url_https(cls, v):
    if v and not v.startswith('https://'):
        v = f'https://{v}'
    return v
```
