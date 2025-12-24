# Plan: Фильтры по видам спорта на Home

## Обзор
Реализация фильтров по видам спорта на главной странице с кнопкой-эквалайзером и попапом выбора.

## UI Design

```
┌─────────────────────────────────────────┐
│ Мои / Все              [≡]           12 │  <- [≡] кнопка фильтра (эквалайзер)
└─────────────────────────────────────────┘

Попап:
┌─────────────────────────────────────────┐
│ Фильтр по спорту                     ✕  │
├─────────────────────────────────────────┤
│ [🏃 Бег] [⛰️ Трейл] [🚴 Вело]          │
│ [🥾 Хайкинг] [🧘 Йога] [💪 Workout]    │
│                                         │
│              [✕ Сбросить]               │  <- появляется если что-то выбрано
└─────────────────────────────────────────┘
```

## Изменения

### 1. Backend - Добавить новые виды спорта

**Файл:** `storage/db.py`

```python
class SportType(str, Enum):
    RUNNING = "running"
    TRAIL = "trail"
    HIKING = "hiking"
    CYCLING = "cycling"
    YOGA = "yoga"        # NEW
    WORKOUT = "workout"  # NEW
    OTHER = "other"
```

### 2. Backend - Множественный фильтр sport_types

**Файл:** `app/routers/activities.py`

Изменить параметр фильтра для поддержки множественного выбора:

```python
@router.get("", response_model=List[ActivityResponse])
async def list_activities(
    # ... existing params ...
    sport_types: Optional[str] = Query(None, description="Comma-separated sport types"),  # CHANGED
    # ...
):
    # ...
    if sport_types:
        types_list = [SportType(t.strip()) for t in sport_types.split(',')]
        query = query.filter(Activity.sport_type.in_(types_list))
```

### 3. Frontend - Обновить константы спорта

**Файл:** `webapp/src/constants/sports.js`

```javascript
export const SPORT_TYPES = [
    { id: 'running', icon: '🏃', label: 'Бег' },
    { id: 'trail', icon: '⛰️', label: 'Трейл' },
    { id: 'hiking', icon: '🥾', label: 'Хайкинг' },
    { id: 'cycling', icon: '🚴', label: 'Вело' },
    { id: 'yoga', icon: '🧘', label: 'Йога' },
    { id: 'workout', icon: '💪', label: 'Workout' },
]
```

**Файл:** `webapp/src/data/sample_data.js`

```javascript
export const sportTypes = [
    { id: 'running', icon: '🏃', label: 'Бег' },
    { id: 'trail', icon: '⛰️', label: 'Трейл' },
    { id: 'hiking', icon: '🥾', label: 'Хайкинг' },
    { id: 'cycling', icon: '🚴', label: 'Вело' },
    { id: 'yoga', icon: '🧘', label: 'Йога' },
    { id: 'workout', icon: '💪', label: 'Workout' },
]
```

### 4. Frontend - Компонент SportFilterButton

**Файл:** `webapp/src/components/home/SportFilterButton.jsx` (NEW)

Кнопка-эквалайзер в хедере:
- Иконка эквалайзера (3 горизонтальных полоски с точками)
- Подсвечивается если выбраны фильтры
- Показывает badge с количеством выбранных

```jsx
export function SportFilterButton({ selectedCount, onClick }) {
    const hasFilters = selectedCount > 0

    return (
        <button
            onClick={onClick}
            className={`relative p-2 rounded-lg transition-colors ${
                hasFilters
                    ? 'bg-gray-800 text-white'
                    : 'text-gray-400 hover:text-gray-600'
            }`}
        >
            {/* Equalizer icon */}
            <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
                <path d="M4 21v-7m0-4V3m8 18v-9m0-4V3m8 18v-5m0-4V3" />
                <circle cx="4" cy="14" r="2" fill="currentColor" />
                <circle cx="12" cy="8" r="2" fill="currentColor" />
                <circle cx="20" cy="16" r="2" fill="currentColor" />
            </svg>

            {/* Badge */}
            {hasFilters && (
                <span className="absolute -top-1 -right-1 w-4 h-4 bg-blue-500 text-white text-xs rounded-full flex items-center justify-center">
                    {selectedCount}
                </span>
            )}
        </button>
    )
}
```

### 5. Frontend - Компонент SportFilterPopup

**Файл:** `webapp/src/components/home/SportFilterPopup.jsx` (NEW)

Bottom sheet попап с выбором видов спорта:

```jsx
export function SportFilterPopup({
    isOpen,
    onClose,
    selectedSports,
    onToggle,
    onClear
}) {
    if (!isOpen) return null

    return (
        <div className="fixed inset-0 z-50 flex items-end justify-center">
            {/* Backdrop */}
            <div className="absolute inset-0 bg-black/30" onClick={onClose} />

            {/* Popup */}
            <div className="relative bg-white rounded-t-2xl w-full max-w-md p-4 pb-8">
                {/* Header */}
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-base font-medium text-gray-800">
                        Фильтр по спорту
                    </h3>
                    <button onClick={onClose} className="text-gray-400 hover:text-gray-600 p-1">
                        <XIcon />
                    </button>
                </div>

                {/* Pills */}
                <div className="flex flex-wrap gap-2">
                    {SPORT_TYPES.map(sport => (
                        <button
                            key={sport.id}
                            onClick={() => onToggle(sport.id)}
                            className={`flex items-center gap-1.5 px-3 py-2 rounded-full text-sm transition-colors ${
                                selectedSports.includes(sport.id)
                                    ? 'bg-gray-800 text-white'
                                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                            }`}
                        >
                            <span>{sport.icon}</span>
                            <span>{sport.label}</span>
                        </button>
                    ))}
                </div>

                {/* Reset button */}
                {selectedSports.length > 0 && (
                    <button
                        onClick={onClear}
                        className="mt-4 flex items-center gap-1.5 px-3 py-2 rounded-full text-sm text-gray-400 hover:text-gray-600 hover:bg-gray-100 mx-auto"
                    >
                        <XIcon className="w-4 h-4" />
                        <span>Сбросить</span>
                    </button>
                )}
            </div>
        </div>
    )
}
```

### 6. Frontend - Интеграция в Home.jsx

**Файл:** `webapp/src/screens/Home.jsx`

```jsx
// Добавить state
const [selectedSports, setSelectedSports] = useState([])
const [showSportFilter, setShowSportFilter] = useState(false)

// Изменить вызов useActivities с фильтрами
const filters = useMemo(() => {
    const f = {}
    if (selectedSports.length > 0) {
        f.sport_types = selectedSports.join(',')
    }
    return f
}, [selectedSports])

const { data: activities = [], isLoading: loading, error, refetch } = useActivities(filters)

// Handlers
const toggleSport = (sportId) => {
    setSelectedSports(prev =>
        prev.includes(sportId)
            ? prev.filter(id => id !== sportId)
            : [...prev, sportId]
    )
}

const clearSportFilters = () => setSelectedSports([])

// В header добавить кнопку фильтра
<div className="... flex items-center justify-between ...">
    <ModeToggle mode={mode} onModeChange={setMode} />
    <div className="flex items-center gap-2">
        <SportFilterButton
            selectedCount={selectedSports.length}
            onClick={() => setShowSportFilter(true)}
        />
        <span className="text-sm text-gray-400">{totalCount}</span>
    </div>
</div>

// Добавить попап
<SportFilterPopup
    isOpen={showSportFilter}
    onClose={() => setShowSportFilter(false)}
    selectedSports={selectedSports}
    onToggle={toggleSport}
    onClear={clearSportFilters}
/>
```

### 7. Frontend - Обновить api.js трансформер

**Файл:** `webapp/src/api.js`

Добавить иконки для новых типов спорта в transformActivity:

```javascript
icon: (a.sport_type === 'running' || !a.sport_type) ? '🏃' :
    a.sport_type === 'trail' ? '⛰️' :
    a.sport_type === 'cycling' ? '🚴' :
    a.sport_type === 'hiking' ? '🥾' :
    a.sport_type === 'yoga' ? '🧘' :
    a.sport_type === 'workout' ? '💪' : '🏃'
```

---

## Порядок реализации

1. **Backend: Enum SportType** - добавить yoga, workout
2. **Backend: API filter** - изменить sport_type на sport_types (множественный)
3. **Frontend: Constants** - добавить yoga, workout в SPORT_TYPES
4. **Frontend: SportFilterButton** - создать компонент кнопки
5. **Frontend: SportFilterPopup** - создать компонент попапа
6. **Frontend: Home.jsx** - интегрировать фильтры
7. **Frontend: api.js** - добавить иконки для новых типов
8. **Тестирование**

---

## Файлы для изменения

| Файл | Изменение |
|------|-----------|
| `storage/db.py` | Добавить YOGA, WORKOUT в SportType enum |
| `app/routers/activities.py` | Изменить sport_type на sport_types (comma-separated) |
| `webapp/src/constants/sports.js` | Добавить yoga, workout |
| `webapp/src/data/sample_data.js` | Добавить yoga, workout + обновить getSportIcon |
| `webapp/src/components/home/SportFilterButton.jsx` | NEW - кнопка эквалайзер |
| `webapp/src/components/home/SportFilterPopup.jsx` | NEW - попап выбора |
| `webapp/src/screens/Home.jsx` | Интегрировать фильтры |
| `webapp/src/api.js` | Добавить иконки yoga, workout |

---

## Чеклист

### Backend
- [x] Добавить YOGA в SportType enum
- [x] Добавить WORKOUT в SportType enum
- [x] Изменить API параметр на sport_types (множественный)
- [ ] Миграция БД (не требуется - enum расширяется автоматически)

### Frontend
- [x] Обновить SPORT_TYPES константу
- [x] Обновить sportTypes в sample_data.js
- [x] Обновить getSportIcon helper (через api.js transformer)
- [x] Создать SportFilterButton компонент
- [x] Создать SportFilterPopup компонент
- [x] Интегрировать в Home.jsx
- [x] Обновить transformActivity в api.js
- [x] Добавить CSS анимацию slide-up для попапа

### QA
- [ ] Фильтр работает с одним видом
- [ ] Фильтр работает с несколькими видами
- [ ] Сброс фильтров работает
- [ ] Кнопка показывает badge при активных фильтрах
- [ ] Счётчик активностей обновляется
