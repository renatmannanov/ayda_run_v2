# План реализации системы доступов (открытые/закрытые сущности)

**Дата:** 2025-12-19
**Статус:** В работе

## Цель

Реализовать систему открытых и закрытых клубов, групп и активностей с механизмом заявок на вступление.

---

## Требования

### Терминология
- **Открытые** сущности - видят ВСЕ, ВСЕ могут свободно вступить
- **Закрытые** сущности - видят ВСЕ, но вступить можно только по заявке организатору

### Функционал

#### 1. Открытые клубы/группы/активности
- Видны ВСЕМ пользователям платформы
- ВСЕ пользователи могут свободно вступить
- Видят ВСЕ данные о сущности (участники, GPX файлы и т.д.)

#### 2. Закрытые клубы/группы/активности
- Видны ВСЕМ пользователям (в списках, карточках)
- Показывается обозначение "закрыто" (🔒)
- НЕ могут свободно вступить - только через заявку
- Скрыты некоторые данные:
  - Список участников (видно только количество)
  - GPX файлы (нельзя скачать)

#### 3. Механика заявок на вступление

**Для пользователя:**
1. Тыкает кнопку "Отправить заявку"
2. Видит подтверждение: "Отправим ваши контактные данные организатору?"
3. При согласии - отправляется заявка

**Для организатора:**
1. Получает уведомление в бота с данными пользователя:
   - Имя
   - Username
   - Выбранные виды спорта
   - Ссылка на Strava (если указана)
2. Кнопки: "Одобрить" / "Отклонить"

**Результаты:**
- При одобрении: пользователь получает уведомление и автоматически добавляется
- При отклонении: пользователь получает уведомление об отказе

#### 4. Автоматическое отклонение заявок
- Для активностей: если активность уже прошла - заявки автоматически отклоняются
- Для других сущностей: можно добавить таймаут (опционально)

#### 5. UI изменения
- Кнопка для открытых: "Присоединиться"
- Кнопка для закрытых: "Отправить заявку"
- Иконка 🔒 для закрытых сущностей

---

## Текущее состояние кода

### Что ЕСТЬ:
- **Group**: поле `is_open` (Boolean) - работает
- **Activity**: поле `visibility` (Enum: PUBLIC, PRIVATE_GROUP, PRIVATE_CLUB, INVITE_ONLY, TELEGRAM_GROUP)
- **Club**: НЕТ поля для открытости/закрытости
- Система уведомлений в боте (`bot/admin_notifications.py`)

### Что НУЖНО добавить:
- **Club**: поле `is_open`
- **Activity**: поле `is_open` (оставляем `visibility` для обратной совместимости)
- **JoinRequest**: новая модель для хранения заявок
- API endpoints для работы с заявками
- Бот handlers для уведомлений и обработки ответов
- Автоматическое отклонение просроченных заявок
- Frontend обновления

---

## План реализации

### **Фаза 1: Модели БД и миграции**

#### 1.1 Обновить модель Club
**Файл:** `storage/db.py:148`

Добавить поле:
```python
# Access control
is_open = Column(Boolean, default=True, nullable=False)  # True = anyone can join
```

#### 1.2 Обновить модель Activity
**Файл:** `storage/db.py:290`

Добавить поле (оставляем `visibility` для обратной совместимости):
```python
# Access control
is_open = Column(Boolean, default=True, nullable=False)  # True = anyone can join
visibility = Column(...)  # оставляем как есть
```

#### 1.3 Создать модель JoinRequest
**Файл:** `storage/db.py` (после модели Participation)

```python
class JoinRequestStatus(str, Enum):
    """Join request status"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"

class JoinRequest(Base):
    """Join request - user's request to join a closed club/group/activity"""
    __tablename__ = 'join_requests'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False, index=True)

    # One of these must be set
    club_id = Column(String(36), ForeignKey('clubs.id'), nullable=True, index=True)
    group_id = Column(String(36), ForeignKey('groups.id'), nullable=True, index=True)
    activity_id = Column(String(36), ForeignKey('activities.id'), nullable=True, index=True)

    # Status
    status = Column(SQLEnum(JoinRequestStatus), default=JoinRequestStatus.PENDING, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)  # Auto-reject after this time

    # Relationships
    user = relationship("User")
    club = relationship("Club")
    group = relationship("Group")
    activity = relationship("Activity")
```

#### 1.4 Создать миграцию Alembic
**Команда:** `alembic revision --autogenerate -m "add_access_control_and_join_requests"`

Миграция должна:
- Добавить `is_open` к Club (default=True)
- Добавить `is_open` к Activity (default=True)
- Создать таблицу `join_requests`
- Установить `is_open=True` для всех существующих записей

---

### **Фаза 2: Обновление Pydantic схем**

#### 2.1 Обновить Club схемы
**Файл:** `schemas/club.py`

```python
class ClubCreate(BaseModel):
    ...
    is_open: bool = Field(default=True, description="True = anyone can join")

class ClubUpdate(BaseModel):
    ...
    is_open: Optional[bool] = None

class ClubResponse(BaseResponse):
    ...
    is_open: bool
```

#### 2.2 Обновить Activity схемы
**Файл:** `schemas/activity.py`

```python
class ActivityCreate(BaseModel):
    ...
    is_open: bool = Field(default=True, description="True = anyone can join")
    # visibility остается для обратной совместимости

class ActivityUpdate(BaseModel):
    ...
    is_open: Optional[bool] = None

class ActivityResponse(BaseResponse):
    ...
    is_open: bool
    # computed fields
    can_view_participants: bool = True  # False if closed and not member
    can_download_gpx: bool = True  # False if closed and not member
```

#### 2.3 Создать схемы для JoinRequest
**Файл:** `schemas/join_request.py` (новый файл)

```python
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from .common import BaseResponse

class JoinRequestCreate(BaseModel):
    """Schema for creating join request"""
    # entity_id будет передаваться через URL

class JoinRequestResponse(BaseResponse):
    """Schema for join request response"""
    user_id: str
    club_id: Optional[str]
    group_id: Optional[str]
    activity_id: Optional[str]
    status: str  # pending, approved, rejected, expired
    expires_at: Optional[datetime]

    # User info (для организатора)
    user_name: Optional[str]
    username: Optional[str]
    user_sports: Optional[str]
    user_strava_link: Optional[str]

class JoinRequestAction(BaseModel):
    """Schema for approving/rejecting join request"""
    # action будет в URL (approve/reject)
```

#### 2.4 Обновить common.py
**Файл:** `schemas/common.py`

Добавить в импорты:
```python
from storage.db import JoinRequestStatus
```

---

### **Фаза 3: Storage слой**

#### 3.1 Создать join_request_storage.py
**Файл:** `storage/join_request_storage.py` (новый файл)

```python
class JoinRequestStorage:
    """Storage layer for join requests"""

    def create_join_request(self, user_id: str, entity_type: str, entity_id: str) -> JoinRequest
    def get_join_request(self, request_id: str) -> Optional[JoinRequest]
    def get_user_pending_request(self, user_id: str, entity_type: str, entity_id: str) -> Optional[JoinRequest]
    def get_pending_requests_for_entity(self, entity_type: str, entity_id: str) -> List[JoinRequest]
    def update_request_status(self, request_id: str, status: JoinRequestStatus) -> JoinRequest
    def delete_expired_requests(self) -> int
    def set_expiry_for_past_activities(self) -> int
```

---

### **Фаза 4: API endpoints**

#### 4.1 Обновить существующие join endpoints

**Clubs** (`app/routers/clubs.py:194`):
```python
@router.post("/{club_id}/join", status_code=201)
def join_club(...):
    club = db.query(Club).filter(Club.id == club_id).first()
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")

    # NEW: Check if open
    if not club.is_open:
        raise HTTPException(
            status_code=403,
            detail="This club is closed. Please send a join request instead."
        )

    # existing logic...
```

**Groups** (`app/routers/groups.py:211`):
- Уже есть проверка `is_open` - оставить как есть

**Activities** (`app/routers/activities.py:271`):
```python
@router.post("/{activity_id}/join", status_code=201)
async def join_activity(...):
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    # NEW: Check if open
    if not activity.is_open:
        raise HTTPException(
            status_code=403,
            detail="This activity is closed. Please send a join request instead."
        )

    # existing logic...
```

#### 4.2 Добавить endpoints для заявок

**Для клубов** (`app/routers/clubs.py`):
```python
@router.post("/{club_id}/request-join", status_code=201)
def request_join_club(...)

@router.get("/{club_id}/join-requests", response_model=List[JoinRequestResponse])
def get_club_join_requests(...)  # только для организаторов

@router.post("/{club_id}/join-requests/{request_id}/approve", status_code=200)
def approve_join_request(...)

@router.post("/{club_id}/join-requests/{request_id}/reject", status_code=200)
def reject_join_request(...)
```

**Для групп** (`app/routers/groups.py`):
```python
@router.post("/{group_id}/request-join", status_code=201)
@router.get("/{group_id}/join-requests", response_model=List[JoinRequestResponse])
@router.post("/{group_id}/join-requests/{request_id}/approve", status_code=200)
@router.post("/{group_id}/join-requests/{request_id}/reject", status_code=200)
```

**Для активностей** (`app/routers/activities.py`):
```python
@router.post("/{activity_id}/request-join", status_code=201)
@router.get("/{activity_id}/join-requests", response_model=List[JoinRequestResponse])
@router.post("/{activity_id}/join-requests/{request_id}/approve", status_code=200)
@router.post("/{activity_id}/join-requests/{request_id}/reject", status_code=200)
```

#### 4.3 Скрытие данных для закрытых сущностей

**Participants endpoint** (`app/routers/activities.py:337`):
```python
@router.get("/{activity_id}/participants", response_model=List[ParticipantResponse])
async def get_participants(activity_id: str, current_user: Optional[User] = Depends(get_current_user_optional), ...):
    activity = db.query(Activity).filter(Activity.id == activity_id).first()

    # NEW: Check if closed and user is not member
    if not activity.is_open and current_user:
        # Check membership in club/group
        is_member = check_user_membership(db, current_user.id, activity)
        if not is_member:
            # Return only count
            count = db.query(Participation).filter(...).count()
            raise HTTPException(
                status_code=403,
                detail=f"This activity is closed. Participants count: {count}"
            )

    # existing logic...
```

**Members endpoints** для клубов и групп - аналогично.

**GPX download** (если есть):
- Добавить проверку `is_open` и членства перед отдачей файла

---

### **Фаза 5: Бот - уведомления**

#### 5.1 Создать join_request_notifications.py
**Файл:** `bot/join_request_notifications.py` (новый файл)

```python
async def notify_organizer_about_join_request(
    bot: Bot,
    request_id: str,
    organizer_telegram_id: int,
    user_data: Dict[str, Any],
    entity_data: Dict[str, Any]
) -> bool:
    """
    Отправить уведомление организатору о новой заявке

    user_data: {
        'name': str,
        'username': str,
        'preferred_sports': List[str],
        'strava_link': Optional[str]
    }
    entity_data: {
        'type': 'club' | 'group' | 'activity',
        'name': str,
        'id': str
    }
    """

async def notify_user_about_approval(
    bot: Bot,
    user_telegram_id: int,
    entity_name: str,
    entity_type: str
) -> bool:
    """Уведомить пользователя об одобрении заявки"""

async def notify_user_about_rejection(
    bot: Bot,
    user_telegram_id: int,
    entity_name: str,
    entity_type: str,
    reason: Optional[str] = None
) -> bool:
    """Уведомить пользователя об отклонении заявки"""
```

#### 5.2 Обновить bot/keyboards.py
```python
def get_join_request_keyboard(request_id: str, entity_type: str) -> InlineKeyboardMarkup:
    """
    Клавиатура для организатора с кнопками одобрения/отклонения

    Кнопки:
    - ✅ Одобрить
    - ❌ Отклонить
    """
```

#### 5.3 Обновить bot/messages.py
```python
def format_join_request_notification(user_data: Dict, entity_data: Dict) -> str:
    """
    Форматирование уведомления организатору

    Пример:
    🔔 Новая заявка на вступление!

    📍 {entity_type}: {entity_name}

    👤 Пользователь:
    Имя: {name}
    Username: @{username}
    Виды спорта: {sports}
    Strava: {strava_link}

    Одобрить заявку?
    """

def format_approval_notification(entity_name: str, entity_type: str) -> str:
    """Уведомление об одобрении"""

def format_rejection_notification(entity_name: str, entity_type: str) -> str:
    """Уведомление об отклонении"""
```

#### 5.4 Создать handlers для callback кнопок
**Файл:** `bot/join_request_handler.py` (новый файл)

```python
async def handle_join_request_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик callback кнопок:
    - approve_join_{request_id}
    - reject_join_{request_id}
    """
```

**Зарегистрировать в** `main.py`:
```python
application.add_handler(CallbackQueryHandler(
    handle_join_request_callback,
    pattern="^(approve|reject)_join_"
))
```

---

### **Фаза 6: Автоматическое отклонение заявок**

#### 6.1 Создать фоновую задачу
**Файл:** `app/services/auto_reject_service.py` (новый файл)

```python
import asyncio
from datetime import datetime
from storage.join_request_storage import JoinRequestStorage
from storage.db import SessionLocal
from bot.join_request_notifications import notify_user_about_rejection

async def auto_reject_expired_requests(bot: Bot):
    """
    Автоматически отклонять заявки для:
    1. Активностей, которые уже прошли
    2. Заявок с истекшим expires_at
    """
    with JoinRequestStorage() as storage:
        # Set expiry for past activities
        expired_count = storage.set_expiry_for_past_activities()

        # Delete expired requests and notify users
        expired_requests = storage.get_expired_requests()
        for request in expired_requests:
            # Update status
            storage.update_request_status(request.id, JoinRequestStatus.EXPIRED)

            # Notify user
            entity_name = get_entity_name(request)
            entity_type = get_entity_type(request)
            await notify_user_about_rejection(
                bot,
                request.user.telegram_id,
                entity_name,
                entity_type,
                reason="Время действия заявки истекло"
            )

async def start_auto_reject_service(bot: Bot):
    """Запустить фоновый сервис автоотклонения (каждые 5 минут)"""
    while True:
        try:
            await auto_reject_expired_requests(bot)
        except Exception as e:
            logger.error(f"Error in auto_reject_service: {e}")

        await asyncio.sleep(300)  # 5 minutes
```

**Запустить в** `main.py`:
```python
# Start background tasks
asyncio.create_task(start_auto_reject_service(application.bot))
```

---

### **Фаза 7: Frontend изменения**

#### 7.1 Обновить отображение кнопок

**В карточках клубов/групп/активностей:**
```javascript
// Псевдокод
if (entity.is_open) {
    button.text = "Присоединиться"
    button.onClick = () => joinEntity(entity.id)
} else {
    button.text = "Отправить заявку"
    button.onClick = () => requestJoinEntity(entity.id)
}
```

#### 7.2 Добавить индикатор закрытости

**В списках и карточках:**
```javascript
if (!entity.is_open) {
    showLockIcon() // 🔒
    showBadge("Закрыто")
}
```

#### 7.3 Скрыть данные для закрытых сущностей

**Список участников:**
```javascript
if (!entity.is_open && !entity.is_member) {
    showParticipantsCount() // "Участников: 15"
    hideParticipantsList()
} else {
    showFullParticipantsList()
}
```

**GPX файл:**
```javascript
if (!entity.is_open && !entity.is_member) {
    hideGPXDownloadButton()
}
```

#### 7.4 Диалог подтверждения при отправке заявки

```javascript
async function requestJoinEntity(entityId) {
    const confirmed = await showConfirmDialog({
        title: "Отправить заявку?",
        message: "Мы отправим ваши контактные данные из профиля организатору",
        confirmText: "Отправить",
        cancelText: "Отмена"
    })

    if (confirmed) {
        await api.post(`/api/activities/${entityId}/request-join`)
        showSuccess("Заявка отправлена!")
    }
}
```

---

### **Фаза 8: Тесты**

#### 8.1 Unit тесты

**Файл:** `tests/test_models/test_join_requests.py`
- Создание JoinRequest
- Валидация (только один из club_id/group_id/activity_id)
- Смена статуса

**Файл:** `tests/test_services/test_join_request_storage.py`
- CRUD операции
- Получение pending requests
- Автоматическое истечение

#### 8.2 Integration тесты

**Файл:** `tests/test_integration/test_join_request_flow.py`
- Тест: пользователь отправляет заявку -> организатор одобряет -> пользователь добавлен
- Тест: пользователь отправляет заявку -> организатор отклоняет -> пользователь НЕ добавлен
- Тест: автоотклонение для прошедшей активности
- Тест: нельзя отправить повторную заявку (пока pending)
- Тест: закрытая сущность - скрыты участники и GPX

**Файл:** `tests/test_api/test_access_control.py`
- Тест: открытая сущность - можно вступить напрямую
- Тест: закрытая сущность - нельзя вступить напрямую, нужна заявка
- Тест: permissions для просмотра списка заявок (только организаторы)

---

## Отдельная задача: Ссылка на Strava

### Добавить поле в User модель
**Файл:** `storage/db.py:88`

```python
class User(Base):
    ...
    # Strava integration
    strava_link = Column(String(500), nullable=True)
```

### Обновить onboarding
**Файл:** `bot/onboarding_handler.py`

Добавить шаг запроса ссылки на Strava (опционально):
```python
STRAVA_LINK = 4  # new state

async def ask_strava_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Запросить ссылку на Strava (опционально)"""
```

### Обновить схемы
**Файл:** `schemas/user.py`

```python
class UserResponse(BaseModel):
    ...
    strava_link: Optional[str]

class UserUpdate(BaseModel):
    ...
    strava_link: Optional[str]
```

### Создать миграцию
```bash
alembic revision --autogenerate -m "add_strava_link_to_user"
```

---

## Порядок выполнения

1. ✅ Создать файл плана
2. ⏳ Фаза 1: Модели БД и миграции
3. ⏳ Фаза 2: Pydantic схемы
4. ⏳ Фаза 3: Storage слой
5. ⏳ Фаза 4: API endpoints
6. ⏳ Фаза 5: Бот уведомления
7. ⏳ Фаза 6: Автоотклонение
8. ⏳ Фаза 7: Frontend
9. ⏳ Фаза 8: Тесты
10. ⏳ Отдельная задача: Strava

---

## Примечания

- `visibility` в Activity оставляем для обратной совместимости
- `is_open` будет основным полем для контроля доступа
- Все изменения должны быть обратно совместимы с существующими данными
- Frontend изменения будут в отдельном репозитории (если есть)

---

## Риски и вопросы

1. **Миграция данных**: Все существующие клубы/группы/активности станут открытыми (is_open=True) - это ОК?
2. **Performance**: Запросы проверки членства могут замедлить API - возможно, нужно кэширование
3. **Race conditions**: Если два пользователя отправляют заявку одновременно - нужна уникальная constraint

---

**Автор:** Claude Sonnet 4.5
**Дата последнего обновления:** 2025-12-19
