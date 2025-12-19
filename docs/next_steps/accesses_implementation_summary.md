# Резюме реализации системы доступов

**Дата:** 2025-12-19
**Статус:** Фазы 1-4 завершены ✅

---

## Что реализовано

### ✅ Фаза 1: Модели БД и миграции

**Файлы:**
- [storage/db.py](../../storage/db.py)
- [alembic/versions/371b27fe8dfd_add_access_control_and_join_requests.py](../../alembic/versions/371b27fe8dfd_add_access_control_and_join_requests.py)

**Изменения:**
1. Добавлено поле `is_open: Boolean` в модель `Club` (строка 152)
2. Добавлено поле `is_open: Boolean` в модель `Activity` (строка 296)
3. Создана новая модель `JoinRequest` (строки 385-418):
   - Хранит заявки на вступление в закрытые клубы/группы/активности
   - Поля: user_id, club_id, group_id, activity_id, status, expires_at
   - Enum `JoinRequestStatus`: PENDING, APPROVED, REJECTED, EXPIRED
4. Создана и применена миграция Alembic

**Результат:** База данных обновлена, все существующие записи имеют `is_open=True`

---

### ✅ Фаза 2: Pydantic схемы

**Файлы:**
- [schemas/club.py](../../schemas/club.py) - обновлены ClubCreate, ClubUpdate, ClubResponse
- [schemas/activity.py](../../schemas/activity.py) - обновлены ActivityCreate, ActivityUpdate, ActivityResponse
- [schemas/join_request.py](../../schemas/join_request.py) - новый файл со схемами для заявок
- [schemas/common.py](../../schemas/common.py) - добавлен JoinRequestStatus enum

**Изменения:**
1. `ClubCreate/Update/Response` - добавлено поле `is_open`
2. `ActivityCreate/Update/Response` - добавлено поле `is_open`
3. `ActivityResponse` - добавлены computed fields:
   - `can_view_participants: bool`
   - `can_download_gpx: bool`
4. Созданы схемы `JoinRequestCreate`, `JoinRequestResponse`, `JoinRequestAction`

---

### ✅ Фаза 3: Storage слой

**Файл:** [storage/join_request_storage.py](../../storage/join_request_storage.py) (новый)

**Реализованные методы:**
- `create_join_request(user_id, entity_type, entity_id)` - создать заявку
- `get_join_request(request_id)` - получить заявку по ID
- `get_user_pending_request(user_id, entity_type, entity_id)` - проверить наличие pending заявки
- `get_pending_requests_for_entity(entity_type, entity_id)` - все pending заявки для сущности
- `update_request_status(request_id, status)` - обновить статус
- `get_expired_requests()` - получить истекшие заявки
- `set_expiry_for_past_activities()` - установить expiry для прошедших активностей
- `delete_request(request_id)` - удалить заявку

**Паттерн:** Context manager с поддержкой как собственной сессии (для бота), так и переданной (для FastAPI)

---

### ✅ Фаза 4: API endpoints

**Обновленные существующие endpoints:**

1. **Clubs** ([app/routers/clubs.py:194](../../app/routers/clubs.py#L194)):
   - `POST /api/clubs/{club_id}/join` - теперь проверяет `is_open`
   - Если `is_open=False` → возвращает 403 с сообщением использовать `/request-join`

2. **Groups** ([app/routers/groups.py:213](../../app/routers/groups.py#L213)):
   - `POST /api/groups/{group_id}/join` - улучшено сообщение об ошибке для закрытых групп

3. **Activities** ([app/routers/activities.py:273](../../app/routers/activities.py#L273)):
   - `POST /api/activities/{activity_id}/join` - теперь проверяет `is_open`
   - Если `is_open=False` → возвращает 403 с сообщением использовать `/request-join`

**Новые endpoints для заявок:**

#### Clubs ([app/routers/clubs.py:275-461](../../app/routers/clubs.py#L275)):
```
POST   /api/clubs/{club_id}/request-join                  - отправить заявку
GET    /api/clubs/{club_id}/join-requests                 - список заявок (organizer+)
POST   /api/clubs/{club_id}/join-requests/{id}/approve    - одобрить (organizer+)
POST   /api/clubs/{club_id}/join-requests/{id}/reject     - отклонить (organizer+)
```

#### Groups ([app/routers/groups.py:319-505](../../app/routers/groups.py#L319)):
```
POST   /api/groups/{group_id}/request-join                - отправить заявку
GET    /api/groups/{group_id}/join-requests               - список заявок (trainer+)
POST   /api/groups/{group_id}/join-requests/{id}/approve  - одобрить (trainer+)
POST   /api/groups/{group_id}/join-requests/{id}/reject   - отклонить (trainer+)
```

#### Activities ([app/routers/activities.py:387-588](../../app/routers/activities.py#L387)):
```
POST   /api/activities/{activity_id}/request-join         - отправить заявку
GET    /api/activities/{activity_id}/join-requests        - список заявок (creator only)
POST   /api/activities/{activity_id}/join-requests/{id}/approve - одобрить (creator only)
POST   /api/activities/{activity_id}/join-requests/{id}/reject  - отклонить (creator only)
```

**Логика endpoints:**
- Проверка прав доступа (permissions)
- Проверка существования pending заявки
- Проверка членства
- Автоматическая установка `expires_at` для activities (дата активности)
- TODO комментарии для интеграции с ботом (Фаза 5)

---

## Что осталось сделать

### ⏳ Фаза 5: Бот уведомления

**Нужно создать:**
- `bot/join_request_notifications.py` - функции отправки уведомлений
- `bot/join_request_handler.py` - обработчик callback кнопок
- Обновить `bot/keyboards.py` - клавиатуры для одобрения/отклонения
- Обновить `bot/messages.py` - форматирование сообщений

**Интеграция с API:**
- В endpoints `request-join` добавить отправку уведомления организатору
- В endpoints `approve/reject` добавить отправку уведомлений пользователю

**Зарегистрировать в main.py:**
```python
application.add_handler(CallbackQueryHandler(
    handle_join_request_callback,
    pattern="^(approve|reject)_join_"
))
```

---

### ⏳ Фаза 6: Автоотклонение заявок

**Нужно создать:**
- `app/services/auto_reject_service.py` - фоновый сервис

**Функционал:**
- Каждые 5 минут проверять expired заявки
- Для активностей: автоматически устанавливать expires_at = activity.date
- Обновлять статус на EXPIRED
- Отправлять уведомления пользователям

**Запустить в main.py:**
```python
asyncio.create_task(start_auto_reject_service(application.bot))
```

---

### ⏳ Фаза 7: Frontend изменения

**UI компоненты:**
1. Кнопки:
   - Открытые сущности: "Присоединиться"
   - Закрытые сущности: "Отправить заявку"
2. Индикаторы:
   - Иконка 🔒 для закрытых сущностей
   - Бейдж "Закрыто"
3. Диалог подтверждения при отправке заявки
4. Скрытие данных для закрытых сущностей:
   - Список участников (показывать только count)
   - GPX файлы (скрыть кнопку скачивания)

---

### ⏳ Фаза 8: Тесты

**Unit тесты:**
- `tests/test_models/test_join_requests.py`
- `tests/test_services/test_join_request_storage.py`

**Integration тесты:**
- `tests/test_integration/test_join_request_flow.py`
  - Флоу: заявка → одобрение → вступление
  - Флоу: заявка → отклонение
  - Автоотклонение для прошедших активностей
  - Нельзя отправить повторную заявку
- `tests/test_api/test_access_control.py`
  - Открытые/закрытые сущности
  - Проверка permissions

---

## Как тестировать реализованное

### 1. Создать закрытый клуб

```bash
curl -X POST http://localhost:8000/api/clubs \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Закрытый беговой клуб",
    "description": "Только для опытных бегунов",
    "is_open": false
  }'
```

### 2. Попытаться вступить напрямую (должна быть ошибка 403)

```bash
curl -X POST http://localhost:8000/api/clubs/{club_id}/join \
  -H "Authorization: Bearer USER_TOKEN"

# Ответ: {"detail": "This club is closed. Please send a join request..."}
```

### 3. Отправить заявку

```bash
curl -X POST http://localhost:8000/api/clubs/{club_id}/request-join \
  -H "Authorization: Bearer USER_TOKEN"

# Ответ: {"message": "Join request sent successfully", "request_id": "..."}
```

### 4. Организатор просматривает заявки

```bash
curl -X GET http://localhost:8000/api/clubs/{club_id}/join-requests \
  -H "Authorization: Bearer ORGANIZER_TOKEN"

# Ответ: [{"id": "...", "user_name": "...", "username": "@user", ...}]
```

### 5. Одобрить заявку

```bash
curl -X POST http://localhost:8000/api/clubs/{club_id}/join-requests/{request_id}/approve \
  -H "Authorization: Bearer ORGANIZER_TOKEN"

# Ответ: {"message": "Join request approved successfully"}
```

### 6. Проверить членство

```bash
curl -X GET http://localhost:8000/api/clubs/{club_id}/members \
  -H "Authorization: Bearer ANY_TOKEN"

# Теперь пользователь в списке участников
```

---

## Известные ограничения текущей реализации

1. **Нет уведомлений в бот** - отмечено TODO комментариями в коде
2. **Нет автоотклонения** - нужна Фаза 6
3. **Нет скрытия данных** - participants endpoints пока возвращают все данные
4. **Frontend не обновлен** - нужны UI изменения

---

## Следующие шаги

1. **Протестировать API endpoints вручную** - создать закрытый клуб и пройти весь флоу
2. **Фаза 5: Реализовать бот уведомления** - чтобы организаторы получали заявки и могли одобрять из бота
3. **Фаза 6: Автоотклонение** - для активностей, которые уже прошли
4. **Фаза 7-8**: Frontend и тесты

---

## Отдельная задача: Strava link

Добавить поле `strava_link` в User модель:

```python
# storage/db.py
class User(Base):
    ...
    strava_link = Column(String(500), nullable=True)
```

Создать миграцию:
```bash
python -m alembic revision --autogenerate -m "add_strava_link_to_user"
python -m alembic upgrade head
```

Обновить onboarding в боте для запроса ссылки на Strava (опционально).

---

**Автор:** Claude Sonnet 4.5
**Дата:** 2025-12-19
