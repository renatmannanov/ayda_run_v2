# Plan: Обновление экрана профиля

## Обзор

Переработка экрана профиля согласно референсам `ayda-run-profile.jsx` и `ayda-run-profile-changelog.md`:
- Новый дизайн профиля с большим аватаром
- Strava ссылка (ручной ввод)
- Клубы и группы в горизонтальном скролле
- Отдельный экран статистики с табами периодов
- Отдельный экран настроек с toggle фото и Strava

## Текущее состояние

**Что есть:**
- Профиль с центрированным аватаром и именем
- Клубы и группы в 2 колонки (grid)
- Статистика в модальном окне (базовая)
- API `GET /users/me` (есть)
- API `PATCH /users/me` (есть, photo и strava_link)

**Что нужно:**
- Новый layout профиля (аватар слева, инфо справа)
- Strava ссылка в хедере профиля
- Клубы/группы в горизонтальном скролле с аватарками
- Статистика - отдельный экран с периодами
- Настройки - отдельный экран
- API `GET /users/me/stats?period=month` (новый endpoint)
- Глобальная настройка `showPhoto` (влияет на аватарки везде)

---

## UI Design

### Профиль (главный экран)

```
┌─────────────────────────────────────────┐
│ Профиль                                 │
├─────────────────────────────────────────┤
│ ┌──────┐  Renat Mannanov                │
│ │ [RM] │  @ray_mann                     │
│ │ 80px │  🏃 🚴                          │
│ └──────┘  [S] strava.com/athletes/... → │
├─────────────────────────────────────────┤
│ Клубы и группы (4)                      │
│ [🏆] [CR] [ГБ] [TN]  ← горизонт. скролл │
│  SRG  Club Горн Trail                   │
├─────────────────────────────────────────┤
│ 📊 Статистика              83%       →  │
│ ⚙️ Настройки                         →  │
└─────────────────────────────────────────┘
```

### Статистика (отдельный экран)

```
┌─────────────────────────────────────────┐
│ ← Статистика                            │
├─────────────────────────────────────────┤
│ [ Месяц ] [ Квартал ] [ Год ] [ Всё ]   │
├─────────────────────────────────────────┤
│ Записался / Участвовал                  │
│ 10 / 12                           83%   │
│ ████████████░░░░                        │
├─────────────────────────────────────────┤
│ По клубам и группам                     │
│ [🏆] SRG Almaty           5/6           │
│      ████████████░░                     │
│ [CR] Club Runners         4/4           │
│      ████████████████                   │
├─────────────────────────────────────────┤
│ По видам спорта                         │
│ 🏃 Бег                      7           │
│    ████████████████                     │
│ ⛰️ Трейл                    2           │
│    ████                                 │
└─────────────────────────────────────────┘
```

### Настройки (отдельный экран)

```
┌─────────────────────────────────────────┐
│ ← Настройки                             │
├─────────────────────────────────────────┤
│ Показывать фото            [●     ]     │
│ Вместо инициалов в аватарке             │
├─────────────────────────────────────────┤
│ Strava                                  │
│ [S] strava.com/athletes/...   Отвязать  │
│                                         │
│ --- ИЛИ если нет ---                    │
│                                         │
│ [ Добавить ссылку на Strava ]           │
└─────────────────────────────────────────┘
```

---

## Изменения Backend

### 1. Новый endpoint: GET /users/me/stats

**Файл:** `app/routers/users.py`

```python
from schemas.user import UserStatsResponse, UserDetailedStatsResponse

@router.get("/me/stats", response_model=UserDetailedStatsResponse)
def get_user_stats(
    period: str = Query("month", description="Period: month, quarter, year, all"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> UserDetailedStatsResponse:
    """
    Get detailed user statistics for period.
    """
    user_storage = UserStorage(session=db)
    stats = user_storage.get_detailed_stats(
        user_id=current_user.id,
        period=period
    )
    return stats
```

### 2. Новая схема ответа

**Файл:** `schemas/user.py`

```python
class ClubStats(BaseModel):
    """Statistics per club/group"""
    id: str
    name: str
    avatar: Optional[str] = None  # emoji или file_id
    initials: Optional[str] = None
    type: str  # 'club' или 'group'
    registered: int
    attended: int

class SportStats(BaseModel):
    """Statistics per sport type"""
    id: str  # 'running', 'trail', etc.
    icon: str  # emoji
    name: str  # 'Бег', 'Трейл', etc.
    count: int

class UserDetailedStatsResponse(BaseModel):
    """Detailed user statistics response"""
    period: str  # 'month', 'quarter', 'year', 'all'
    registered: int  # Total registered activities
    attended: int  # Total attended activities
    attendance_rate: int  # Percentage
    clubs: List[ClubStats]  # Stats by club/group
    sports: List[SportStats]  # Stats by sport type
```

### 3. Метод статистики в storage

**Файл:** `storage/user_storage.py`

```python
def get_detailed_stats(self, user_id: str, period: str = "month") -> dict:
    """
    Get detailed statistics for user.

    Args:
        user_id: User UUID
        period: 'month', 'quarter', 'year', 'all'

    Returns:
        Dict with registered, attended, clubs stats, sports stats
    """
    # Calculate date range based on period
    now = datetime.utcnow()
    if period == "month":
        start_date = now - timedelta(days=30)
    elif period == "quarter":
        start_date = now - timedelta(days=90)
    elif period == "year":
        start_date = now - timedelta(days=365)
    else:  # all
        start_date = None

    # Query participations with activities
    query = self.session.query(Participation).join(Activity).filter(
        Participation.user_id == user_id
    )

    if start_date:
        query = query.filter(Activity.date >= start_date)

    participations = query.all()

    # Aggregate stats...
    # (подробная логика агрегации)
```

### 4. Новое поле в User модели

**Файл:** `storage/db.py`

Добавить поле `show_photo`:

```python
class User(Base):
    # ... existing fields ...
    show_photo = Column(Boolean, default=True, nullable=False)
```

**Файл:** `schemas/user.py`

Добавить в UserResponse:
```python
show_photo: bool = True
```

Добавить в UserProfileUpdate:
```python
show_photo: Optional[bool] = None
```

### 5. Обновить update_profile

**Файл:** `storage/user_storage.py`

```python
def update_profile(self, user_id: str, photo: Optional[str] = None,
                  strava_link: Optional[str] = None,
                  show_photo: Optional[bool] = None) -> Optional[User]:
    # ... existing logic ...
    if show_photo is not None:
        user.show_photo = show_photo
```

---

## Изменения Frontend

### 1. Обновить transformUser в api.js

**Файл:** `webapp/src/api.js`

```javascript
const transformUser = (u) => !u ? null : ({
    id: u.id,
    telegramId: u.telegram_id,
    username: u.username,
    firstName: u.first_name,
    lastName: u.last_name,
    country: u.country,
    city: u.city,
    createdAt: u.created_at,
    preferredSports: u.preferred_sports,
    photo: u.photo,
    stravaLink: u.strava_link,  // ADD
    showPhoto: u.show_photo !== false,  // ADD (default true)
})
```

### 2. Обновить usersApi

**Файл:** `webapp/src/api.js`

```javascript
export const usersApi = {
    getMe: () => apiFetch('/users/me').then(transformUser),

    getStats: (period = 'month') =>
        apiFetch(`/users/me/stats?period=${period}`),

    updateProfile: (data) => apiFetch('/users/me', {
        method: 'PATCH',
        body: JSON.stringify({
            photo: data.photo,
            strava_link: data.stravaLink,
            show_photo: data.showPhoto,
        })
    }).then(transformUser),
}
```

### 3. Глобальный контекст для showPhoto

**Файл:** `webapp/src/contexts/UserContext.jsx` (NEW)

```jsx
import React, { createContext, useContext, useState, useEffect } from 'react'
import { usersApi } from '../api'
import { useApi } from '../hooks'

const UserContext = createContext()

export function UserProvider({ children }) {
    const { data: userProfile, refetch } = useApi(usersApi.getMe)
    const [showPhoto, setShowPhoto] = useState(true)

    useEffect(() => {
        if (userProfile) {
            setShowPhoto(userProfile.showPhoto !== false)
        }
    }, [userProfile])

    const updateShowPhoto = async (value) => {
        setShowPhoto(value)
        await usersApi.updateProfile({ showPhoto: value })
        refetch()
    }

    return (
        <UserContext.Provider value={{
            user: userProfile,
            showPhoto,
            updateShowPhoto,
            refetch
        }}>
            {children}
        </UserContext.Provider>
    )
}

export const useUser = () => useContext(UserContext)
```

### 4. Обновить Avatar компонент

**Файл:** `webapp/src/components/ui/Avatar.jsx`

```jsx
import { useUser } from '../../contexts/UserContext'

export default function Avatar({ src, name, size = 'md', className = '', forceShowPhoto = false }) {
    const { showPhoto: globalShowPhoto } = useUser() || { showPhoto: true }
    const [imageError, setImageError] = React.useState(false)

    // Если глобально выключено показывать фото - показываем инициалы
    // Но можно форсировать показ фото для определённых мест
    const shouldShowImage = forceShowPhoto || globalShowPhoto

    const showImage = src && shouldShowImage && !imageError

    // ... rest of component
}
```

### 5. Создать компонент StravaLink

**Файл:** `webapp/src/components/profile/StravaLink.jsx` (NEW)

```jsx
export default function StravaLink({ url, onAdd }) {
    if (url) {
        // Показываем ссылку
        return (
            <a
                href={url.startsWith('http') ? url : `https://${url}`}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 text-sm text-gray-500 hover:text-orange-500"
            >
                <span className="w-5 h-5 rounded bg-orange-500 text-white text-xs font-bold flex items-center justify-center">S</span>
                <span className="truncate max-w-[180px]">{url.replace(/^https?:\/\//, '')}</span>
                <svg className="w-4 h-4" ...>
                    {/* External link icon */}
                </svg>
            </a>
        )
    }

    // Кнопка добавить
    return (
        <button
            onClick={onAdd}
            className="flex items-center gap-2 text-sm text-orange-500 hover:text-orange-600"
        >
            <span className="w-5 h-5 rounded bg-orange-100 text-orange-500 text-xs font-bold flex items-center justify-center">S</span>
            <span>Добавить Strava</span>
        </button>
    )
}
```

### 6. Создать компонент ClubGroupCard (для профиля)

**Файл:** `webapp/src/components/profile/ClubGroupCard.jsx` (NEW)

```jsx
import { Avatar } from '../ui'

export default function ClubGroupCard({ item, onClick }) {
    const isClub = item.type === 'club' || !item.groupId

    return (
        <button
            onClick={onClick}
            className="flex flex-col items-center gap-1 min-w-[64px]"
        >
            <Avatar
                src={item.photo}
                name={item.name}
                size="lg"  // 48px
            />
            <span className="text-xs text-gray-600 max-w-[64px] truncate">
                {item.name}
            </span>
        </button>
    )
}
```

### 7. Создать компонент ProgressBar

**Файл:** `webapp/src/components/ui/ProgressBar.jsx` (NEW)

```jsx
export default function ProgressBar({ value, max, showPercent = true }) {
    const percent = max > 0 ? Math.round((value / max) * 100) : 0

    return (
        <div className="flex items-center gap-3">
            <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
                <div
                    className="h-full bg-gray-300 rounded-full transition-all duration-300"
                    style={{ width: `${percent}%` }}
                />
            </div>
            {showPercent && (
                <span className="text-sm text-gray-400 w-12 text-right">{percent}%</span>
            )}
        </div>
    )
}
```

### 8. Создать экран Statistics

**Файл:** `webapp/src/screens/Statistics.jsx` (NEW)

```jsx
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { usersApi } from '../api'
import { useApi } from '../hooks'
import { Avatar, ProgressBar } from '../components/ui'
import { SPORT_TYPES } from '../constants/sports'

const PERIODS = [
    { id: 'month', label: 'Месяц' },
    { id: 'quarter', label: 'Квартал' },
    { id: 'year', label: 'Год' },
    { id: 'all', label: 'Всё время' },
]

export default function Statistics() {
    const navigate = useNavigate()
    const [period, setPeriod] = useState('month')

    const { data: stats, isLoading } = useApi(
        () => usersApi.getStats(period),
        [period]
    )

    if (isLoading) return <LoadingScreen />

    const totalSports = stats?.sports?.reduce((sum, s) => sum + s.count, 0) || 0

    return (
        <div className="h-screen bg-gray-50 flex flex-col">
            {/* Header */}
            <div className="bg-white border-b border-gray-200 px-4 py-3 flex items-center gap-3">
                <button onClick={() => navigate(-1)} className="text-gray-500">
                    <ChevronLeftIcon />
                </button>
                <h1 className="text-base font-medium text-gray-800">Статистика</h1>
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {/* Period Tabs */}
                <div className="bg-white rounded-2xl p-4">
                    <div className="flex gap-1 p-1 bg-gray-100 rounded-lg">
                        {PERIODS.map(p => (
                            <button
                                key={p.id}
                                onClick={() => setPeriod(p.id)}
                                className={`flex-1 py-1.5 px-2 text-xs font-medium rounded-md transition-colors ${
                                    period === p.id
                                        ? 'bg-white text-gray-800 shadow-sm'
                                        : 'text-gray-500'
                                }`}
                            >
                                {p.label}
                            </button>
                        ))}
                    </div>
                </div>

                {/* Registered / Attended */}
                <div className="bg-white rounded-2xl p-4">
                    <h3 className="text-sm font-medium text-gray-800 mb-3">
                        Записался / Участвовал
                    </h3>
                    <div className="flex items-baseline justify-between mb-2">
                        <span className="text-2xl font-medium text-gray-800">
                            {stats?.attended || 0}
                            <span className="text-gray-300"> / </span>
                            {stats?.registered || 0}
                        </span>
                        <span className="text-sm text-gray-400">
                            {stats?.attendanceRate || 0}%
                        </span>
                    </div>
                    <ProgressBar
                        value={stats?.attended || 0}
                        max={stats?.registered || 1}
                        showPercent={false}
                    />
                </div>

                {/* By Clubs & Groups */}
                {stats?.clubs?.length > 0 && (
                    <div className="bg-white rounded-2xl p-4">
                        <h3 className="text-sm font-medium text-gray-800 mb-3">
                            По клубам и группам
                        </h3>
                        <div className="space-y-3">
                            {stats.clubs.map((club) => (
                                <div key={club.id} className="flex items-center gap-3">
                                    <Avatar
                                        src={club.avatar}
                                        name={club.name}
                                        size="sm"
                                    />
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-baseline justify-between mb-1">
                                            <span className="text-sm text-gray-700 truncate">
                                                {club.name}
                                            </span>
                                            <span className="text-xs text-gray-400 ml-2">
                                                {club.attended}/{club.registered}
                                            </span>
                                        </div>
                                        <ProgressBar
                                            value={club.attended}
                                            max={club.registered}
                                            showPercent={false}
                                        />
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* By Sports */}
                {stats?.sports?.length > 0 && (
                    <div className="bg-white rounded-2xl p-4">
                        <h3 className="text-sm font-medium text-gray-800 mb-3">
                            По видам спорта
                        </h3>
                        <div className="space-y-3">
                            {stats.sports.map((sport) => (
                                <div key={sport.id}>
                                    <div className="flex items-center justify-between mb-1">
                                        <span className="text-sm text-gray-700">
                                            {sport.icon} {sport.name}
                                        </span>
                                        <span className="text-xs text-gray-400">
                                            {sport.count}
                                        </span>
                                    </div>
                                    <ProgressBar
                                        value={sport.count}
                                        max={totalSports}
                                        showPercent={false}
                                    />
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </div>
    )
}
```

### 9. Создать экран Settings

**Файл:** `webapp/src/screens/Settings.jsx` (NEW)

```jsx
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useUser } from '../contexts/UserContext'
import { usersApi } from '../api'

export default function Settings() {
    const navigate = useNavigate()
    const { user, showPhoto, updateShowPhoto, refetch } = useUser()

    const [stravaInput, setStravaInput] = useState('')
    const [showStravaInput, setShowStravaInput] = useState(false)
    const [saving, setSaving] = useState(false)

    const handleTogglePhoto = async () => {
        await updateShowPhoto(!showPhoto)
    }

    const handleAddStrava = async () => {
        if (!stravaInput.trim()) return
        setSaving(true)
        try {
            await usersApi.updateProfile({ stravaLink: stravaInput })
            refetch()
            setShowStravaInput(false)
            setStravaInput('')
        } finally {
            setSaving(false)
        }
    }

    const handleRemoveStrava = async () => {
        setSaving(true)
        try {
            await usersApi.updateProfile({ stravaLink: '' })
            refetch()
        } finally {
            setSaving(false)
        }
    }

    return (
        <div className="h-screen bg-gray-50 flex flex-col">
            {/* Header */}
            <div className="bg-white border-b border-gray-200 px-4 py-3 flex items-center gap-3">
                <button onClick={() => navigate(-1)} className="text-gray-500">
                    <ChevronLeftIcon />
                </button>
                <h1 className="text-base font-medium text-gray-800">Настройки</h1>
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {/* Photo Toggle */}
                <div className="bg-white rounded-2xl p-4">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm font-medium text-gray-800">
                                Показывать фото
                            </p>
                            <p className="text-xs text-gray-400 mt-0.5">
                                Вместо инициалов в аватарке
                            </p>
                        </div>
                        <button
                            onClick={handleTogglePhoto}
                            className={`w-12 h-7 rounded-full transition-colors ${
                                showPhoto ? 'bg-gray-800' : 'bg-gray-200'
                            }`}
                        >
                            <div className={`w-5 h-5 rounded-full bg-white shadow-sm transition-transform mx-1 ${
                                showPhoto ? 'translate-x-5' : 'translate-x-0'
                            }`} />
                        </button>
                    </div>
                </div>

                {/* Strava */}
                <div className="bg-white rounded-2xl p-4">
                    <h3 className="text-sm font-medium text-gray-800 mb-3">Strava</h3>

                    {user?.stravaLink ? (
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                                <span className="w-6 h-6 rounded bg-orange-500 text-white text-xs font-bold flex items-center justify-center">
                                    S
                                </span>
                                <span className="text-sm text-gray-600 truncate max-w-[180px]">
                                    {user.stravaLink.replace(/^https?:\/\//, '')}
                                </span>
                            </div>
                            <button
                                onClick={handleRemoveStrava}
                                disabled={saving}
                                className="text-xs text-red-500 hover:text-red-600"
                            >
                                Отвязать
                            </button>
                        </div>
                    ) : showStravaInput ? (
                        <div className="space-y-3">
                            <input
                                type="text"
                                value={stravaInput}
                                onChange={(e) => setStravaInput(e.target.value)}
                                placeholder="strava.com/athletes/..."
                                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm"
                            />
                            <div className="flex gap-2">
                                <button
                                    onClick={() => setShowStravaInput(false)}
                                    className="flex-1 py-2 text-sm text-gray-600"
                                >
                                    Отмена
                                </button>
                                <button
                                    onClick={handleAddStrava}
                                    disabled={saving || !stravaInput.trim()}
                                    className="flex-1 py-2 bg-orange-500 text-white rounded-lg text-sm font-medium disabled:opacity-50"
                                >
                                    Сохранить
                                </button>
                            </div>
                        </div>
                    ) : (
                        <button
                            onClick={() => setShowStravaInput(true)}
                            className="w-full py-3 bg-orange-500 text-white rounded-xl text-sm font-medium flex items-center justify-center gap-2"
                        >
                            <span className="font-bold">S</span>
                            <span>Добавить ссылку на Strava</span>
                        </button>
                    )}
                </div>
            </div>
        </div>
    )
}
```

### 10. Обновить Profile.jsx

**Файл:** `webapp/src/screens/Profile.jsx`

Основные изменения:
- Новый layout хедера (аватар слева)
- Strava ссылка под sports
- Клубы+группы объединены в горизонтальный скролл
- Ссылки на /statistics и /settings вместо модалки
- Убрать StatsModal

### 11. Обновить роутинг

**Файл:** `webapp/src/App.jsx`

```jsx
import Statistics from './screens/Statistics'
import Settings from './screens/Settings'

// ...
<Route path="/statistics" element={<Statistics />} />
<Route path="/settings" element={<Settings />} />
```

### 12. Добавить UserProvider

**Файл:** `webapp/src/App.jsx`

```jsx
import { UserProvider } from './contexts/UserContext'

function App() {
    return (
        <UserProvider>
            <Router>
                {/* ... */}
            </Router>
        </UserProvider>
    )
}
```

---

## Порядок реализации

### Этап 1: Backend

1. **DB: Добавить поле show_photo в User**
   - `storage/db.py` - добавить Column
   - Миграция Alembic

2. **Schema: Обновить UserResponse и UserProfileUpdate**
   - `schemas/user.py` - добавить show_photo
   - Добавить схемы для detailed stats

3. **Storage: Обновить update_profile**
   - `storage/user_storage.py` - добавить show_photo
   - Добавить метод get_detailed_stats

4. **API: Обновить PATCH /users/me**
   - `app/routers/users.py` - поддержка show_photo

5. **API: Создать GET /users/me/stats**
   - `app/routers/users.py` - новый endpoint

### Этап 2: Frontend - Основа

6. **API: Обновить transformUser и usersApi**
   - `webapp/src/api.js`

7. **Context: Создать UserContext**
   - `webapp/src/contexts/UserContext.jsx`

8. **App: Добавить UserProvider и роуты**
   - `webapp/src/App.jsx`

### Этап 3: Frontend - Компоненты

9. **UI: Создать ProgressBar**
   - `webapp/src/components/ui/ProgressBar.jsx`

10. **Profile: Создать StravaLink**
    - `webapp/src/components/profile/StravaLink.jsx`

11. **Profile: Создать ClubGroupCard**
    - `webapp/src/components/profile/ClubGroupCard.jsx`

12. **Avatar: Обновить для showPhoto**
    - `webapp/src/components/ui/Avatar.jsx`

### Этап 4: Frontend - Экраны

13. **Screen: Создать Statistics**
    - `webapp/src/screens/Statistics.jsx`

14. **Screen: Создать Settings**
    - `webapp/src/screens/Settings.jsx`

15. **Screen: Обновить Profile**
    - `webapp/src/screens/Profile.jsx`

### Этап 5: Тестирование

16. **Тест: Backend endpoints**
17. **Тест: Frontend навигация**
18. **Тест: showPhoto toggle**

---

## Файлы для изменения

| Файл | Изменение |
|------|-----------|
| `storage/db.py` | Добавить show_photo в User |
| `schemas/user.py` | Добавить show_photo, ClubStats, SportStats, UserDetailedStatsResponse |
| `storage/user_storage.py` | Добавить show_photo в update_profile, добавить get_detailed_stats |
| `app/routers/users.py` | Обновить PATCH, добавить GET /me/stats |
| `webapp/src/api.js` | Обновить transformUser, usersApi |
| `webapp/src/contexts/UserContext.jsx` | NEW - глобальный контекст юзера |
| `webapp/src/components/ui/Avatar.jsx` | Добавить поддержку showPhoto |
| `webapp/src/components/ui/ProgressBar.jsx` | NEW - прогресс бар |
| `webapp/src/components/ui/index.js` | Экспорт ProgressBar |
| `webapp/src/components/profile/StravaLink.jsx` | NEW |
| `webapp/src/components/profile/ClubGroupCard.jsx` | NEW |
| `webapp/src/screens/Statistics.jsx` | NEW |
| `webapp/src/screens/Settings.jsx` | NEW |
| `webapp/src/screens/Profile.jsx` | Полная переработка |
| `webapp/src/App.jsx` | Добавить UserProvider, роуты |

---

## Отложено на будущее

- **Strava OAuth** - полноценная интеграция (сейчас только ссылка)
- **"Часто тренируюсь с"** - секция training partners в статистике
- **Редактирование видов спорта** - отдельный экран выбора спорта

---

## Чеклист

### Backend
- [ ] Добавить show_photo в User модель
- [ ] Создать миграцию Alembic
- [ ] Обновить UserResponse схему
- [ ] Обновить UserProfileUpdate схему
- [ ] Создать ClubStats, SportStats, UserDetailedStatsResponse схемы
- [ ] Обновить update_profile в storage
- [ ] Создать get_detailed_stats в storage
- [ ] Обновить PATCH /users/me endpoint
- [ ] Создать GET /users/me/stats endpoint

### Frontend
- [ ] Обновить transformUser в api.js
- [ ] Обновить usersApi в api.js
- [ ] Создать UserContext
- [ ] Обновить Avatar компонент
- [ ] Создать ProgressBar компонент
- [ ] Создать StravaLink компонент
- [ ] Создать ClubGroupCard компонент
- [ ] Создать Statistics экран
- [ ] Создать Settings экран
- [ ] Обновить Profile экран
- [ ] Добавить роуты в App.jsx
- [ ] Обернуть в UserProvider

### QA
- [ ] Профиль отображается корректно
- [ ] Strava ссылка добавляется/удаляется
- [ ] Toggle фото работает глобально
- [ ] Статистика показывает данные по периодам
- [ ] Навигация между экранами работает
- [ ] Клубы/группы кликабельны
