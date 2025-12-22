# GPX Routes Implementation Plan

**Дата:** 2025-12-22
**Статус:** Ready for Implementation
**Приоритет:** P1 (Should Have)

---

## 📋 РЕЗЮМЕ

Реализация загрузки GPX файлов для активностей с хранением в приватном Telegram канале (без хранения на сервере).

### Ключевые решения:
- **Хранилище:** Приватный Telegram канал (бот = админ)
- **Доступ:** Через Bot API `getFile` → временная ссылка (работает для приватных каналов)
- **Лимит:** До 20MB (GPX обычно 10KB - 1MB)
- **Интерфейс:** Web приложение (не бот)

---

## 🏗️ АРХИТЕКТУРА

### Схема потока данных

```
┌─────────────────────────────────────────────────────────────────┐
│                         UPLOAD FLOW                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  [Web App]                                                      │
│      │                                                          │
│      │ 1. User selects .gpx file                               │
│      │ 2. POST /api/activities/{id}/gpx (multipart/form-data)  │
│      ▼                                                          │
│  [FastAPI Backend]                                              │
│      │                                                          │
│      │ 3. Validate GPX (extension + XML structure)             │
│      │ 4. bot.send_document(channel_id, file)                  │
│      ▼                                                          │
│  [Telegram GPX Channel]                                         │
│      │                                                          │
│      │ 5. Store message_id + file_id                           │
│      ▼                                                          │
│  [Database]                                                     │
│      gpx_file_id = "AgACAgIAAxkB..."                           │
│      gpx_message_id = 123                                       │
│      gpx_channel_id = -1001234567890                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                        DOWNLOAD FLOW                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  [Web App]                                                      │
│      │                                                          │
│      │ 1. User clicks "Download GPX"                           │
│      │ 2. GET /api/activities/{id}/gpx                         │
│      ▼                                                          │
│  [FastAPI Backend]                                              │
│      │                                                          │
│      │ 3. Check permissions (can_download_gpx)                 │
│      │ 4. bot.get_file(file_id) → file_path                    │
│      │ 5. Fetch file from Telegram                             │
│      │ 6. Return as StreamingResponse                          │
│      ▼                                                          │
│  [User Browser]                                                 │
│      Downloads: route_name.gpx                                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### База данных (уже готово!)

```python
# storage/db.py - Activity model
gpx_file_channel_id = Column(Integer, nullable=True)  # ← уже есть
gpx_file_message_id = Column(Integer, nullable=True)  # ← уже есть

# Добавить:
gpx_file_id = Column(String, nullable=True)           # ← file_id для скачивания
gpx_filename = Column(String, nullable=True)          # ← оригинальное имя файла
```

---

## 📝 ПЛАН РЕАЛИЗАЦИИ

### Phase 1: Настройка инфраструктуры

#### 1.1 Настройка Telegram канала для GPX
- [x] Канал уже создан: https://t.me/aydarun_tracks
- [ ] Убедиться что бот добавлен как администратор с правами на отправку сообщений
- [ ] Добавить `GPX_CHANNEL_ID` в `.env` и `settings.py`

#### 1.2 Обновление схемы БД
```python
# storage/db.py
class Activity(Base):
    # Существующие поля
    gpx_file_channel_id = Column(Integer, nullable=True)
    gpx_file_message_id = Column(Integer, nullable=True)

    # Новые поля
    gpx_file_id = Column(String, nullable=True)      # Telegram file_id
    gpx_filename = Column(String, nullable=True)     # Оригинальное имя файла
```

```bash
# Миграция
alembic revision --autogenerate -m "add gpx file fields"
alembic upgrade head
```

---

### Phase 2: Backend - Upload Endpoint

#### 2.1 GPX Validator Service
```python
# app/services/gpx_service.py

import xml.etree.ElementTree as ET
from fastapi import UploadFile, HTTPException

class GPXService:
    MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB
    ALLOWED_EXTENSIONS = ['.gpx']

    @staticmethod
    async def validate_gpx(file: UploadFile) -> bytes:
        """Validate GPX file and return contents."""

        # 1. Check extension
        if not file.filename.lower().endswith('.gpx'):
            raise HTTPException(400, "Only .gpx files are allowed")

        # 2. Read content
        content = await file.read()

        # 3. Check size
        if len(content) > GPXService.MAX_FILE_SIZE:
            raise HTTPException(400, "File too large. Maximum 20MB")

        # 4. Validate XML structure
        try:
            root = ET.fromstring(content)
            # Check for GPX namespace
            if 'gpx' not in root.tag.lower():
                raise HTTPException(400, "Invalid GPX file structure")
        except ET.ParseError:
            raise HTTPException(400, "Invalid XML format")

        return content

    @staticmethod
    async def upload_to_telegram(
        bot,
        content: bytes,
        filename: str,
        activity_title: str
    ) -> tuple[str, int]:
        """Upload GPX to Telegram channel. Returns (file_id, message_id)."""
        from telegram import InputFile
        from app.core.settings import settings

        # Create caption with activity info
        caption = f"📍 GPX: {activity_title}\n📅 Uploaded: {datetime.now().isoformat()}"

        # Send to channel
        message = await bot.send_document(
            chat_id=settings.gpx_channel_id,
            document=InputFile(content, filename=filename),
            caption=caption
        )

        return message.document.file_id, message.message_id
```

#### 2.2 Upload Endpoint
```python
# app/routers/activities.py

from fastapi import UploadFile, File
from app.services.gpx_service import GPXService

@router.post("/{activity_id}/gpx")
async def upload_gpx(
    activity_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload GPX file for activity."""

    # 1. Get activity
    activity = activity_storage.get_by_id(db, activity_id)
    if not activity:
        raise HTTPException(404, "Activity not found")

    # 2. Check permissions (only creator can upload)
    if activity.creator_id != current_user.id:
        raise HTTPException(403, "Only activity creator can upload GPX")

    # 3. Validate GPX
    content = await GPXService.validate_gpx(file)

    # 4. Upload to Telegram
    from app.core.dependencies import get_bot
    bot = get_bot()

    file_id, message_id = await GPXService.upload_to_telegram(
        bot, content, file.filename, activity.title
    )

    # 5. Update activity
    activity_storage.update_gpx(
        db,
        activity_id,
        gpx_file_id=file_id,
        gpx_message_id=message_id,
        gpx_filename=file.filename
    )

    return {"success": True, "filename": file.filename}
```

---

### Phase 3: Backend - Download Endpoint

#### 3.1 Download Endpoint
```python
# app/routers/activities.py

from fastapi.responses import StreamingResponse
import httpx

@router.get("/{activity_id}/gpx")
async def download_gpx(
    activity_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Download GPX file for activity."""

    # 1. Get activity
    activity = activity_storage.get_by_id(db, activity_id)
    if not activity:
        raise HTTPException(404, "Activity not found")

    # 2. Check if GPX exists
    if not activity.gpx_file_id:
        raise HTTPException(404, "No GPX file for this activity")

    # 3. Check permissions
    can_download = check_gpx_permission(activity, current_user, db)
    if not can_download:
        raise HTTPException(403, "You don't have access to this GPX file")

    # 4. Get file from Telegram
    bot = get_bot()
    file = await bot.get_file(activity.gpx_file_id)

    # 5. Download and stream to user
    async with httpx.AsyncClient() as client:
        response = await client.get(file.file_path)

        return StreamingResponse(
            iter([response.content]),
            media_type="application/gpx+xml",
            headers={
                "Content-Disposition": f'attachment; filename="{activity.gpx_filename}"'
            }
        )


def check_gpx_permission(activity, user, db) -> bool:
    """Check if user can download GPX."""
    # Creator always can
    if activity.creator_id == user.id:
        return True

    # Participants can
    if user.id in [p.id for p in activity.participants]:
        return True

    # For open activities - anyone can
    if activity.is_open:
        return True

    # For club activities - club members can
    if activity.club_id:
        membership = club_storage.get_membership(db, activity.club_id, user.id)
        if membership:
            return True

    return False
```

---

### Phase 4: Frontend - Upload UI

#### 4.1 Обновление API клиента
```javascript
// webapp/src/api.js

export const activitiesApi = {
    // ... existing methods ...

    uploadGpx: async (activityId, file) => {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(`${API_BASE}/activities/${activityId}/gpx`, {
            method: 'POST',
            headers: getAuthHeaders(),  // БЕЗ Content-Type - браузер сам добавит с boundary
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Upload failed');
        }

        return response.json();
    },

    getGpxDownloadUrl: (activityId) => {
        return `${API_BASE}/activities/${activityId}/gpx`;
    }
};
```

#### 4.2 Компонент загрузки GPX
```jsx
// webapp/src/components/GpxUpload.jsx

import { useState, useRef } from 'react';
import { activitiesApi } from '../api';

export function GpxUpload({ activityId, onSuccess }) {
    const [uploading, setUploading] = useState(false);
    const [error, setError] = useState(null);
    const [filename, setFilename] = useState(null);
    const inputRef = useRef();

    const handleFileSelect = async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        // Validate extension
        if (!file.name.toLowerCase().endsWith('.gpx')) {
            setError('Только файлы .gpx');
            return;
        }

        // Validate size (20MB)
        if (file.size > 20 * 1024 * 1024) {
            setError('Файл слишком большой. Максимум 20MB');
            return;
        }

        setUploading(true);
        setError(null);

        try {
            await activitiesApi.uploadGpx(activityId, file);
            setFilename(file.name);
            onSuccess?.();
        } catch (err) {
            setError(err.message);
        } finally {
            setUploading(false);
        }
    };

    return (
        <div className="mb-4">
            <label className="text-sm text-gray-700 mb-2 block">
                Маршрут GPX
            </label>

            <input
                ref={inputRef}
                type="file"
                accept=".gpx"
                onChange={handleFileSelect}
                className="hidden"
            />

            {filename ? (
                <div className="flex items-center gap-2 px-4 py-3 bg-green-50 border border-green-200 rounded-xl">
                    <span className="text-green-600">✓</span>
                    <span className="text-sm text-green-700">{filename}</span>
                    <button
                        onClick={() => {
                            setFilename(null);
                            inputRef.current.value = '';
                        }}
                        className="ml-auto text-gray-400 hover:text-gray-600"
                    >
                        ✕
                    </button>
                </div>
            ) : (
                <button
                    onClick={() => inputRef.current?.click()}
                    disabled={uploading}
                    className="px-4 py-3 border border-dashed border-gray-300 rounded-xl text-sm text-gray-500 hover:border-gray-400 hover:text-gray-600 transition-colors w-full text-left disabled:opacity-50"
                >
                    {uploading ? '⏳ Загрузка...' : '+ Добавить GPX файл'}
                </button>
            )}

            {error && (
                <p className="text-red-500 text-sm mt-1">{error}</p>
            )}
        </div>
    );
}
```

#### 4.3 Интеграция в ActivityCreate (Вариант A: двухшаговый)

**Флоу:**
1. Пользователь создает активность (без GPX)
2. После создания → редирект на ActivityDetail
3. На ActivityDetail показываем кнопку "Добавить GPX" (только для создателя)
4. Создатель загружает GPX

```jsx
// webapp/src/screens/ActivityCreate.jsx
// GPX загрузка НЕ добавляется сюда - остается как есть

// webapp/src/screens/ActivityDetail.jsx
// Добавляем секцию для загрузки GPX (только для создателя)

{isCreator && !activity.gpx_file_id && (
    <GpxUpload
        activityId={activity.id}
        onSuccess={() => refetch()}
    />
)}

{isCreator && activity.gpx_file_id && (
    <div className="flex items-center gap-2 text-sm text-gray-600">
        <span>📍</span>
        <span>{activity.gpx_filename}</span>
        <button onClick={handleDeleteGpx} className="text-red-500 ml-2">
            Удалить
        </button>
    </div>
)}
```

**Преимущества:**
- Проще реализация (GPX опционален)
- Не усложняем форму создания
- Можно добавить GPX позже, после создания

---

### Phase 5: Frontend - Download UI

#### 5.1 Кнопка скачивания в ActivityDetail
```jsx
// webapp/src/screens/ActivityDetail.jsx

{activity.gpx_file_id && activity.can_download_gpx && (
    <a
        href={activitiesApi.getGpxDownloadUrl(activity.id)}
        download
        className="flex items-center gap-2 px-4 py-2 bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 transition-colors"
    >
        <span>📍</span>
        <span>Скачать маршрут GPX</span>
    </a>
)}
```

---

### Phase 6: Schema Updates

#### 6.1 Activity Response Schema
```python
# schemas/activity.py

class ActivityResponse(BaseModel):
    # ... existing fields ...

    gpx_file_id: Optional[str] = None
    gpx_filename: Optional[str] = None
    has_gpx: bool = False  # Computed field
    can_download_gpx: bool = True  # Permission check

    @validator('has_gpx', pre=True, always=True)
    def compute_has_gpx(cls, v, values):
        return bool(values.get('gpx_file_id'))
```

---

## 📁 ФАЙЛЫ ДЛЯ ИЗМЕНЕНИЯ

### Backend:
1. `app/core/settings.py` - добавить `GPX_CHANNEL_ID`
2. `storage/db.py` - добавить поля `gpx_file_id`, `gpx_filename`
3. `storage/activity_storage.py` - метод `update_gpx()`
4. `app/services/gpx_service.py` - **новый файл**
5. `app/routers/activities.py` - endpoints upload/download
6. `schemas/activity.py` - обновить схемы

### Frontend:
7. `webapp/src/api.js` - методы для GPX
8. `webapp/src/components/GpxUpload.jsx` - **новый файл**
9. `webapp/src/screens/ActivityCreate.jsx` - удалить placeholder (GPX загружается на ActivityDetail)
10. `webapp/src/screens/ActivityDetail.jsx` - загрузка GPX (для создателя) + кнопка скачивания (для всех)

### Config:
11. `.env` - добавить `GPX_CHANNEL_ID`

---

## ⏱️ ОЦЕНКА ВРЕМЕНИ

| Phase | Описание | Время |
|-------|----------|-------|
| 1 | Инфраструктура (канал, БД) | 30 мин |
| 2 | Backend Upload | 45 мин |
| 3 | Backend Download | 30 мин |
| 4 | Frontend Upload | 45 мин |
| 5 | Frontend Download | 15 мин |
| 6 | Schema Updates | 15 мин |
| - | Тестирование | 30 мин |

**Итого:** ~3-3.5 часа

---

## 🧪 ТЕСТИРОВАНИЕ

### Unit Tests
```python
# tests/test_gpx_service.py

async def test_validate_gpx_valid_file():
    """Valid GPX file passes validation."""

async def test_validate_gpx_invalid_extension():
    """Non-GPX file is rejected."""

async def test_validate_gpx_invalid_xml():
    """Invalid XML is rejected."""

async def test_validate_gpx_too_large():
    """File over 20MB is rejected."""
```

### Integration Tests
```python
# tests/test_gpx_endpoints.py

async def test_upload_gpx_as_creator():
    """Creator can upload GPX."""

async def test_upload_gpx_as_non_creator():
    """Non-creator cannot upload GPX."""

async def test_download_gpx_as_participant():
    """Participant can download GPX."""

async def test_download_gpx_no_permission():
    """Non-member of closed activity cannot download."""
```

### Manual Testing Checklist
- [ ] Загрузка валидного GPX файла
- [ ] Отклонение файла с неправильным расширением
- [ ] Отклонение слишком большого файла
- [ ] Отклонение невалидного XML
- [ ] Скачивание GPX создателем активности
- [ ] Скачивание GPX участником
- [ ] Блокировка скачивания для закрытой активности
- [ ] Отображение кнопки скачивания в UI

---

## 🔒 БЕЗОПАСНОСТЬ

1. **Валидация файлов:**
   - Проверка расширения `.gpx`
   - Парсинг XML для проверки структуры
   - Лимит размера 20MB

2. **Права доступа:**
   - Только создатель может загружать GPX
   - Скачивание контролируется через `can_download_gpx`
   - Закрытые активности требуют членства

3. **Telegram канал:**
   - Приватный канал (нет прямого доступа)
   - Файлы доступны только через Bot API

---

## 🚀 БУДУЩИЕ УЛУЧШЕНИЯ (Out of Scope)

- [ ] Превью маршрута на карте (Leaflet + GPX parsing)
- [ ] Публичный канал с красивым отображением маршрутов
- [ ] Поиск маршрутов по региону/сложности
- [ ] Статистика маршрута (дистанция, набор высоты)
- [ ] Загрузка нескольких GPX файлов
- [ ] Конвертация из других форматов (KML, TCX)

---

**Last Updated:** 2025-12-22
**Author:** Claude Opus 4.5
**Status:** Ready for Implementation
