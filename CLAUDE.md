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
