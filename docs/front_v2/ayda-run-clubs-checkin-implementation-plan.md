# План реализации: Обновления клубов/групп + Чекин организаторов

## СТАТУС: РЕАЛИЗОВАНО ✅

## Обзор задачи

Три основных направления:
1. ✅ **Обновления экранов клубов и групп** — показ родительского клуба для групп (кликабельный)
2. ✅ **Чекин посещаемости для организаторов** — UI и API для отметки посещения
3. ✅ **Уведомления в боте** — организатору приходит запрос на чекин после завершения активности

---

## ЧАСТЬ 1: Обновления экранов клубов и групп

### 1.1 Показ родительского клуба для групп (КРИТИЧНО)

**Проблема:** Сейчас группы не показывают родительский клуб.

**Что нужно сделать:**
- В карточке группы `GroupCard.jsx` — уже реализовано (строка 37-38), но `club_name` может не приходить
- В деталях группы `ClubGroupDetail.jsx` — уже есть (строка 249-251), но нужно сделать кликабельным

**Изменения:**

#### a) Карточка группы — сделать клуб кликабельным
**Файл:** `webapp/src/components/shared/GroupCard.jsx`

```jsx
// Текущий код (строки 34-39):
{(group.club_name || group.parentClub) && (
    <span className="text-gray-400 font-normal truncate"> / {group.club_name || group.parentClub}</span>
)}

// Нужно изменить на:
{(group.club_name || group.parentClub) && (
    <span
        onClick={(e) => { e.stopPropagation(); navigate(`/club/${group.clubId}`); }}
        className="text-gray-400 font-normal truncate hover:underline cursor-pointer"
    > / {group.club_name || group.parentClub}</span>
)}
```

#### b) Экран деталей группы — сделать клуб кликабельным
**Файл:** `webapp/src/screens/ClubGroupDetail.jsx`

```jsx
// Текущий код (строки 249-251):
{!isClub && (item.club_name || item.parentClub) && (
    <span className="text-gray-400 font-normal"> / {item.club_name || item.parentClub}</span>
)}

// Нужно изменить на:
{!isClub && (item.club_name || item.parentClub) && (
    <span
        onClick={() => navigate(`/club/${item.clubId}`)}
        className="text-gray-400 font-normal hover:underline cursor-pointer"
    > / {item.club_name || item.parentClub}</span>
)}
```

#### c) API — убедиться что `club_id` передаётся
**Файл:** `webapp/src/api.js`

```javascript
// Текущий transformGroup (строка 119):
const transformGroup = (g) => !g ? null : ({
    id: g.id,
    name: g.name,
    // ...
    clubId: g.club_id,  // ✅ Уже есть
    // ...
})
```

Проверить: в `schemas/group.py` `GroupResponse` должен включать `club_id` — ✅ уже есть (строка 36).

---

### 1.2 Видимость в подзаголовке

**Где:** `ClubGroupDetail.jsx`

**Текущий код (строки 253-256):**
```jsx
<p className="text-sm text-gray-500">
    {isClub ? '🏆 Клуб' : '👥 Группа'}
    {!item.isOpen && ' · Закрытый'}
</p>
```

**Новый формат:**
```jsx
<p className="text-sm text-gray-500">
    {item.members} участников
    {isClub && item.groupsCount > 0 && ` · ${item.groupsCount} групп`}
    {' · '}
    {isClub ? (
        item.visibility === 'public'
            ? '🌐 Публичный'
            : '🔒 Закрытый'
    ) : (
        item.visibility === 'public'
            ? '🌐 Публичная'
            : `🏆 ${item.visibilityClubName || item.club_name || 'Только для клуба'}`
    )}
</p>
```

**Требуется в API:**
- Добавить поле `visibility` для клубов и групп
- Для групп добавить `visibilityClubName`

---

### 1.3 Виды спорта (sports)

**Где:** После подзаголовка в `ClubGroupDetail.jsx`

**Добавить иконки:**
```jsx
{item.sports && item.sports.length > 0 && (
    <div className="flex gap-1 mt-2">
        {item.sports.map(sportId => (
            <span key={sportId} className="text-base">
                {sportTypes[sportId]?.icon}
            </span>
        ))}
    </div>
)}
```

**Требуется в API:**
- Добавить поле `sports: string[]` в `ClubResponse` и `GroupResponse`
- Добавить колонку `sports` (JSON) в модели `Club` и `Group`

---

### 1.4 Ссылки (Links)

**Где:** Новая секция в `ClubGroupDetail.jsx` перед admin actions

**Добавить:**
```jsx
{/* Links */}
{item.links && item.links.length > 0 && (
    <>
        <div className="border-t border-gray-200 my-4" />
        <div>
            <div className="flex items-center justify-between mb-2">
                <p className="text-sm text-gray-500">Ссылки</p>
                {isAdmin && (
                    <button
                        onClick={() => setShowAddLink(true)}
                        className="text-xs text-gray-400 hover:text-gray-600"
                    >
                        + Добавить
                    </button>
                )}
            </div>
            {item.links.map(link => (
                <LinkItem key={link.id} link={link} />
            ))}
        </div>
    </>
)}
```

**Требуется в API:**
- Новая модель `Link` с полями: `id`, `entity_type`, `entity_id`, `type`, `label`, `url`
- CRUD эндпоинты для ссылок
- Или хранить ссылки как JSON в клубах/группах

---

## ЧАСТЬ 2: Чекин посещаемости для организаторов

### 2.1 Логика чекина

**Условия для показа кнопки чекина:**
- Активность принадлежит клубу ИЛИ группе (`activity.clubId || activity.groupId`)
- Активность завершилась (`isPast === true`)
- Пользователь — организатор (`isCreator` или `isClubAdmin` или `isGroupAdmin`)

### 2.2 Изменения в ActivityDetail.jsx

**Файл:** `webapp/src/screens/ActivityDetail.jsx`

**a) Добавить состояния:**
```jsx
const [showAttendance, setShowAttendance] = useState(false)
const [attendanceData, setAttendanceData] = useState(participants)
```

**b) Определить `isOrganizer`:**
```jsx
// Организатор если:
// - Создатель активности
// - ИЛИ админ клуба (если активность клубная)
// - ИЛИ тренер группы (если активность групповая)
const isOrganizer = isCreator || activity?.isClubAdmin || activity?.isGroupAdmin
```

**c) Добавить проверку для показа кнопки чекина:**
```jsx
const canMarkAttendance = isOrganizer && isPast && (activity?.clubId || activity?.groupId)
```

**d) Модифицировать `getActionButton()`:**
```jsx
// ДОБАВИТЬ в начало функции:
// ORGANIZER: Show attendance marking button when activity is finished
if (canMarkAttendance && activity?.participationStatus !== 'attended' && activity?.participationStatus !== 'missed') {
    const attendedCount = attendanceData.filter(p => p.attended === true).length
    return (
        <button
            onClick={() => setShowAttendance(true)}
            className="w-full py-4 bg-gray-800 text-white rounded-xl text-sm font-medium hover:bg-gray-700 transition-colors flex items-center justify-center gap-2"
        >
            <span>📋</span>
            <span>Отметить посещение</span>
            {attendedCount > 0 && (
                <span className="bg-white/20 px-2 py-0.5 rounded-full text-xs">
                    {attendedCount}/{attendanceData.length}
                </span>
            )}
        </button>
    )
}
```

### 2.3 Компонент AttendancePopup

**Создать новый компонент:** `webapp/src/components/shared/AttendancePopup.jsx`

Функционал:
- Список участников с чекбоксами (null → true → false → null)
- Прогресс-бар отмеченных
- Поиск и добавление участников из клуба/группы
- Кнопка "Сохранить" с отправкой в API

### 2.4 API для чекина

**Новый эндпоинт:** `POST /api/activities/{id}/mark-attendance`

**Файл:** `app/routers/activities.py`

```python
@router.post("/{activity_id}/mark-attendance", status_code=200)
async def mark_attendance(
    activity_id: str,
    attendance_data: List[AttendanceItem],  # [{user_id, attended: bool|null}]
    notify_participants: bool = Query(True),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Mark attendance for multiple participants (organizers only)

    Only available for club/group activities.
    Sends notifications to participants about their attendance status.
    """
    activity = db.query(Activity).filter(Activity.id == activity_id).first()

    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Check if activity belongs to club or group
    if not activity.club_id and not activity.group_id:
        raise HTTPException(
            status_code=400,
            detail="Attendance marking is only available for club/group activities"
        )

    # Check if activity is past
    if activity.date > datetime.now():
        raise HTTPException(status_code=400, detail="Cannot mark attendance for future activities")

    # Check permissions (creator or club/group admin)
    is_organizer = (
        activity.creator_id == current_user.id or
        _is_club_admin(db, current_user.id, activity.club_id) or
        _is_group_admin(db, current_user.id, activity.group_id)
    )
    if not is_organizer:
        raise HTTPException(status_code=403, detail="Only organizers can mark attendance")

    # Update participations
    updated_users = []
    for item in attendance_data:
        participation = db.query(Participation).filter(
            Participation.activity_id == activity_id,
            Participation.user_id == item.user_id
        ).first()

        if participation:
            if item.attended is True:
                participation.status = ParticipationStatus.ATTENDED
                participation.attended = True
            elif item.attended is False:
                participation.status = ParticipationStatus.MISSED
                participation.attended = False
            else:
                participation.status = ParticipationStatus.AWAITING
                participation.attended = None

            updated_users.append({
                'user_id': item.user_id,
                'attended': item.attended
            })

    db.commit()

    # Send notifications
    if notify_participants:
        asyncio.create_task(_send_attendance_notifications(
            activity_id=activity_id,
            activity_title=activity.title,
            activity_date=activity.date,
            updated_users=updated_users
        ))

    return {"message": "Attendance marked successfully", "updated": len(updated_users)}
```

**Также нужен эндпоинт для добавления участника:**
`POST /api/activities/{id}/add-participant`

```python
@router.post("/{activity_id}/add-participant", status_code=201)
async def add_participant(
    activity_id: str,
    user_id: str,
    attended: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add a club/group member as participant (organizers only)
    Used when marking attendance for someone who didn't sign up.
    """
    # ... permission checks same as above ...

    # Create new participation
    participation = Participation(
        activity_id=activity_id,
        user_id=user_id,
        status=ParticipationStatus.ATTENDED if attended else ParticipationStatus.MISSED,
        attended=attended
    )
    db.add(participation)
    db.commit()

    return {"message": "Participant added successfully"}
```

---

## ЧАСТЬ 3: Уведомления в боте

### 3.1 Уведомление после чекина организатором

**Файл:** `bot/activity_notifications.py`

**Добавить новые функции:**

```python
def format_organizer_attendance_notification(
    activity_title: str,
    activity_date: datetime,
    attended: bool,
    organizer_name: str
) -> str:
    """
    Format notification when organizer marks user's attendance.
    """
    date_str = activity_date.strftime("%a, %d %b")

    if attended:
        message = (
            f"✅ Твоё участие подтверждено!\n\n"
            f"\"{activity_title}\"\n"
            f"{date_str}\n\n"
            f"Организатор {organizer_name} отметил твоё присутствие"
        )
    else:
        message = (
            f"ℹ️ Отметка о пропуске\n\n"
            f"\"{activity_title}\"\n"
            f"{date_str}\n\n"
            f"Организатор {organizer_name} отметил, что тебя не было на тренировке"
        )

    return message


async def send_organizer_attendance_notification(
    bot: Bot,
    user_telegram_id: int,
    activity_title: str,
    activity_date: datetime,
    attended: bool,
    organizer_name: str
) -> bool:
    """
    Send notification when organizer marks attendance for a participant.
    """
    try:
        message_text = format_organizer_attendance_notification(
            activity_title=activity_title,
            activity_date=activity_date,
            attended=attended,
            organizer_name=organizer_name
        )

        await bot.send_message(
            chat_id=user_telegram_id,
            text=message_text
        )

        logger.info(f"Sent organizer attendance notification to user {user_telegram_id}")
        return True

    except TelegramError as e:
        logger.error(f"Error sending organizer attendance notification: {e}")
        return False
```

### 3.2 Интеграция уведомлений в API

**Файл:** `app/routers/activities.py`

```python
from bot.activity_notifications import send_organizer_attendance_notification

async def _send_attendance_notifications(
    activity_id: str,
    activity_title: str,
    activity_date: datetime,
    updated_users: List[dict],
    organizer_name: str
):
    """Send notifications to users whose attendance was marked by organizer."""
    try:
        bot = Bot(token=settings.bot_token)

        for user_data in updated_users:
            # Skip if attendance is null (not marked)
            if user_data['attended'] is None:
                continue

            # Get user's telegram_id
            user = db.query(User).filter(User.id == user_data['user_id']).first()
            if not user or not user.telegram_id:
                continue

            await send_organizer_attendance_notification(
                bot=bot,
                user_telegram_id=user.telegram_id,
                activity_title=activity_title,
                activity_date=activity_date,
                attended=user_data['attended'],
                organizer_name=organizer_name
            )

    except Exception as e:
        logger.error(f"Failed to send attendance notifications: {e}")
```

---

## ЧАСТЬ 4: Схема API

### 4.1 Новые схемы

**Файл:** `schemas/activity.py`

```python
class AttendanceItem(BaseModel):
    """Single attendance mark"""
    user_id: str
    attended: Optional[bool] = None  # True = attended, False = missed, None = not marked

class MarkAttendanceRequest(BaseModel):
    """Request to mark attendance for multiple participants"""
    participants: List[AttendanceItem]
    notify: bool = True
```

### 4.2 Обновления в ActivityResponse

```python
class ActivityResponse(BaseResponse):
    # ... existing fields ...

    # Organizer permissions
    is_club_admin: bool = False
    is_group_admin: bool = False
    can_mark_attendance: bool = False  # Computed: is_past && (club_id || group_id) && is_organizer
```

---

## ЧАСТЬ 5: Модели данных (опционально для ссылок)

### 5.1 Если делать ссылки как отдельную таблицу

**Файл:** `storage/db.py`

```python
class Link(Base):
    __tablename__ = "links"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    entity_type = Column(String(10), nullable=False)  # 'club' | 'group'
    entity_id = Column(String, nullable=False)
    type = Column(String(20), nullable=False)  # telegram, strava, instagram, etc.
    label = Column(String(100), nullable=False)
    url = Column(String(500), nullable=False)
    order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('ix_links_entity', 'entity_type', 'entity_id'),
    )
```

### 5.2 Альтернатива: JSON поле

Проще хранить `links` как JSON массив в клубах/группах.

---

## Порядок реализации

### Фаза 1: Критичные исправления (1-2 часа)
1. ✅ Кликабельный родительский клуб в GroupCard
2. ✅ Кликабельный родительский клуб в ClubGroupDetail
3. ✅ Убедиться что `clubId` передаётся в API

### Фаза 2: Чекин организаторов (3-4 часа)
1. Компонент AttendancePopup
2. API эндпоинт mark-attendance
3. API эндпоинт add-participant
4. Интеграция в ActivityDetail
5. Уведомления в боте

### Фаза 3: Дополнительные улучшения UI (2-3 часа)
1. Видимость в подзаголовке (требует изменений API)
2. Виды спорта (требует изменений модели)
3. Ссылки (требует новой модели/таблицы)

---

## Вопросы для уточнения

1. **Ссылки** — делаем сейчас или позже? Требуется новая таблица или JSON поле?

2. **Виды спорта клубов** — добавляем колонку в БД сейчас или откладываем?

3. **Видимость клубов** — сейчас есть только `is_open`. Нужно отдельное поле `visibility`?

4. **Чекин** — при добавлении участника из клуба/группы:
   - Где брать список участников клуба/группы?
   - Показывать всех или только тех, кто не записан?

5. **Уведомления** — отправлять уведомление сразу при каждой отметке или один раз при нажатии "Сохранить"?

---

## Зависимости файлов

### Frontend:
- `webapp/src/screens/ActivityDetail.jsx`
- `webapp/src/screens/ClubGroupDetail.jsx`
- `webapp/src/components/shared/GroupCard.jsx`
- `webapp/src/components/shared/AttendancePopup.jsx` (новый)
- `webapp/src/api.js`
- `webapp/src/hooks/index.js`

### Backend:
- `app/routers/activities.py`
- `schemas/activity.py`
- `bot/activity_notifications.py`
- `storage/db.py` (опционально для ссылок/спорта)
