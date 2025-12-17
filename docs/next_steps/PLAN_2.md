# Analytics Dashboard - Implementation Plan

**Дата создания:** 2025-12-17
**Статус:** Анализ завершен, ожидает подтверждения
**Оценка общая:** ~3-4 часа (фаза 1), ~6-8 часов (полная версия)

---

## Анализ предложенных метрик

### 🎯 Критически важные метрики (Must Have)
**Польза:** ⭐⭐⭐⭐⭐ | **Сложность:** ⭐ | **Время:** ~1-2 часа

#### USER METRICS - базовые
- ✅ **Total registered users** - COUNT(users)
- ✅ **Active users (last 7 days)** - WHERE updated_at/last_activity > now() - 7 days
- ❌ **User retention** - SKIP (сложно для MVP, нужна дополнительная логика трекинга)

**Реализация:**
```python
# Уже есть все данные в таблице users
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM users WHERE updated_at >= NOW() - INTERVAL '7 days';
```

#### ACTIVITY METRICS - базовые
- ✅ **Total activities created** - COUNT(activities)
- ✅ **Activities by status** - GROUP BY status (upcoming/completed/cancelled)
- ✅ **Average participants** - AVG(COUNT(participations))

**Реализация:**
```python
# Данные из таблиц activities + participations
SELECT status, COUNT(*) FROM activities GROUP BY status;
SELECT AVG(participant_count) FROM (
    SELECT activity_id, COUNT(*) as participant_count
    FROM participations GROUP BY activity_id
);
```

#### CLUB METRICS - базовые
- ✅ **Total clubs** - COUNT(clubs)
- ✅ **Activities per club** - COUNT(activities) GROUP BY club_id
- ✅ **Members per club** - COUNT(memberships) WHERE club_id IS NOT NULL

**Реализация:**
```python
# Данные из clubs, activities, memberships
SELECT COUNT(*) FROM clubs;
SELECT club_id, COUNT(*) FROM activities GROUP BY club_id;
```

---

### ⚠️ Полезные, но можно отложить (Should Have)
**Польза:** ⭐⭐⭐ | **Сложность:** ⭐⭐ | **Время:** ~2-3 часа

#### USER METRICS - расширенные
- ⏸️ **User activity by club** - JOIN users + memberships + clubs
- ⏸️ **User retention (Week 1/2/4)** - требует cohort analysis, отложить

**Проблема:** Для retention нужно:
1. Трекать "когда пользователь в первый раз открыл апп" (нет поля)
2. Определять cohorts (группы юзеров по неделям регистрации)
3. Считать % вернувшихся в Week 1, Week 2, Week 4

**Решение:** Отложить на Phase 2, добавить поле `first_seen_at` и `last_seen_at`

#### CLUB METRICS - расширенные
- ⏸️ **Club engagement (% members who use app)** - нужно трекать активность членов
- ⏸️ **Average participants per activity** - есть выше в базовых

#### ACTIVITY METRICS - расширенные
- ⏸️ **Activities with >50% attendance** - нужно сравнивать registered vs attended
- ⏸️ **Average time between creation and activity date** - полезно, но не критично

**Проблема:** Поле `attended` в `participations` есть, но нужно заполнять вручную (кто-то должен отмечать attendance)

---

### ❌ Не нужно для MVP (Nice to Have / Future)
**Польза:** ⭐⭐ | **Сложность:** ⭐⭐⭐⭐ | **Время:** ~4-6 часов

#### ORGANIZER METRICS - слишком сложно
- ❌ **Time spent in app (session duration)** - требует трекинг каждого действия + session management
- ❌ **Number of actions per session** - аналогично, нужен event tracking
- ❌ **Feature usage (which features used most)** - требует instrumentation кода

**Почему не нужно сейчас:**
1. Нет инфраструктуры для event tracking (нужен analytics pipeline)
2. Нужно добавлять логирование в каждый endpoint
3. Нужна отдельная таблица `events` или интеграция с analytics service (Amplitude, Mixpanel)
4. Слишком много работы для малой пользы на старте

**Когда добавлять:** Когда будет 100+ активных пользователей и нужно оптимизировать UX

---

## 🚀 Рекомендуемый план реализации

### **Phase 1: MVP Dashboard (Must Have)** ⭐
**Время:** ~2-3 часа
**Приоритет:** HIGH
**Польза/сложность:** 10/10

#### Что делаем:
1. **Backend: добавить endpoint** `/api/admin/analytics`
   - Возвращает JSON с базовыми метриками
   - Требует admin права (role=ADMIN)

2. **Метрики Phase 1:**
   ```json
   {
     "users": {
       "total": 156,
       "active_7d": 42,
       "new_7d": 12
     },
     "clubs": {
       "total": 8,
       "with_activities": 5
     },
     "activities": {
       "total": 67,
       "upcoming": 12,
       "completed": 48,
       "cancelled": 7,
       "avg_participants": 8.5
     }
   }
   ```

3. **Frontend: простая страница в admin panel**
   - Карточки с цифрами (cards)
   - Никаких графиков, только числа
   - Обновление по кнопке или auto-refresh каждые 30 сек

#### Где добавлять:
```
app/
  routers/
    admin.py          # NEW - admin endpoints
webapp/
  src/
    screens/
      AdminDashboard.jsx  # NEW - dashboard UI
```

#### Пример реализации:
```python
# app/routers/admin.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from storage.db import get_db, User, Club, Activity, Participation
from app.auth import require_admin

router = APIRouter(prefix="/api/admin", tags=["admin"])

@router.get("/analytics")
async def get_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get basic analytics metrics (admin only)"""

    # Users
    total_users = db.query(func.count(User.id)).scalar()
    week_ago = datetime.utcnow() - timedelta(days=7)
    active_users_7d = db.query(func.count(User.id)).filter(
        User.updated_at >= week_ago
    ).scalar()
    new_users_7d = db.query(func.count(User.id)).filter(
        User.created_at >= week_ago
    ).scalar()

    # Clubs
    total_clubs = db.query(func.count(Club.id)).scalar()
    clubs_with_activities = db.query(func.count(func.distinct(Activity.club_id))).filter(
        Activity.club_id.isnot(None)
    ).scalar()

    # Activities
    total_activities = db.query(func.count(Activity.id)).scalar()
    upcoming = db.query(func.count(Activity.id)).filter(
        Activity.status == "upcoming"
    ).scalar()
    completed = db.query(func.count(Activity.id)).filter(
        Activity.status == "completed"
    ).scalar()
    cancelled = db.query(func.count(Activity.id)).filter(
        Activity.status == "cancelled"
    ).scalar()

    # Average participants per activity
    avg_participants = db.query(
        func.avg(func.count(Participation.id))
    ).select_from(Participation).group_by(Participation.activity_id).scalar() or 0

    return {
        "users": {
            "total": total_users,
            "active_7d": active_users_7d,
            "new_7d": new_users_7d
        },
        "clubs": {
            "total": total_clubs,
            "with_activities": clubs_with_activities
        },
        "activities": {
            "total": total_activities,
            "upcoming": upcoming,
            "completed": completed,
            "cancelled": cancelled,
            "avg_participants": round(avg_participants, 1)
        }
    }
```

```jsx
// webapp/src/screens/AdminDashboard.jsx
import { useQuery } from '@tanstack/react-query';
import api from '../services/api';

export default function AdminDashboard() {
  const { data, isLoading } = useQuery({
    queryKey: ['admin', 'analytics'],
    queryFn: () => api.get('/api/admin/analytics'),
    refetchInterval: 30000 // Auto-refresh every 30s
  });

  if (isLoading) return <div>Loading...</div>;

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">Analytics Dashboard</h1>

      {/* Users */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <MetricCard
          title="Total Users"
          value={data.users.total}
          subtitle={`${data.users.active_7d} active (7d)`}
        />
        <MetricCard
          title="New Users (7d)"
          value={data.users.new_7d}
        />
      </div>

      {/* Clubs */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <MetricCard title="Total Clubs" value={data.clubs.total} />
        <MetricCard title="Active Clubs" value={data.clubs.with_activities} />
      </div>

      {/* Activities */}
      <div className="grid grid-cols-4 gap-4">
        <MetricCard title="Total Activities" value={data.activities.total} />
        <MetricCard title="Upcoming" value={data.activities.upcoming} />
        <MetricCard title="Completed" value={data.activities.completed} />
        <MetricCard title="Avg Participants" value={data.activities.avg_participants} />
      </div>
    </div>
  );
}

function MetricCard({ title, value, subtitle }) {
  return (
    <div className="bg-white p-4 rounded-lg shadow">
      <div className="text-gray-500 text-sm">{title}</div>
      <div className="text-3xl font-bold">{value}</div>
      {subtitle && <div className="text-gray-400 text-xs mt-1">{subtitle}</div>}
    </div>
  );
}
```

#### Шаги реализации:
1. ✅ Создать `app/routers/admin.py`
2. ✅ Добавить endpoint `/api/admin/analytics`
3. ✅ Добавить `require_admin` middleware (проверка role=ADMIN)
4. ✅ Создать `webapp/src/screens/AdminDashboard.jsx`
5. ✅ Добавить роут `/admin` в webapp
6. ✅ Тест: проверить что только admin видит дашборд
7. ✅ Коммит: `feat(admin): add basic analytics dashboard`

---

### **Phase 2: Extended Metrics (Should Have)**
**Время:** ~3-4 часа
**Приоритет:** MEDIUM
**Польза/сложность:** 7/10

#### Что добавляем:
1. **User retention tracking**
   - Добавить поля `first_seen_at`, `last_seen_at` в User
   - Middleware для обновления `last_seen_at` при каждом запросе
   - Cohort analysis: Week 1, Week 2, Week 4 retention

2. **Activity attendance rate**
   - % активностей с >50% attendance
   - Требует: организаторы должны отмечать attended=True

3. **Club engagement**
   - % членов клуба, которые были active за последние 7 дней
   - JOIN memberships + users (last_seen_at)

4. **Charts (графики)**
   - Recharts или Chart.js для визуализации
   - График: Users over time (по неделям)
   - График: Activities по типам спорта

#### Когда делать:
- Когда в БД будет >50 пользователей
- Когда будет >20 активностей
- Когда нужно анализировать тренды

---

### **Phase 3: Advanced Analytics (Nice to Have)**
**Время:** ~6-8 часов
**Приоритет:** LOW
**Польза/сложность:** 4/10

#### Что добавляем (только если ОЧЕНЬ нужно):
1. **Event tracking**
   - Таблица `events` (user_id, event_type, timestamp, metadata)
   - Middleware для логирования всех действий
   - Feature usage analytics

2. **Session tracking**
   - Таблица `sessions` (user_id, started_at, ended_at, actions_count)
   - WebSocket/heartbeat для отслеживания онлайн статуса

3. **Integration с analytics service**
   - Amplitude, Mixpanel, PostHog (self-hosted)
   - Автоматический трекинг всех событий

#### Когда делать:
- НЕ СЕЙЧАС
- Когда будет >200 пользователей
- Когда нужно принимать product decisions на основе данных

---

## 📊 Итоговая приоритизация

### Рекомендую делать:
1. ✅ **Phase 1: MVP Dashboard** (~2-3 часа)
   - Максимальная польза, минимальная сложность
   - Сразу увидишь: есть ли пользователи, создают ли активности
   - Понятно, работает ли продукт

### Можно отложить на потом:
2. ⏸️ **Phase 2: Extended Metrics** (~3-4 часа)
   - Делать когда наберется критическая масса пользователей
   - Сначала нужны данные для анализа

### Не делать сейчас:
3. ❌ **Phase 3: Advanced Analytics**
   - Overkill для MVP
   - Тратить время лучше на фичи для пользователей

---

## 🎯 Что ТОЧНО делать сейчас

**Начни с Phase 1:**
1. Простой admin dashboard с 10 базовыми метриками
2. Карточки с цифрами (без графиков)
3. Обновление раз в 30 сек
4. Доступ только для admin

**Время:** 2-3 часа
**Результат:** Сразу видишь, растет ли проект

---

## 📝 Дополнительные улучшения

### Что еще можно добавить в Phase 1 (опционально):
- ✅ **Breakdown by club** - топ-5 клубов по активности
- ✅ **Breakdown by sport type** - какой спорт популярнее
- ✅ **Recent activities** - последние 5 созданных активностей

### Пример расширенной версии:
```json
{
  "users": { ... },
  "clubs": { ... },
  "activities": { ... },
  "breakdown": {
    "top_clubs": [
      {"id": 1, "name": "Almaty Runners", "activities_count": 15},
      {"id": 2, "name": "Trail Kings", "activities_count": 12}
    ],
    "by_sport": {
      "running": 45,
      "trail": 12,
      "cycling": 10
    }
  }
}
```

---

## ✅ Чеклист для Phase 1

### Backend (Python):
- [ ] Создать `app/routers/admin.py`
- [ ] Добавить endpoint `GET /api/admin/analytics`
- [ ] Добавить middleware `require_admin` (проверка user.role == ADMIN)
- [ ] SQL queries для 10 базовых метрик
- [ ] Тесты: pytest для admin endpoint

### Frontend (React):
- [ ] Создать `webapp/src/screens/AdminDashboard.jsx`
- [ ] Компонент `MetricCard` для отображения цифр
- [ ] useQuery для fetching данных
- [ ] Auto-refresh каждые 30 сек
- [ ] Добавить route `/admin` (protected, только для admin)

### Deployment:
- [ ] Проверить права доступа (только admin может видеть)
- [ ] Добавить первого admin user в БД (UPDATE users SET role='admin' WHERE telegram_id=...)
- [ ] Протестировать на production

---

**Вывод:**
- Делай Phase 1 (MVP Dashboard) - максимальная польза за 2-3 часа
- Retention, engagement, event tracking - отложи на Phase 2/3
- Не трать время на сложные метрики пока нет 100+ пользователей

**Готов приступать?** 🚀
