# Индекс всех фаз рефакторинга

**Навигация по задачам рефакторинга**

---

## 📁 Phase 1: Подготовка и безопасность (ГОТОВО)

| Файл | Статус | Описание |
|------|--------|----------|
| `phase-1.1-test-setup.md` | 📄 | Настройка pytest, fixtures, структура тестов |
| `phase-1.2-fix-auth.md` | 📄 | Исправление dev mode bypass, security |
| `phase-1.3-rate-limiting.md` | 📄 | Добавление slowapi, защита от abuse |
| `phase-1.4-cors-validation.md` | 📄 | CORS hardening, Pydantic schemas |
| `phase-1.5-logging-tests.md` | 📄 | Logging, убрать print(), базовые тесты |

---

## 📁 Phase 2: Структурный рефакторинг Backend

**Создать модульную архитектуру API**

Файлы для создания:
- `phase-2.1-api-structure.md` - Создать папки api/routers/, api/services/
- `phase-2.2-dependencies.md` - Создать api/dependencies.py
- `phase-2.3-services.md` - Service layer (ActivityService, ClubService)
- `phase-2.4-routers.md` - Разделить endpoints на routers
- `phase-2.5-permissions.md` - Рефакторинг permissions.py
- `phase-2.6-db-optimization.md` - Indexes, eager loading, pagination

**Краткое описание:**

Разбить монолитный `api_server.py` (698 строк) на:
```
api/
├── dependencies.py      # get_db, get_current_user
├── routers/
│   ├── activities.py    # Activity endpoints
│   ├── clubs.py
│   ├── groups.py
│   └── users.py
└── services/
    ├── activity_service.py  # Business logic
    ├── club_service.py
    └── membership_service.py
```

**Результат:** api_server.py < 200 строк, чистая архитектура

---

## 📁 Phase 3: Оптимизация Frontend

**React Query, упрощение компонентов**

Файлы для создания:
- `phase-3.1-react-query.md` - Интеграция TanStack Query
- `phase-3.2-refactor-home.md` - Home.jsx: 342 → 150 строк
- `phase-3.3-shared-components.md` - DetailPage, ParticipantsList
- `phase-3.4-form-validation.md` - react-hook-form + zod
- `phase-3.5-frontend-tests.md` - Vitest, testing-library (опционально)

**Краткое описание:**

- Заменить useApi на React Query (caching, refetch)
- Вынести DaySection, useWeekNavigation hook
- Создать переиспользуемые компоненты
- Добавить валидацию форм

**Результат:** Меньше кода, лучше UX, кэширование

---

## 📁 Phase 4: Performance и Testing

**Оптимизация производительности, полное покрытие**

Файлы для создания:
- `phase-4.1-backend-perf.md` - DB pooling, caching, compression
- `phase-4.2-frontend-perf.md` - Code splitting, мемоизация
- `phase-4.3-comprehensive-tests.md` - Coverage 60%+ backend, 40%+ frontend
- `phase-4.4-monitoring.md` - Sentry, health checks

**Краткое описание:**

Backend:
- Database connection pooling
- Caching (aiocache)
- GZIP compression
- Optimize serialization

Frontend:
- Lazy loading screens
- React.memo для компонентов
- Virtual scrolling для списков

**Результат:** API < 200ms, frontend < 2s load

---

## 📁 Phase 5: Финальная проверка

**Production-ready**

Файлы для создания:
- `phase-5.1-code-review.md` - Checklist для review
- `phase-5.2-documentation.md` - Обновить docs
- `phase-5.3-production.md` - Deployment checklist, performance testing

**Краткое описание:**

- Code review всех изменений
- Обновить README, ARCHITECTURE, создать CHANGELOG
- Production deployment guide
- Load testing (Locust)
- Security audit

**Результат:** Готов к production deploy

---

## 🔄 Как использовать

### 1. Текущая задача

```bash
# Смотреть MASTER.md для статусов
cat docs/refactoring/MASTER.md

# Открыть текущую задачу
cat docs/refactoring/phase-X.Y-name.md
```

### 2. После завершения задачи

```bash
# Коммит (формат из задачи)
git commit -m "feat(phase-X.Y): ..."

# Обновить MASTER.md - поменять статус на ✅
# Перейти к следующей задаче
```

### 3. Создание новых файлов задач

По мере прохождения Phase 1, создавать файлы для Phase 2-5 по аналогии:

**Структура файла задачи:**
```markdown
# Phase X.Y: Название задачи

**Задача:** Краткое описание
**Время:** Оценка
**Приоритет:** 🔴/🟡/🟢

---

## Цель
Зачем это нужно

## Решение
### Шаг 1
...

## Тесты
...

## Проверка результата
✅ Checklist

## Коммит
Пример commit message

## Следующая задача
Ссылка на следующий файл
```

---

## 📊 Прогресс по фазам

| Phase | Файлов создано | Файлов выполнено | %
|-------|----------------|------------------|------|
| 1 | 5/5 | 0/5 | 0% |
| 2 | 0/6 | 0/6 | 0% |
| 3 | 0/5 | 0/5 | 0% |
| 4 | 0/4 | 0/4 | 0% |
| 5 | 0/3 | 0/3 | 0% |

**Общий прогресс:** 5/23 файлов создано (22%), 0/23 выполнено (0%)

---

## 📝 Заметки

- Файлы Phase 2-5 создаются по мере необходимости
- Формат аналогичен файлам Phase 1
- Каждый файл = одна атомарная задача
- Размер файла ~200-400 строк (не больше!)
- После Phase 1 можно параллельно работать над Phase 2 и 3

---

## 🚀 Быстрый старт

**Начать рефакторинг:**
```bash
# 1. Проверить статусы
cat docs/refactoring/MASTER.md

# 2. Открыть первую задачу
cat docs/refactoring/phase-1.1-test-setup.md

# 3. Создать ветку
git checkout -b refactor/phase-1-security

# 4. Начать!
```

**После Phase 1:**
```bash
# Обновить MASTER.md
# Merge Phase 1
git checkout master && git merge refactor/phase-1-security

# Начать Phase 2
git checkout -b refactor/phase-2-backend
cat docs/refactoring/phase-2.1-api-structure.md
```
