# Next Steps - Implementation Plan

**Дата создания:** 2025-12-15
**Статус:** Ready to implement
**Приоритет:** High

---

## Контекст

После завершения рефакторинга (Phases 1-5), осталось реализовать:
1. Фикс Pydantic warnings
2. Онбординг через Telegram бота
3. Логика городов (city filtering)
4. Проверка моделей (ручная задача)

---

## Задача 1: Фикс Pydantic Warnings ⚡

**Приоритет:** High (быстро и критично для чистоты)
**Время:** ~15 минут
**Статус:** Ready to implement

### Проблема
В тестах видны warnings:
```
PydanticDeprecatedSince20: Support for class-based `config` is deprecated,
use ConfigDict instead.
```

Затронутые файлы:
- `schemas/common.py:52`
- `schemas/activity.py:6`
- `schemas/club.py:5`

### Решение

**До:**
```python
from pydantic import BaseModel

class BaseResponse(BaseModel):
    class Config:
        from_attributes = True
        arbitrary_types_allowed = True
```

**После:**
```python
from pydantic import BaseModel, ConfigDict

class BaseResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        arbitrary_types_allowed=True
    )
```

### Шаги
1. Обновить `schemas/common.py`
2. Обновить `schemas/activity.py`
3. Обновить `schemas/club.py`
4. Обновить остальные schema файлы если есть
5. Запустить тесты: `pytest tests/ -v`
6. Убедиться что warnings исчезли
7. Коммит: `fix(schemas): migrate to Pydantic v2 ConfigDict`

---

## Задача 2: Онбординг через Telegram Бота 🤖

**Приоритет:** High
**Время:** ~1-2 часа
**Статус:** Requires implementation

### Требования

**User Flow (Вариант A):**

#### Сценарий 1: Новый пользователь (самостоятельный)
1. Пользователь пишет `/start` боту
2. Бот проверяет: есть ли User в БД?
3. Если нет → запускает онбординг в чате
4. Бот спрашивает: "Какими видами спорта интересуешься?"
5. Показывает кнопки (inline keyboard):
   ```
   🏃 Бег        🚴 Велоспорт
   ⛷️ Лыжи       🏊 Плавание
   ⚽ Футбол     🏀 Баскетбол
   ✅ Готово
   ```
6. Пользователь выбирает (можно несколько)
7. Жмет "Готово"
8. Бот сохраняет в `User.preferred_sports` (JSON)
9. Бот устанавливает `User.city = "Almaty"` (hardcoded пока)
10. Бот отправляет: "Отлично! Открывай приложение 👇"
11. Показывает кнопку WebApp: "🏃 Открыть Ayda Run"

#### Сценарий 2: Приглашение в группу/клуб
1. Пользователь получает invite link: `https://t.me/your_bot?start=club_123`
2. Пользователь пишет `/start club_123` боту
3. Бот парсит параметр `club_123`
4. Если User нет → запускает онбординг (шаги 4-9 из Сценария 1)
5. После онбординга → автоматически присоединяет к Club #123
6. Бот отправляет: "Ты присоединился к клубу [Название]! Открывай приложение 👇"
7. Показывает кнопку WebApp

#### Сценарий 3: Существующий пользователь
1. Пользователь пишет `/start`
2. Бот видит что User уже есть
3. Бот отправляет: "С возвращением! 👋"
4. Показывает кнопку WebApp: "🏃 Открыть Ayda Run"

### Технические детали

**Backend изменения:**

1. **Добавить поле в User модель:**
```python
# storage/db.py
class User(Base):
    # ... existing fields
    city = Column(String(100), default="Almaty", nullable=False)  # NEW
    # preferred_sports уже есть
```

2. **Migration:**
```sql
ALTER TABLE users ADD COLUMN city VARCHAR(100) DEFAULT 'Almaty' NOT NULL;
```

3. **Обновить UserResponse schema:**
```python
# schemas/user.py
class UserResponse(BaseModel):
    # ... existing fields
    city: str
```

**Bot изменения:**

1. **Обновить `bot/start_handler.py`:**

```python
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
import json

# Доступные спорты для онбординга
SPORTS_OPTIONS = [
    ("🏃 Бег", "running"),
    ("🚴 Велоспорт", "cycling"),
    ("⛷️ Лыжи", "skiing"),
    ("🏊 Плавание", "swimming"),
    ("⚽ Футбол", "football"),
    ("🏀 Баскетбол", "basketball"),
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command with onboarding flow"""
    user_tg = update.effective_user
    args = context.args  # Get parameters after /start

    # Check if user exists in DB
    from storage.db import get_session, User
    session = get_session()
    user = session.query(User).filter(User.telegram_id == user_tg.id).first()

    # Parse invite parameter (e.g., /start club_123)
    invite_type = None
    invite_id = None
    if args and len(args) > 0:
        param = args[0]
        if param.startswith("club_"):
            invite_type = "club"
            invite_id = int(param.replace("club_", ""))
        elif param.startswith("group_"):
            invite_type = "group"
            invite_id = int(param.replace("group_", ""))

    # Scenario 3: Existing user
    if user and user.has_completed_onboarding:
        await send_webapp_button(update, context,
            text="С возвращением! 👋\n\nОткрывай приложение и погнали на тренировку!")

        # If invite link, auto-join
        if invite_type and invite_id:
            await auto_join_entity(user, invite_type, invite_id, update, context)

        session.close()
        return

    # Scenario 1 & 2: New user - start onboarding
    if not user:
        # Create user in DB
        user = User(
            telegram_id=user_tg.id,
            username=user_tg.username,
            first_name=user_tg.first_name,
            last_name=user_tg.last_name,
            city="Almaty",  # Default city
            has_completed_onboarding=False
        )
        session.add(user)
        session.commit()

    # Store invite info in context for later
    context.user_data['invite_type'] = invite_type
    context.user_data['invite_id'] = invite_id
    context.user_data['selected_sports'] = []

    # Start onboarding - ask for sports
    await ask_sports_preferences(update, context)
    session.close()


async def ask_sports_preferences(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ask user to select preferred sports"""
    keyboard = []

    # Create 2-column layout for sports buttons
    for i in range(0, len(SPORTS_OPTIONS), 2):
        row = []
        row.append(InlineKeyboardButton(
            SPORTS_OPTIONS[i][0],
            callback_data=f"sport_{SPORTS_OPTIONS[i][1]}"
        ))
        if i + 1 < len(SPORTS_OPTIONS):
            row.append(InlineKeyboardButton(
                SPORTS_OPTIONS[i+1][0],
                callback_data=f"sport_{SPORTS_OPTIONS[i+1][1]}"
            ))
        keyboard.append(row)

    # Add "Done" button
    keyboard.append([InlineKeyboardButton("✅ Готово", callback_data="sports_done")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "👋 Привет! Давай настроим твой профиль.\n\n"
        "Какими видами спорта интересуешься? (можно выбрать несколько)",
        reply_markup=reply_markup
    )


async def handle_sport_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle sport selection callbacks"""
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "sports_done":
        # Finish onboarding
        await finish_onboarding(update, context)
        return

    # Toggle sport selection
    if data.startswith("sport_"):
        sport = data.replace("sport_", "")
        selected = context.user_data.get('selected_sports', [])

        if sport in selected:
            selected.remove(sport)
        else:
            selected.append(sport)

        context.user_data['selected_sports'] = selected

        # Update button text to show selection
        keyboard = []
        for i in range(0, len(SPORTS_OPTIONS), 2):
            row = []
            for j in range(2):
                if i + j >= len(SPORTS_OPTIONS):
                    break
                name, value = SPORTS_OPTIONS[i + j]
                # Add checkmark if selected
                if value in selected:
                    name = f"✓ {name}"
                row.append(InlineKeyboardButton(name, callback_data=f"sport_{value}"))
            keyboard.append(row)

        keyboard.append([InlineKeyboardButton(
            f"✅ Готово ({len(selected)} выбрано)",
            callback_data="sports_done"
        )])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_reply_markup(reply_markup=reply_markup)


async def finish_onboarding(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Save onboarding data and show WebApp"""
    query = update.callback_query
    user_tg = update.effective_user

    selected_sports = context.user_data.get('selected_sports', [])
    invite_type = context.user_data.get('invite_type')
    invite_id = context.user_data.get('invite_id')

    # Save to DB
    from storage.db import get_session, User
    session = get_session()
    user = session.query(User).filter(User.telegram_id == user_tg.id).first()

    if user:
        user.preferred_sports = json.dumps(selected_sports)
        user.has_completed_onboarding = True
        session.commit()

    # Delete onboarding message
    await query.message.delete()

    # Send success message
    sports_text = ", ".join([s for s in selected_sports]) if selected_sports else "все виды спорта"
    message = f"🎉 Отлично! Ты выбрал: {sports_text}\n\n"

    # Handle invite
    if invite_type and invite_id:
        await auto_join_entity(user, invite_type, invite_id, update, context)
        if invite_type == "club":
            message += "Ты автоматически присоединился к клубу!\n\n"
        elif invite_type == "group":
            message += "Ты автоматически присоединился к группе!\n\n"

    message += "Открывай приложение и погнали на тренировку! 👇"

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=message
    )

    # Show WebApp button
    await send_webapp_button(update, context)
    session.close()


async def send_webapp_button(update: Update, context: ContextTypes.DEFAULT_TYPE, text=None):
    """Send WebApp button to user"""
    webapp_url = "https://your-domain.com"  # TODO: Replace with actual URL

    keyboard = [[InlineKeyboardButton(
        "🏃 Открыть Ayda Run",
        web_app=WebAppInfo(url=webapp_url)
    )]]

    reply_markup = InlineKeyboardMarkup(keyboard)

    if text is None:
        text = "Открывай приложение:"

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text,
        reply_markup=reply_markup
    )


async def auto_join_entity(user, entity_type, entity_id, update, context):
    """Auto-join user to club or group from invite link"""
    from storage.db import get_session, Club, Group, club_members, group_members

    session = get_session()

    try:
        if entity_type == "club":
            club = session.query(Club).filter(Club.id == entity_id).first()
            if club and user not in club.members:
                club.members.append(user)
                session.commit()
        elif entity_type == "group":
            group = session.query(Group).filter(Group.id == entity_id).first()
            if group and user not in group.members:
                group.members.append(user)
                session.commit()
    except Exception as e:
        print(f"Error auto-joining: {e}")
    finally:
        session.close()


# Register handlers
def setup_handlers(application):
    """Setup all bot handlers"""
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_sport_selection, pattern="^sport_"))
    application.add_handler(CallbackQueryHandler(handle_sport_selection, pattern="^sports_done$"))
```

2. **Обновить `main.py`:**
```python
from bot.start_handler import setup_handlers

# ... existing code

# Setup handlers
setup_handlers(application)

# ... rest of code
```

### Что удалить

1. **Удалить или оставить неактивным:** `webapp/src/screens/Onboarding.jsx`
   - Оставить файл, но не показывать экран (убрать из роутинга)
   - Может пригодиться для редактирования профиля позже

2. **Удалить endpoint?** НЕТ, оставить `/api/users/me/onboarding`
   - Может пригодиться для изменения предпочтений из WebApp

### Тестирование

1. Создать тестового бота в @BotFather
2. Запустить `python main.py`
3. Написать `/start` боту → проверить онбординг
4. Написать `/start club_1` → проверить auto-join
5. Проверить что `User.city = "Almaty"` и `preferred_sports` сохранились

### Коммит
```
feat(bot): implement Telegram bot onboarding flow

- Add /start command with sport selection
- Inline keyboard for choosing sports (running, cycling, skiing, etc.)
- Auto-join to clubs/groups via invite links (/start club_123)
- Set default city to "Almaty"
- WebApp button after onboarding
- Migration: add User.city field

BREAKING CHANGE: Onboarding now happens in Telegram bot, not WebApp
```

---

## Задача 3: Логика городов (City Filtering) 🌆

**Приоритет:** High
**Время:** ~1-1.5 часа
**Статус:** Requires implementation

### Требования

**Логика:**
1. User выбирает город (пока hardcoded "Almaty")
2. Видит только активности/клубы/группы в своем городе
3. **НО:** На экране "Я" (профиль) показываются клубы из других городов, если пользователь в них состоит

**Пример:**
- User.city = "Almaty"
- User состоит в Club #1 (Almaty) и Club #5 (Astana)
- Экран "Активности" → только Almaty
- Экран "Клубы" → только Almaty
- Экран "Я" (Мои клубы) → Almaty + Astana (все где состоит)

### Изменения в моделях

**1. Добавить поле `city` в модели:**

```python
# storage/db.py

class User(Base):
    # ... existing fields
    city = Column(String(100), default="Almaty", nullable=False)

class Activity(Base):
    # ... existing fields
    city = Column(String(100), nullable=False)  # Required!

class Club(Base):
    # ... existing fields
    city = Column(String(100), nullable=False)

class Group(Base):
    # ... existing fields
    city = Column(String(100), nullable=False)
```

**2. Migration (для существующих записей):**
```sql
-- Add city column to users (done in Task 2)
ALTER TABLE users ADD COLUMN city VARCHAR(100) DEFAULT 'Almaty' NOT NULL;

-- Add city column to activities
ALTER TABLE activities ADD COLUMN city VARCHAR(100) DEFAULT 'Almaty' NOT NULL;

-- Add city column to clubs
ALTER TABLE clubs ADD COLUMN city VARCHAR(100) DEFAULT 'Almaty' NOT NULL;

-- Add city column to groups
ALTER TABLE groups ADD COLUMN city VARCHAR(100) DEFAULT 'Almaty' NOT NULL;
```

### Изменения в schemas

**1. Обновить Pydantic schemas:**

```python
# schemas/activity.py
class ActivityCreate(BaseModel):
    title: str
    date: datetime
    sport_type: SportType
    city: str  # NEW - required!
    location: str  # Конкретное место (e.g., "Central Park, near fountain")
    # ... rest

class ActivityResponse(BaseModel):
    # ... existing fields
    city: str
    location: str

# schemas/club.py
class ClubCreate(BaseModel):
    name: str
    city: str  # NEW - required!
    # ... rest

class ClubResponse(BaseModel):
    # ... existing fields
    city: str

# schemas/group.py
class GroupCreate(BaseModel):
    name: str
    city: str  # NEW - required!
    # ... rest

class GroupResponse(BaseModel):
    # ... existing fields
    city: str
```

### Изменения в роутерах

**1. Фильтрация по городу в `app/routers/activities.py`:**

```python
@router.get("/", response_model=List[ActivityResponse])
async def list_activities(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_optional_user)
):
    """List activities in user's city"""
    query = db.query(Activity)

    # Filter by user's city
    if current_user:
        query = query.filter(Activity.city == current_user.city)
    else:
        # For anonymous users, show Almaty by default
        query = query.filter(Activity.city == "Almaty")

    # ... rest of existing logic (filter by date, etc.)

    return activities
```

**2. Фильтрация в `app/routers/clubs.py`:**

```python
@router.get("/", response_model=List[ClubResponse])
async def list_clubs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_optional_user)
):
    """List clubs in user's city"""
    query = db.query(Club)

    # Filter by user's city
    if current_user:
        query = query.filter(Club.city == current_user.city)
    else:
        query = query.filter(Club.city == "Almaty")

    # ... rest

    return clubs
```

**3. Аналогично для groups:**

```python
@router.get("/", response_model=List[GroupResponse])
async def list_groups(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_optional_user)
):
    """List groups in user's city"""
    query = db.query(Group)

    # Filter by user's city
    if current_user:
        query = query.filter(Group.city == current_user.city)
    else:
        query = query.filter(Group.city == "Almaty")

    return groups
```

**4. Добавить endpoint "Мои клубы" (без фильтра по городу):**

```python
# app/routers/clubs.py

@router.get("/me/joined", response_model=List[ClubResponse])
async def get_my_clubs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all clubs user is member of (across all cities)"""
    # No city filter! Show all clubs user joined
    clubs = db.query(Club).join(club_members).filter(
        club_members.c.user_id == current_user.id
    ).all()

    return clubs


# app/routers/groups.py

@router.get("/me/joined", response_model=List[GroupResponse])
async def get_my_groups(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all groups user is member of (across all cities)"""
    groups = db.query(Group).join(group_members).filter(
        group_members.c.user_id == current_user.id
    ).all()

    return groups
```

### Изменения в Frontend

**1. Обновить формы создания:**

```jsx
// webapp/src/screens/ActivityCreate.jsx
// Добавить скрытое поле city (берем из user.city)

const [formData, setFormData] = useState({
    // ... existing fields
    city: user?.city || "Almaty",  // Hidden field, auto-filled
    location: ""  // Visible field for specific location
})
```

**2. Обновить экран "Я" (Profile):**

```jsx
// webapp/src/screens/Profile.jsx (или как он у тебя называется)

// Fetch user's clubs across all cities
const { data: myClubs } = useQuery({
    queryKey: ['clubs', 'me', 'joined'],
    queryFn: () => api.get('/api/clubs/me/joined')
})

// Show clubs grouped by city
<div>
    <h3>Мои клубы</h3>
    {myClubs?.map(club => (
        <ClubCard
            key={club.id}
            club={club}
            showCity={true}  // Show city badge if not current city
        />
    ))}
</div>
```

**3. Показать город в карточках (опционально):**

```jsx
// webapp/src/components/shared/ActivityCard.jsx
// Добавить бейдж города если нужно

{activity.city && (
    <span className="text-xs text-gray-500">📍 {activity.city}</span>
)}
```

### Константы городов

**Создать файл с константами:**

```typescript
// webapp/src/constants/cities.ts

export const CITIES = [
    { value: "Almaty", label: "Алматы" },
    // { value: "Astana", label: "Астана" },  // Commented for future
    // { value: "Shymkent", label: "Шымкент" },
] as const

export type CityValue = typeof CITIES[number]['value']

export const DEFAULT_CITY = "Almaty"
```

```python
# Backend: constants.py (или в config.py)

AVAILABLE_CITIES = ["Almaty"]  # Will expand later
DEFAULT_CITY = "Almaty"
```

### Тестирование

1. Создать активность с city="Almaty"
2. Создать активность с city="Astana" (руками в БД)
3. User.city = "Almaty" → видит только Almaty активности
4. Вступить в клуб Astana (руками в БД)
5. Открыть экран "Я" → видит клубы Almaty + Astana

### Коммит
```
feat(city): add city filtering for activities, clubs, and groups

- Add city field to User, Activity, Club, Group models
- Filter lists by user's current city
- Add /me/joined endpoints to show user's entities across all cities
- Set default city to "Almaty" for MVP
- Migration: add city columns with default "Almaty"

Closes #issue_number
```

---

## Задача 4: Проверка моделей 🔍

**Приоритет:** Medium (ручная задача)
**Время:** ~30-60 минут (ручная проверка)
**Статус:** Manual review needed

### Что проверить

**1. User модель:**
- [ ] `telegram_id` - уникальный ID из Telegram
- [ ] `username` - @username (может быть null)
- [ ] `first_name` - имя пользователя
- [ ] `last_name` - фамилия (может быть null)
- [ ] `city` - город пользователя (добавим в Task 2)
- [ ] `preferred_sports` - JSON массив спортов (есть)
- [ ] `has_completed_onboarding` - флаг завершения онбординга (есть)
- [ ] **TODO:** `avatar_url` - URL аватарки из Telegram?
- [ ] **TODO:** `phone_number` - номер телефона (если нужен для связи)?

**2. Activity модель:**
- [ ] `title` - название активности
- [ ] `date` - дата и время
- [ ] `sport_type` - тип спорта (enum)
- [ ] `city` - город (добавим в Task 3)
- [ ] `location` - конкретное место встречи
- [ ] `description` - описание
- [ ] `difficulty` - сложность
- [ ] `max_participants` - макс участников
- [ ] `creator_id` - создатель (FK to User)
- [ ] `club_id` - клуб (FK to Club, nullable)
- [ ] `group_id` - группа (FK to Group, nullable)
- [ ] **TODO:** `is_paid` - платная ли активность?
- [ ] **TODO:** `price` - цена если платная?
- [ ] **TODO:** `gpx_file` - ссылка на GPX файл маршрута?

**3. Club модель:**
- [ ] `name` - название клуба
- [ ] `city` - город (добавим в Task 3)
- [ ] `description` - описание
- [ ] `visibility` - публичный/приватный
- [ ] `is_paid` - платный клуб?
- [ ] `monthly_price` - цена подписки
- [ ] `admin_id` - админ (FK to User)
- [ ] **TODO:** `logo_url` - логотип клуба?
- [ ] **TODO:** `telegram_chat_id` - связь с Telegram группой?
- [ ] **TODO:** `member_limit` - лимит участников?

**4. Group модель:**
- [ ] `name` - название группы
- [ ] `city` - город (добавим в Task 3)
- [ ] `description` - описание
- [ ] `sport_type` - тип спорта
- [ ] `visibility` - публичный/приватный
- [ ] `club_id` - клуб (FK to Club, nullable)
- [ ] `admin_id` - админ (FK to User)
- [ ] **TODO:** `telegram_chat_id` - связь с Telegram группой?
- [ ] **TODO:** `member_limit` - лимит участников?

**5. Relationships (связи):**
- [ ] User → Activities (created activities)
- [ ] User → Clubs (member of clubs)
- [ ] User → Groups (member of groups)
- [ ] Activity → Participants (many-to-many)
- [ ] Club → Members (many-to-many)
- [ ] Club → Groups (one-to-many)
- [ ] Group → Members (many-to-many)
- [ ] Group → Club (many-to-one, nullable)

**6. Indexes:**
- [ ] User.telegram_id (unique)
- [ ] Activity.creator_id (indexed)
- [ ] Activity.sport_type (indexed)
- [ ] Activity.date (indexed)
- [ ] Activity.city (добавить индекс)
- [ ] Club.city (добавить индекс)
- [ ] Group.city (добавить индекс)

**7. Cascades (что происходит при удалении):**
- [ ] User удален → Activities остаются? (creator_id → null)
- [ ] Club удален → Groups удаляются? (cascade delete)
- [ ] Activity удалена → Participants отвязываются? (cascade delete link)
- [ ] User покинул Club → membership удаляется (работает через association table)

### Аватарка пользователя

**Telegram API предоставляет:**
- `user.photo.small_file_id` - маленькая аватарка
- `user.photo.big_file_id` - большая аватарка

**Варианты реализации:**

**Вариант A (рекомендую):** Хранить file_id в БД
```python
class User(Base):
    # ... existing
    avatar_file_id = Column(String(200), nullable=True)
```

При отображении в WebApp:
```python
# Get file URL from Telegram
photo_url = f"https://api.telegram.org/file/bot{TOKEN}/photos/{file_id}"
```

**Вариант B:** Скачивать и хранить на сервере (не рекомендую, лишняя работа)

**Вариант C:** Запрашивать из Telegram каждый раз (медленно, нужен bot API)

**Решение:** Добавить `avatar_file_id` в User модель, получать при регистрации из Telegram.

### Action Items (для тебя)

1. Открыть `storage/db.py` и проверить каждое поле
2. Открыть Swagger (`http://localhost:8000/docs`) и проверить schemas
3. Попробовать создать Activity/Club/Group через Swagger
4. Проверить что relationships работают (JOIN queries)
5. Список полей которые нужно добавить → записать в отдельный файл
6. Создать GitHub issue или задачу в docs/next_steps/

---

## Приоритизация

### Must Have (сделать завтра):
1. ✅ **Task 1:** Фикс Pydantic warnings (15 мин)
2. ✅ **Task 3:** City filtering (1-1.5 часа)

### Should Have (сделать завтра/послезавтра):
3. ✅ **Task 2:** Telegram bot onboarding (1-2 часа)

### Nice to Have (когда будет время):
4. **Task 4:** Проверка моделей (ручная, потом доделаем)

---

## Итоговый план на завтра

### Сессия 1 (~1.5 часа):
1. Task 1: Фикс Pydantic warnings (15 мин)
2. Task 3: City filtering (1-1.5 часа)
   - Добавить поле city в модели
   - Migration
   - Обновить роутеры с фильтрацией
   - Тесты

### Сессия 2 (~2 часа):
3. Task 2: Telegram bot onboarding (1-2 часа)
   - Обновить bot/start_handler.py
   - Inline keyboard для выбора спортов
   - WebApp button
   - Тесты с реальным ботом

### Проверка:
4. Запустить приложение end-to-end
5. Проверить что city filtering работает
6. Проверить что онбординг работает
7. Пушим все в GitHub

---

## Следующие итерации (после)

1. **Avatar support** - добавить avatar_file_id
2. **City selector** - UI для смены города
3. **Paid activities** - платные активности
4. **GPX routes** - загрузка маршрутов
5. **Telegram chat integration** - связь с группами TG
6. **Member limits** - лимиты участников

---

**Автор:** Claude Sonnet 4.5
**Дата:** 2025-12-15
**Статус:** Ready for implementation 🚀
