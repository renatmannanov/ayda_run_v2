# План реализации статуса "awaiting" (ожидает подтверждения)

## Обзор

Добавляем новый статус участия `awaiting` — когда тренировка прошла, но пользователь ещё не подтвердил, был он или нет.

**Flow:**
```
registered → awaiting (автоматически после времени старта)
awaiting → attended (пользователь подтвердил участие)
awaiting → missed (пользователь пропустил)
```

---

## Этап 1: Backend — Модели и схемы

### 1.1 Обновить ParticipationStatus enum

**Файл:** `storage/db.py`

Добавить новые статусы:
```python
class ParticipationStatus(str, Enum):
    REGISTERED = "registered"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    AWAITING = "awaiting"    # NEW: ждёт подтверждения
    ATTENDED = "attended"    # NEW: участвовал
    MISSED = "missed"        # NEW: пропустил
```

### 1.2 Обновить схему в Pydantic

**Файл:** `schemas/common.py`

Добавить те же статусы в enum.

---

## Этап 2: Backend — API endpoint для подтверждения

### 2.1 Новый endpoint

**Файл:** `app/routers/activities.py`

```python
POST /api/activities/{id}/confirm
Body: { "attended": true }  # или false
Response: { "status": "attended" }  # или "missed"
```

**Логика:**
1. Проверить, что пользователь имеет participation для этой активности
2. Проверить, что текущий статус = `awaiting`
3. Обновить статус на `attended` или `missed`
4. Вернуть обновлённый статус

---

## Этап 3: Backend — Сервис автоперехода в awaiting

### 3.1 Создать AwaitingConfirmationService

**Файл:** `app/services/awaiting_confirmation_service.py` (новый)

**Логика:**
- Интервал: каждые 5 минут (как AutoRejectService)
- Найти все Participation где:
  - `status = REGISTERED`
  - `activity.date + activity.time < now()` (сразу после старта)
- Для каждой:
  - Обновить `status = AWAITING`
  - Отправить уведомление в Telegram

**Примечание:** Дедлайна для подтверждения нет — пользователь может ответить когда угодно.

### 3.2 Зарегистрировать сервис

**Файл:** `api_server.py`

Добавить инициализацию `AwaitingConfirmationService` в `lifespan()`.

---

## Этап 4: Telegram Bot — Уведомление и кнопки

### 4.1 Функция отправки уведомления

**Файл:** `bot/activity_notifications.py`

Добавить функцию `send_awaiting_confirmation_notification()`:

```python
async def send_awaiting_confirmation_notification(user_id, activity):
    """
    Отправляет сообщение:

    🏃 Тренировка завершена!

    "Утренняя йога"
    пн, 23 дек · 08:00 · Студия Zen

    Ты был на тренировке?

    [Участвовал ✓]  [Пропустил ✕]
    """
```

### 4.2 Inline клавиатура

**Файл:** `bot/keyboards.py`

Добавить функцию `get_confirmation_keyboard(activity_id)`:

```python
def get_confirmation_keyboard(activity_id: str):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Участвовал ✓", callback_data=f"confirm_attended_{activity_id}"),
            InlineKeyboardButton("Пропустил ✕", callback_data=f"confirm_missed_{activity_id}")
        ]
    ])
```

### 4.3 Callback handler

**Файл:** `bot/confirmation_handler.py` (новый)

```python
async def handle_confirmation_callback(update, context):
    """
    Обрабатывает нажатие кнопок "Участвовал" / "Пропустил"

    1. Парсит callback_data
    2. Вызывает API /api/activities/{id}/confirm
    3. Обновляет сообщение на "✓ Отмечено: Участвовал" или "Пропустил"
    """
```

### 4.4 Зарегистрировать handler

**Файл:** `api_server.py`

Добавить `CallbackQueryHandler` для паттерна `confirm_*`.

---

## Этап 5: Frontend — Типы и API

### 5.1 Обновить типы статусов

**Файлы:**
- `webapp/src/api.js` — если есть типизация
- `webapp/src/hooks/useActivities.ts` — если нужны новые хуки

### 5.2 Добавить API метод confirm

**Файл:** `webapp/src/api.js`

```javascript
activitiesApi: {
  // ... существующие методы
  confirm: (id, attended) => api.post(`/api/activities/${id}/confirm`, { attended }),
}
```

### 5.3 Добавить хук useConfirmActivity

**Файл:** `webapp/src/hooks/useActivities.ts`

```typescript
export const useConfirmActivity = () => {
  return useMutation({
    mutationFn: ({ id, attended }) => activitiesApi.confirm(id, attended),
    onSuccess: () => {
      queryClient.invalidateQueries(['activities']);
    },
  });
};
```

---

## Этап 6: Frontend — StatusButton в карточке

### 6.1 Обновить StatusButton

**Файл:** `webapp/src/components/shared/ActivityCard.jsx`

Добавить состояния:

| Статус | Иконка | Цвет | Opacity карточки |
|--------|--------|------|------------------|
| `awaiting` | `?` | оранжевый | 100% |
| `attended` | `✓` | зелёный | 50% |
| `missed` | `✕` | серый | 50% |

```jsx
// Awaiting confirmation - orange outlined circle with ?
if (status === 'awaiting') {
  return (
    <div className="w-9 h-9 rounded-full border-[2.5px] border-orange-400 flex items-center justify-center">
      <span className="text-orange-400 font-bold text-lg">?</span>
    </div>
  );
}

// Attended - green outlined circle with checkmark
if (status === 'attended') {
  return (
    <div className="w-9 h-9 rounded-full border-[2.5px] border-green-500 flex items-center justify-center">
      <svg className="w-5 h-5 text-green-500" ...>✓</svg>
    </div>
  );
}

// Missed - gray outlined circle with X
if (status === 'missed') {
  return (
    <div className="w-9 h-9 rounded-full border-[2.5px] border-gray-400 flex items-center justify-center">
      <svg className="w-5 h-5 text-gray-400" ...>✕</svg>
    </div>
  );
}
```

### 6.2 Обновить opacity карточки

**Файл:** `webapp/src/components/shared/ActivityCard.jsx`

```jsx
const isPast = status === 'attended' || status === 'missed';
// ...
className={`... ${isPast ? 'opacity-50' : ''}`}
```

---

## Этап 7: Frontend — ActivityDetail

### 7.1 Обновить getActionButton()

**Файл:** `webapp/src/screens/ActivityDetail.jsx`

Добавить обработку статусов `awaiting`, `attended`, `missed`:

```jsx
// Awaiting - две кнопки
if (status === 'awaiting') {
  return (
    <div className="flex items-center gap-3">
      <button onClick={handleConfirmMissed} className="flex-1 py-4 border ...">
        Пропустил
      </button>
      <button onClick={handleConfirmAttended} className="flex-1 py-4 bg-gray-800 ...">
        Участвовал
      </button>
    </div>
  );
}

// Attended - зелёный текст
if (status === 'attended') {
  return (
    <div className="flex items-center justify-center gap-2 text-green-600">
      <svg>✓</svg>
      <span>Участвовал</span>
    </div>
  );
}

// Missed - серый текст
if (status === 'missed') {
  return (
    <div className="flex items-center justify-center gap-2 text-gray-400">
      <svg>✕</svg>
      <span>Пропустил</span>
    </div>
  );
}
```

### 7.2 Добавить обработчики

```jsx
const confirmMutation = useConfirmActivity();

const handleConfirmAttended = () => {
  confirmMutation.mutate({ id: activity.id, attended: true });
};

const handleConfirmMissed = () => {
  confirmMutation.mutate({ id: activity.id, attended: false });
};
```

---

## Этап 8: Миграция базы данных

### 8.1 Создать миграцию Alembic

```bash
alembic revision --autogenerate -m "add awaiting attended missed statuses"
alembic upgrade head
```

---

## Порядок выполнения

1. **Backend модели** (Этап 1) — добавить enum значения
2. **Миграция БД** (Этап 8) — применить изменения
3. **Backend API** (Этап 2) — endpoint confirm
4. **Backend сервис** (Этап 3) — автопереход в awaiting
5. **Bot уведомления** (Этап 4) — отправка и обработка
6. **Frontend API** (Этап 5) — метод и хук
7. **Frontend UI** (Этапы 6-7) — StatusButton и ActivityDetail

---

## Файлы для изменения

### Backend (Python):
- `storage/db.py` — enum ParticipationStatus
- `schemas/common.py` — Pydantic enum
- `app/routers/activities.py` — endpoint /confirm
- `app/services/awaiting_confirmation_service.py` — новый файл
- `api_server.py` — регистрация сервиса и handler
- `bot/activity_notifications.py` — функция уведомления
- `bot/keyboards.py` — клавиатура подтверждения
- `bot/confirmation_handler.py` — новый файл

### Frontend (React):
- `webapp/src/api.js` — метод confirm
- `webapp/src/hooks/useActivities.ts` — хук useConfirmActivity
- `webapp/src/components/shared/ActivityCard.jsx` — StatusButton
- `webapp/src/screens/ActivityDetail.jsx` — кнопки подтверждения

### Миграции:
- `alembic/versions/xxx_add_awaiting_statuses.py`

---

## Тестирование

1. Создать активность с датой в прошлом
2. Убедиться, что сервис переводит в `awaiting`
3. Проверить получение уведомления в Telegram
4. Нажать "Участвовал" — статус → `attended`
5. Проверить UI в веб-приложении
6. Повторить для "Пропустил" → `missed`
