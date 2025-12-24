# Ayda Run — Экраны создания сущностей

## Файлы

| Файл | Описание |
|------|----------|
| `ayda-run-create-activity.jsx` | Создание активности |
| `ayda-run-create-club.jsx` | Создание клуба |
| `ayda-run-create-group.jsx` | Создание группы |
| `ayda-run-create-shared.jsx` | Общие компоненты |

---

## Общая схема логики

### Два ключевых параметра

Каждая сущность имеет:
1. **Видимость** — кто может видеть/найти
2. **Доступ** — кто может записаться/вступить

---

### Активность

```
Видимость (dropdown):
├── 🌐 Публичная · видят все
├── 🏆 {Клуб} · клуб
└── 👥 {Группа} · {Клуб}

Кто может записаться? (toggle):
├── [Все желающие]
└── [🔒 По заявке]
```

**Комбинации:**

| Видимость | Доступ | Результат |
|-----------|--------|-----------|
| Публичная | Все | Видят все, записываются все |
| Публичная | По заявке | Видят все, нужна заявка |
| Клуб/Группа | Все | Видят участники, записываются все участники |
| Клуб/Группа | По заявке | Видят участники, нужна заявка |

---

### Клуб

```
Видимость (dropdown):
├── 🌐 Публичный · все могут найти
└── 🔒 Закрытый · только по заявке    ← фиксирует доступ

Кто может вступить? (toggle):
├── [Все желающие]     ← только для публичного
└── [🔒 По заявке]     ← единственный для закрытого
```

**Комбинации:**

| Видимость | Доступ | Результат |
|-----------|--------|-----------|
| Публичный | Все | Находят все, вступают все |
| Публичный | По заявке | Находят все, нужна заявка |
| Закрытый | По заявке (fixed) | Только по приглашению + заявка |

**Важно:** При выборе "Закрытый" доступ автоматически фиксируется на "По заявке".

---

### Группа

```
Видимость (dropdown):
├── 🌐 Публичная · видят все
└── 🏆 {Клуб} · только участники клуба

Кто может вступить? (toggle):
├── [Все желающие]
└── [🔒 По заявке]
```

**Комбинации:**

| Видимость | Доступ | Результат |
|-----------|--------|-----------|
| Публичная | Все | Видят все, вступают все |
| Публичная | По заявке | Видят все, нужна заявка |
| Клуб | Все | Видят участники клуба, вступают все |
| Клуб | По заявке | Видят участники клуба, нужна заявка |

---

## UI компоненты

### DropdownPicker

Используется для **Видимость**.

```jsx
<DropdownPicker
  value={visibility}
  options={visibilityOptions}
  onChange={setVisibility}
  placeholder="Выбрать..."
/>
```

**Где:** Все три экрана, секция "Видимость"

---

### ToggleButtons

Используется для **Кто может записаться/вступить**.

```jsx
<ToggleButtons
  options={accessOptions}
  selected={access}
  onChange={setAccess}
  hint={getAccessHint()}
/>
```

**Где:** Все три экрана, секция "Кто может..."

---

### FixedAccess

Используется когда доступ зафиксирован (закрытый клуб).

```jsx
<FixedAccess
  icon="🔒"
  label="По заявке"
  hint="Закрытый клуб — вступление только по заявке"
/>
```

**Где:** `ayda-run-create-club.jsx`, когда `visibility === 'private'`

---

### GPXUploadPopup

Универсальный попап для работы с GPX файлами.

```jsx
<GPXUploadPopup
  isOpen={isOpen}
  onClose={handleClose}
  onSkip={handleSkip}      // только для mode='create'
  onUpload={handleUpload}
  mode="create"            // 'create' | 'add' | 'edit'
  existingFile={file}      // для mode='edit'
/>
```

**Где:** 
- `CreateActivityScreen` — после создания
- Экран деталей активности — добавление/редактирование

---

## Структура данных

### Visibility options

**Активность:**
```javascript
const visibilityOptions = [
  { id: 'public', icon: '🌐', label: 'Публичная', sublabel: 'видят все' },
  { id: 'club_1', icon: '🏆', label: 'SRG Almaty', sublabel: 'клуб' },
  { id: 'group_1', icon: '👥', label: 'Горные бегуны', sublabel: 'SRG Almaty' },
];
```

**Клуб:**
```javascript
const visibilityOptions = [
  { id: 'public', icon: '🌐', label: 'Публичный', sublabel: 'все могут найти' },
  { id: 'private', icon: '🔒', label: 'Закрытый', sublabel: 'только по заявке' },
];
```

**Группа:**
```javascript
const visibilityOptions = [
  { id: 'public', icon: '🌐', label: 'Публичная', sublabel: 'видят все' },
  { id: 'club_1', icon: '🏆', label: 'SRG Almaty', sublabel: 'только участники клуба' },
];
```

---

### Access options

Одинаковые для всех:
```javascript
const accessOptions = [
  { id: 'open', label: 'Все желающие' },
  { id: 'request', icon: '🔒', label: 'По заявке' },
];
```

---

## Порядок полей

### Активность
1. Название
2. Видимость
3. Кто может записаться?

### Клуб
1. Название
2. Описание
3. Виды спорта
4. Telegram чат
5. Видимость
6. Кто может вступить?

### Группа
1. Название
2. Описание
3. Telegram чат
4. Видимость
5. Кто может вступить?

---

## Проверка соответствия

### Чеклист для агента

**1. Видимость — всегда DropdownPicker:**
- [ ] Активность: public / club_{id} / group_{id}
- [ ] Клуб: public / private
- [ ] Группа: public / club_{id}

**2. Доступ — всегда ToggleButtons:**
- [ ] Опции: "Все желающие" / "🔒 По заявке"
- [ ] Hint меняется в зависимости от выбора

**3. Клуб — особая логика:**
- [ ] При `visibility === 'private'` → `access` фиксируется на `'request'`
- [ ] Показывается `FixedAccess` вместо `ToggleButtons`

**4. Лейблы:**
- [ ] Активность: "Кто может записаться?"
- [ ] Клуб/Группа: "Кто может вступить?"

---

## Backend модели

### Activity
```typescript
interface Activity {
  visibility: 'public' | 'club' | 'group';
  visibilityTargetId?: string;  // club_id или group_id
  access: 'open' | 'request';
}
```

### Club
```typescript
interface Club {
  visibility: 'public' | 'private';
  access: 'open' | 'request';  // 'request' если visibility === 'private'
}
```

### Group
```typescript
interface Group {
  visibility: 'public' | 'club';
  visibilityTargetId?: string;  // club_id
  access: 'open' | 'request';
}
```

---

## GPX Upload Popup

### Использование

Один компонент `GPXUploadPopup` для трёх сценариев:

| Сценарий | mode | Когда появляется |
|----------|------|------------------|
| После создания активности | `create` | Автоматически после "Создать тренировку" |
| Добавление к существующей | `add` | Из экрана деталей активности |
| Редактирование маршрута | `edit` | Из экрана деталей активности |

---

### Props

```typescript
interface GPXUploadPopupProps {
  isOpen: boolean;
  onClose: () => void;
  onSkip?: () => void;        // только для mode='create'
  onUpload: (file: GPXFile) => void;
  mode: 'create' | 'add' | 'edit';
  existingFile?: GPXFile;     // для mode='edit'
}

interface GPXFile {
  name: string;
  size: string;
}
```

---

### UI по режимам

**mode="create":**
```
┌─────────────────────────────────┐
│ Добавить маршрут             ✕  │
│                                 │
│ Хотите добавить GPX файл с      │
│ маршрутом? Это поможет          │
│ участникам лучше подготовиться. │
│                                 │
│  ┌─────────────────────────┐    │
│  │        📍               │    │
│  │  Выбрать GPX файл       │    │
│  └─────────────────────────┘    │
│                                 │
│  [Пропустить]    [Готово]       │
└─────────────────────────────────┘
```

**mode="add":**
```
┌─────────────────────────────────┐
│ Добавить GPX                 ✕  │
│                                 │
│ Загрузите GPX файл с маршрутом  │
│ тренировки                      │
│  ...                            │
│  [Отмена]       [Добавить]      │
└─────────────────────────────────┘
```

**mode="edit":**
```
┌─────────────────────────────────┐
│ Изменить GPX                 ✕  │
│                                 │
│ Загрузите новый GPX файл для    │
│ замены текущего маршрута        │
│                                 │
│  ┌─────────────────────────┐    │
│  │ 📍 medeu_trail.gpx   🗑  │    │
│  │    124.5 KB              │    │
│  └─────────────────────────┘    │
│                                 │
│           [Сохранить]           │
└─────────────────────────────────┘
```

---

### Флоу создания активности

```
[Форма] → [Создать тренировку]
              ↓
        [GPX Popup]
         ↙      ↘
   [Пропустить]  [Загрузить]
         ↘      ↙
        [Success]
              ↓
         [Готово]
```

**Где в коде:** `CreateActivityScreen`, state `flowStep`

---

### Интеграция в экран деталей

```jsx
// Кнопка добавления GPX (если нет файла)
<button onClick={() => setShowGpxPopup(true)}>
  📍 Добавить маршрут
</button>

// Кнопка редактирования GPX (если есть файл)
<button onClick={() => setShowGpxPopup(true)}>
  📍 medeu_trail.gpx  ✎
</button>

// Popup
<GPXUploadPopup
  isOpen={showGpxPopup}
  onClose={() => setShowGpxPopup(false)}
  onUpload={handleGpxUpload}
  mode={activity.gpxFile ? 'edit' : 'add'}
  existingFile={activity.gpxFile}
/>
```

---

### Backend

```typescript
interface Activity {
  // ... другие поля
  gpxFile?: {
    url: string;
    name: string;
    size: string;
    uploadedAt: Date;
  };
}
```

**Endpoints:**
- `POST /api/activities/{id}/gpx` — загрузка файла
- `PUT /api/activities/{id}/gpx` — замена файла
- `DELETE /api/activities/{id}/gpx` — удаление файла
