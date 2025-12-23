# Ayda Run — Статус "Ожидает подтверждения" (awaiting)

## Зачем

После тренировки мы не знаем, был человек или нет. Вместо автоматической отметки "пропустил" — спрашиваем пользователя.

---

## Flow статусов

```
ДО тренировки:
none → registered

ПОСЛЕ времени старта (автоматически на бэке):
registered → awaiting

Пользователь подтверждает:
awaiting → attended (участвовал)
awaiting → missed (пропустил)
```

---

## Визуалы

### Карточка (StatusButton)

| Статус | Иконка | Цвет | Opacity карточки |
|--------|--------|------|------------------|
| `none` | `+` | серый | 100% |
| `registered` | `✓` | серый | 100% |
| `awaiting` | `?` | оранжевый | 100% |
| `attended` | `✓` | зелёный | 50% |
| `missed` | `✕` | серый | 50% |

**Где в коде:** `ayda-run-activity-list.jsx` → компонент `StatusButton`

### Детали активности (нижняя панель)

**awaiting:**
```
[ Пропустил ]   [ Участвовал ]
```

**attended:**
```
✓ Участвовал (зелёный текст)
```

**missed:**
```
✕ Пропустил (серый текст)
```

**Где в коде:** `ayda-run-activity-detail.jsx` → функция `getActionButton()`

---

## Backend

### 1. Автоматический переход в `awaiting`

**Триггер:** Время старта активности прошло

**Действие:** 
```python
# Cron job или event scheduler
if activity.start_time < now() and registration.status == 'registered':
    registration.status = 'awaiting'
    send_bot_notification(user_id, activity_id)
```

### 2. Эндпоинты подтверждения

```
POST /api/activities/{id}/confirm
Body: { "attended": true }  # или false

Response: { "status": "attended" }  # или "missed"
```

### 3. Статусы в БД

```python
class RegistrationStatus(Enum):
    NONE = "none"
    REGISTERED = "registered"
    AWAITING = "awaiting"
    ATTENDED = "attended"
    MISSED = "missed"
```

---

## Telegram Bot — Уведомление

### Когда отправлять

При переходе `registered → awaiting` (сразу после времени старта)

### Текст сообщения

```
🏃 Тренировка завершена!

"Утренняя йога"
пн, 23 дек · 08:00 · Студия Zen

Ты был на тренировке?

[Участвовал ✓]  [Пропустил ✕]
```

### Inline кнопки

```python
keyboard = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("Участвовал ✓", callback_data=f"confirm_attended_{activity_id}"),
        InlineKeyboardButton("Пропустил ✕", callback_data=f"confirm_missed_{activity_id}")
    ]
])
```

### Callback handler

```python
@bot.callback_query_handler(func=lambda c: c.data.startswith('confirm_'))
def handle_confirmation(call):
    action, status, activity_id = call.data.split('_')
    
    if status == 'attended':
        update_registration_status(user_id, activity_id, 'attended')
        bot.answer_callback_query(call.id, "Отлично! Отмечено ✓")
    else:
        update_registration_status(user_id, activity_id, 'missed')
        bot.answer_callback_query(call.id, "Понял, в следующий раз!")
    
    # Обновить сообщение
    bot.edit_message_text(
        f"✓ Отмечено: {'Участвовал' if status == 'attended' else 'Пропустил'}",
        call.message.chat.id,
        call.message.message_id
    )
```

---

## Референсные файлы

| Файл | Что содержит |
|------|--------------|
| `ayda-run-activity-list.jsx` | StatusButton с awaiting/missed |
| `ayda-run-activity-detail.jsx` | getActionButton() с двумя кнопками |

---

## Чеклист

### Frontend
- [x] StatusButton — оранжевый `?` для awaiting
- [x] StatusButton — серый `✕` для missed  
- [x] Opacity 50% для attended/missed карточек
- [x] Две кнопки "Пропустил" / "Участвовал" в деталях
- [x] Финальные состояния после подтверждения

### Backend
- [ ] Enum статусов в модели
- [ ] Cron/scheduler для перевода в awaiting
- [ ] Эндпоинт подтверждения
- [ ] Триггер отправки в бот

### Telegram Bot
- [ ] Сообщение с inline кнопками
- [ ] Callback handler для подтверждения
- [ ] Обновление сообщения после ответа
