# План: Синхронизация онбординга с новыми изменениями

**Дата:** 2024-12-24
**Статус:** ✅ Выполнено

## Цели

1. ✅ Синхронизировать ID видов спорта между ботом и API
2. ✅ Добавить выбор видимости аватарки в онбординг пользователя
3. ✅ Добавить выбор доступности клуба в онбординг организатора
4. ✅ Добавить выбор доступности в `/create_club`
5. ✅ Перенести web-онбординг в legacy
6. ✅ Добавить валидацию Strava ссылок

---

## Фаза 0: Исправить рассинхронизацию спортов ✅

### Проблема
ID спортов в боте не совпадали с API:
- Бот: `RUNNING`, `TRAIL_RUNNING`, `HIKING`, `CYCLING`
- API: `RUNNING`, `TRAIL`, `HIKING`, `CYCLING`, `OTHER`

### Выполнено
- [x] Изменён `TRAIL_RUNNING` → `TRAIL` в `bot/keyboards.py`
- [x] Добавлен `OTHER` ("Другое") в список спортов

---

## Фаза 1: Онбординг пользователя — добавить `show_photo` ✅

### Новый flow
```
/start → Consent → Photo Visibility → Sports → Role → Strava → Intro → Done
```

### Выполнено
- [x] Добавлен state `ASKING_PHOTO_VISIBILITY = 6`
- [x] Добавлена функция `get_photo_visibility_keyboard()`
- [x] Добавлено сообщение `get_photo_visibility_message()`
- [x] Добавлен handler `handle_photo_visibility()`
- [x] Изменён `handle_consent()` — после consent переходит к photo visibility
- [x] Сохраняется `show_photo` через `user_storage.update_profile()`
- [x] Обновлён `onboarding_conv_handler`

---

## Фаза 2: Онбординг организатора — добавить `is_open` ✅

### Новый flow
```
Role=Organizer → Type → Name → Description → Sports → Members → Groups → Telegram → Contact → Access → Confirm
```

### Выполнено

#### 2.1 Миграция БД
- [x] Создана миграция: `0589ae247848_add_is_open_to_club_requests.py`
- [x] Добавлено поле `is_open` в модель `ClubRequest`

#### 2.2 Бот
- [x] Добавлен state `CLUB_ACCESS = 19`
- [x] Добавлена функция `get_club_access_keyboard()`
- [x] Добавлено сообщение `get_club_access_prompt()`
- [x] Добавлен handler `handle_club_access_choice()`
- [x] Изменены `handle_club_contact_choice/phone` — после contact переходят к access
- [x] Обновлён `format_club_confirmation_message()` — показывает выбор доступности
- [x] Обновлён `organizer_conv_handler`

#### 2.3 Storage
- [x] Обновлён `ClubStorage.create_club_request()` — принимает `is_open`

---

## Фаза 3: `/create_club` — добавить `is_open` ✅

### Новый flow
```
/create_club → Checks → Preview → Confirm → Sports → Access → Create
```

### Выполнено
- [x] Добавлен state `SELECTING_ACCESS = 3`
- [x] Добавлен handler `handle_access_selection()`
- [x] После выбора спортов → переход к выбору доступности
- [x] Передаётся `is_open` в `create_club_from_telegram_group()`
- [x] Обновлён `ClubStorage.create_club_from_telegram_group()` — принимает `is_open`

---

## Фаза 4: Web-онбординг → legacy ✅

### Выполнено
- [x] Переименован `Onboarding.jsx` → `Onboarding_legacy.jsx`
- [x] Убран import и route из `App.jsx`
- [x] Убрана проверка `checkOnboarding()`

---

## Фаза 5: Валидация Strava ссылок ✅

### Выполнено
- [x] Добавлена функция `validate_strava_link()` в `bot/validators.py`
- [x] Применена в `handle_strava_link()` в `onboarding_handler.py`
- [x] При невалидной ссылке — сообщение с примером формата

---

## Изменённые файлы

### Бот
- `bot/keyboards.py` — новые клавиатуры
- `bot/messages.py` — новые сообщения
- `bot/validators.py` — валидация Strava
- `bot/onboarding_handler.py` — photo visibility + Strava валидация
- `bot/organizer_handler.py` — is_open для заявок
- `bot/group_club_creation_handler.py` — is_open для /create_club

### Storage
- `storage/db.py` — поле is_open в ClubRequest
- `storage/club_storage.py` — передача is_open

### База данных
- `alembic/versions/0589ae247848_add_is_open_to_club_requests.py`

### Webapp
- `webapp/src/App.jsx` — убран onboarding
- `webapp/src/screens/Onboarding_legacy.jsx` — переименован
