# Ayda Run — Create Screens Implementation Plan

## Обзор изменений

Редизайн экранов создания: ActivityCreate, CreateClub, CreateGroup.

### Ключевые изменения:
1. **Унификация UI** — DropdownPicker для видимости, ToggleButtons для доступа
2. **GPX Popup** — после создания активности показывается popup для загрузки GPX
3. **Унификация Success** — единый Success popup для всех экранов, редирект на созданную сущность

---

## Фаза 1: Новые Shared-компоненты

### 1.1 DropdownPicker

**Файл:** `webapp/src/components/ui/DropdownPicker.jsx`

```jsx
// Props:
// - value: string (id выбранного элемента)
// - options: Array<{ id, icon?, label, sublabel? }>
// - onChange: (id) => void
// - placeholder: string

// Стилизация:
// - Кнопка с border, при клике открывает dropdown
// - Иконка + label + sublabel (серый, через "·")
// - Стрелка вниз, поворачивается при открытии
// - Dropdown: абсолютный, с тенью, checkmark у выбранного
```

### 1.2 ToggleButtons

**Файл:** `webapp/src/components/ui/ToggleButtons.jsx`

```jsx
// Props:
// - options: Array<{ id, icon?, label }>
// - selected: string
// - onChange: (id) => void
// - hint?: string
// - disabled?: boolean

// Стилизация:
// - Кнопки в ряд с gap-2
// - Выбранная: bg-gray-800 text-white
// - Не выбранная: bg-gray-100 text-gray-600
// - Hint под кнопками (xs, text-gray-400)
```

### 1.3 FixedAccess

**Файл:** `webapp/src/components/ui/FixedAccess.jsx`

```jsx
// Props:
// - icon?: string
// - label: string
// - hint?: string

// Стилизация:
// - Одна "кнопка" (не кликабельная) в стиле selected ToggleButton
// - Hint под ней
```

### 1.4 GPXUploadPopup

**Файл:** `webapp/src/components/ui/GPXUploadPopup.jsx`

```jsx
// Props:
// - isOpen: boolean
// - onClose: () => void
// - onSkip?: () => void (только для mode='create')
// - onUpload: (file: { name, size }) => Promise<void>
// - mode: 'create' | 'add' | 'edit'
// - existingFile?: { name, size }
// - activityId?: string (для API calls)

// UI по режимам:
// mode='create':
//   - Title: "Добавить маршрут"
//   - Description: "Хотите добавить GPX файл..."
//   - Кнопки: "Пропустить" + "Готово" (если файл выбран)
//
// mode='add':
//   - Title: "Добавить GPX"
//   - Description: "Загрузите GPX файл..."
//   - Кнопки: "Отмена" + "Добавить"
//
// mode='edit':
//   - Title: "Изменить GPX"
//   - Description: "Загрузите новый GPX..."
//   - Показывает текущий файл с кнопкой удаления
//   - Кнопка: "Сохранить"

// Внутренняя логика:
// - useState для выбранного файла
// - Валидация: .gpx, макс 20MB
// - При загрузке показывает preview файла
// - Кнопка удаления (иконка корзины)
```

### 1.5 SuccessPopup

**Файл:** `webapp/src/components/ui/SuccessPopup.jsx`

```jsx
// Props:
// - isOpen: boolean
// - title: string (e.g. "Тренировка создана!")
// - description?: string
// - onDone: () => void
// - shareLink?: string (опционально, для клубов/групп)
// - onCopyLink?: () => void

// UI:
// - Fullscreen overlay с центрированным модалом
// - Зеленая галочка в круге
// - Title + Description
// - Если shareLink: показать поле со ссылкой + кнопки Копировать/Поделиться
// - Кнопка "Готово" / "Перейти к [сущность]"
```

### 1.6 Экспорт компонентов

**Файл:** `webapp/src/components/ui/index.jsx` — добавить экспорты:

```jsx
export { default as DropdownPicker } from './DropdownPicker'
export { default as ToggleButtons } from './ToggleButtons'
export { default as FixedAccess } from './FixedAccess'
export { default as GPXUploadPopup } from './GPXUploadPopup'
export { default as SuccessPopup } from './SuccessPopup'
```

---

## Фаза 2: ActivityCreate — Рефакторинг

### 2.1 Изменения состояния

```jsx
// Удалить:
// - isPublic (boolean)
// - selectedClub, selectedGroup (отдельные поля)
// - showClubPicker

// Добавить:
// - visibility: string ('public' | 'club_{id}' | 'group_{id}')
// - access: string ('open' | 'request')
// - flowStep: 'form' | 'gpx' | 'success'
// - createdActivityId: string | null
```

### 2.2 Visibility Options Builder

```jsx
const buildVisibilityOptions = (clubs, groups) => {
  const options = [
    { id: 'public', icon: '🌐', label: 'Публичная', sublabel: 'видят все' }
  ]

  // Добавить клубы пользователя
  clubs.filter(c => c.isMember).forEach(club => {
    options.push({
      id: `club_${club.id}`,
      icon: '🏆',
      label: club.name,
      sublabel: 'клуб'
    })
  })

  // Добавить группы пользователя
  groups.filter(g => g.isMember).forEach(group => {
    options.push({
      id: `group_${group.id}`,
      icon: '👥',
      label: group.name,
      sublabel: group.clubName || 'группа'
    })
  })

  return options
}
```

### 2.3 Access Options

```jsx
const accessOptions = [
  { id: 'open', label: 'Все желающие' },
  { id: 'request', icon: '🔒', label: 'По заявке' }
]

const getAccessHint = (access, visibility) => {
  if (access === 'open') {
    return visibility === 'public'
      ? 'Любой может записаться на тренировку'
      : 'Любой участник может записаться'
  }
  return 'Нужно одобрение организатора'
}
```

### 2.4 Замена ClubGroupPicker на DropdownPicker

```jsx
// Было:
<FormSelect
  label="Клуб / Группа"
  value={getClubGroupDisplay()}
  onClick={() => setShowClubPicker(true)}
/>

// Стало:
<div className="mb-4">
  <label className="text-sm text-gray-700 mb-2 block">Видимость</label>
  <DropdownPicker
    value={visibility}
    options={visibilityOptions}
    onChange={setVisibility}
    placeholder="Выбрать..."
  />
</div>
```

### 2.5 Замена Access toggle на ToggleButtons

```jsx
// Было (inline кнопки):
<div className="flex gap-2">
  <button onClick={() => setIsOpen(true)} ...>Все желающие</button>
  <button onClick={() => setIsOpen(false)} ...>🔒 По заявке</button>
</div>

// Стало:
<div className="mb-4">
  <label className="text-sm text-gray-700 mb-2 block">Кто может записаться?</label>
  <ToggleButtons
    options={accessOptions}
    selected={access}
    onChange={setAccess}
    hint={getAccessHint(access, visibility)}
  />
</div>
```

### 2.6 Парсинг visibility для API

```jsx
const parseVisibility = (visibility) => {
  if (visibility === 'public') {
    return { club_id: null, group_id: null }
  }
  if (visibility.startsWith('club_')) {
    return { club_id: visibility.replace('club_', ''), group_id: null }
  }
  if (visibility.startsWith('group_')) {
    return { club_id: null, group_id: visibility.replace('group_', '') }
  }
  return { club_id: null, group_id: null }
}
```

### 2.7 Flow после создания

```jsx
const handleSubmit = async () => {
  if (!validate()) return

  try {
    const { club_id, group_id } = parseVisibility(visibility)

    const result = await createActivity({
      title,
      date: `${date}T${time}:00`,
      location: locationValue,
      sport_type: sportType,
      distance: distance ? parseFloat(distance) : null,
      duration: duration ? parseInt(duration) : null,
      difficulty,
      max_participants: noLimit ? null : parseInt(maxParticipants),
      description,
      club_id,
      group_id,
      is_open: access === 'open'
    })

    setCreatedActivityId(result.id)
    setFlowStep('gpx') // Показываем GPX popup

  } catch (e) {
    console.error('Failed to create activity', e)
    tg.showAlert(`Ошибка: ${e.message || 'Не удалось создать'}`)
  }
}

const handleGpxUpload = async (file) => {
  // API call уже внутри GPXUploadPopup
  setFlowStep('success')
}

const handleGpxSkip = () => {
  setFlowStep('success')
}

const handleSuccessDone = () => {
  navigate(`/activity/${createdActivityId}`)
}
```

### 2.8 JSX изменения (в конце формы)

```jsx
// Заменить секцию "Клуб / Группа" + "Кто может записаться?"

<div className="border-t border-gray-200 my-4" />

{/* Видимость */}
{isEditMode ? (
  <div className="mb-4">
    <label className="text-sm text-gray-700 mb-2 block">Видимость</label>
    <div className="px-4 py-3 bg-gray-100 rounded-xl text-sm text-gray-500">
      {getVisibilityDisplay()}
      <span className="text-xs text-gray-400 ml-2">(нельзя изменить)</span>
    </div>
  </div>
) : (
  <div className="mb-4">
    <label className="text-sm text-gray-700 mb-2 block">Видимость</label>
    <DropdownPicker
      value={visibility}
      options={visibilityOptions}
      onChange={setVisibility}
      placeholder="Выбрать..."
    />
  </div>
)}

{/* Доступ */}
<div className="mb-4">
  <label className="text-sm text-gray-700 mb-2 block">Кто может записаться?</label>
  <ToggleButtons
    options={accessOptions}
    selected={access}
    onChange={setAccess}
    hint={getAccessHint(access, visibility)}
  />
</div>

{/* GPX Popup */}
<GPXUploadPopup
  isOpen={flowStep === 'gpx'}
  onClose={() => setFlowStep('form')}
  onSkip={handleGpxSkip}
  onUpload={handleGpxUpload}
  mode="create"
  activityId={createdActivityId}
/>

{/* Success Popup */}
<SuccessPopup
  isOpen={flowStep === 'success'}
  title="Тренировка создана!"
  description="Участники смогут записаться на неё"
  onDone={handleSuccessDone}
/>
```

---

## Фаза 3: CreateClub — Рефакторинг

### 3.1 Изменения состояния

```jsx
// Удалить:
// - visibilityOptions (FormRadioGroup options)

// Добавить/изменить:
// - visibility: 'public' | 'private'
// - access: 'open' | 'request'
```

### 3.2 Visibility Options

```jsx
const visibilityOptions = [
  { id: 'public', icon: '🌐', label: 'Публичный', sublabel: 'все могут найти' },
  { id: 'private', icon: '🔒', label: 'Закрытый', sublabel: 'только по приглашению' }
]
```

### 3.3 Access с учётом private

```jsx
const handleVisibilityChange = (newVisibility) => {
  setVisibility(newVisibility)
  // При закрытом клубе - фиксируем доступ
  if (newVisibility === 'private') {
    setAccess('request')
  }
}

const accessOptions = [
  { id: 'open', label: 'Все желающие' },
  { id: 'request', icon: '🔒', label: 'По заявке' }
]

const getAccessHint = () => {
  if (visibility === 'private') {
    return 'Закрытый клуб — вступление только по заявке'
  }
  if (access === 'open') {
    return 'Любой может вступить в клуб'
  }
  return 'Нужно одобрение администратора'
}
```

### 3.4 JSX изменения

```jsx
// Заменить FormRadioGroup на:

<div className="mb-4">
  <label className="text-sm text-gray-700 mb-2 block">Видимость</label>
  <DropdownPicker
    value={visibility}
    options={visibilityOptions}
    onChange={handleVisibilityChange}
    placeholder="Выбрать..."
  />
</div>

<div className="mb-4">
  <label className="text-sm text-gray-700 mb-2 block">Кто может вступить?</label>
  {visibility === 'private' ? (
    <FixedAccess
      icon="🔒"
      label="По заявке"
      hint={getAccessHint()}
    />
  ) : (
    <ToggleButtons
      options={accessOptions}
      selected={access}
      onChange={setAccess}
      hint={getAccessHint()}
    />
  )}
</div>
```

### 3.5 Замена Success экрана

```jsx
// Удалить inline Success screen

// Добавить state:
const [showSuccess, setShowSuccess] = useState(false)

// В handleSubmit:
const result = await createClub(payload)
setCreatedId(result.id)
setShareLink(`https://t.me/aydarun_bot?start=club_${result.id}`)
setShowSuccess(true)

// JSX:
<SuccessPopup
  isOpen={showSuccess}
  title="Клуб создан!"
  description="Пригласи участников по ссылке"
  shareLink={shareLink}
  onCopyLink={() => {
    navigator.clipboard.writeText(shareLink)
    tg.showAlert('Ссылка скопирована!')
  }}
  onDone={() => navigate(`/club/${createdId}`)}
/>
```

### 3.6 API payload

```jsx
const payload = {
  name,
  description,
  is_private: visibility === 'private',
  is_open: access === 'open'  // false если private
}
```

---

## Фаза 4: CreateGroup — Рефакторинг

### 4.1 Изменения состояния

```jsx
// Удалить:
// - isIndependent (checkbox)
// - showClubPicker
// - joinAccessOptions (FormRadioGroup)

// Добавить:
// - visibility: 'public' | 'club_{id}'
// - access: 'open' | 'request'
```

### 4.2 Visibility Options Builder

```jsx
const buildVisibilityOptions = (clubs) => {
  const options = [
    { id: 'public', icon: '🌐', label: 'Публичная', sublabel: 'видят все' }
  ]

  clubs.filter(c => c.isMember).forEach(club => {
    options.push({
      id: `club_${club.id}`,
      icon: '🏆',
      label: club.name,
      sublabel: 'только участники клуба'
    })
  })

  return options
}
```

### 4.3 Access Options

```jsx
const accessOptions = [
  { id: 'open', label: 'Все желающие' },
  { id: 'request', icon: '🔒', label: 'По заявке' }
]

const getAccessHint = () => {
  if (access === 'open') {
    return visibility === 'public'
      ? 'Любой может вступить в группу'
      : 'Любой участник клуба может вступить'
  }
  return 'Нужно одобрение администратора'
}
```

### 4.4 JSX изменения

```jsx
// Удалить секцию "Часть клуба?" с checkbox

// Заменить на:
<div className="mb-4">
  <label className="text-sm text-gray-700 mb-2 block">Видимость</label>
  <DropdownPicker
    value={visibility}
    options={visibilityOptions}
    onChange={setVisibility}
    placeholder="Выбрать..."
    disabled={isEditMode}
  />
  {isEditMode && (
    <p className="text-xs text-gray-400 mt-1">Нельзя изменить привязку к клубу</p>
  )}
</div>

<div className="mb-4">
  <label className="text-sm text-gray-700 mb-2 block">Кто может вступить?</label>
  <ToggleButtons
    options={accessOptions}
    selected={access}
    onChange={setAccess}
    hint={getAccessHint()}
  />
</div>
```

### 4.5 Парсинг visibility для API

```jsx
const parseVisibility = (visibility) => {
  if (visibility === 'public') {
    return { club_id: null }
  }
  if (visibility.startsWith('club_')) {
    return { club_id: visibility.replace('club_', '') }
  }
  return { club_id: null }
}
```

### 4.6 Замена Success экрана

```jsx
// Аналогично клубу:
<SuccessPopup
  isOpen={showSuccess}
  title="Группа создана!"
  description="Пригласи участников по ссылке"
  shareLink={shareLink}
  onCopyLink={() => {
    navigator.clipboard.writeText(shareLink)
    tg.showAlert('Ссылка скопирована!')
  }}
  onDone={() => navigate(`/group/${createdId}`)}
/>
```

---

## Фаза 5: ActivityDetail — GPX интеграция

### 5.1 Изменения

```jsx
// Добавить state:
const [showGpxPopup, setShowGpxPopup] = useState(false)

// Заменить GpxUpload на кнопки:
{canEdit && (
  <>
    <div className="border-t border-gray-200 my-4" />
    <div className="space-y-2">
      {!activity.hasGpx ? (
        <button
          onClick={() => setShowGpxPopup(true)}
          className="flex items-center gap-2 text-sm text-gray-700 hover:text-gray-900 py-1"
        >
          <span className="w-5 text-center">📍</span>
          <span className="font-medium">Добавить маршрут</span>
        </button>
      ) : (
        <button
          onClick={() => setShowGpxPopup(true)}
          className="flex items-center gap-2 text-sm text-gray-700 hover:text-gray-900 py-1"
        >
          <span className="w-5 text-center">📍</span>
          <span>{activity.gpxFilename || 'track.gpx'}</span>
          <span className="text-gray-400">✎</span>
        </button>
      )}
      {/* ... edit/delete buttons */}
    </div>
  </>
)}

{/* GPX Popup */}
<GPXUploadPopup
  isOpen={showGpxPopup}
  onClose={() => setShowGpxPopup(false)}
  onUpload={async (file) => {
    setShowGpxPopup(false)
    refetchActivity()
  }}
  mode={activity.hasGpx ? 'edit' : 'add'}
  existingFile={activity.hasGpx ? { name: activity.gpxFilename, size: '' } : null}
  activityId={activity.id}
/>
```

---

## Фаза 6: Порядок полей (финальный)

### ActivityCreate:
1. Название *
2. Когда * (дата + время)
3. Где *
4. Тип активности
5. --- divider ---
6. Дистанция / Набор
7. Длительность / Сложность
8. Макс. участников
9. --- divider ---
10. Описание
11. --- divider ---
12. **Видимость** (DropdownPicker)
13. **Кто может записаться?** (ToggleButtons)

### CreateClub:
1. Название клуба *
2. Описание
3. Виды активностей
4. --- divider ---
5. Telegram чат клуба
6. --- divider ---
7. **Видимость** (DropdownPicker)
8. **Кто может вступить?** (ToggleButtons/FixedAccess)

### CreateGroup:
1. Название группы *
2. Описание
3. --- divider ---
4. Telegram чат группы
5. --- divider ---
6. **Видимость** (DropdownPicker)
7. **Кто может вступить?** (ToggleButtons)

---

## Чеклист реализации

### Новые компоненты:
- [ ] `DropdownPicker.jsx`
- [ ] `ToggleButtons.jsx`
- [ ] `FixedAccess.jsx`
- [ ] `GPXUploadPopup.jsx`
- [ ] `SuccessPopup.jsx`
- [ ] Обновить `components/ui/index.jsx`
- [ ] Обновить `components/index.jsx`

### ActivityCreate:
- [ ] Заменить isPublic + selectedClub/Group на visibility
- [ ] Заменить isOpen на access
- [ ] Добавить flowStep state
- [ ] Заменить ClubGroupPicker на DropdownPicker
- [ ] Заменить inline кнопки на ToggleButtons
- [ ] Добавить GPXUploadPopup
- [ ] Добавить SuccessPopup
- [ ] Обновить handleSubmit для нового flow

### CreateClub:
- [ ] Заменить FormRadioGroup на DropdownPicker
- [ ] Добавить ToggleButtons/FixedAccess
- [ ] Добавить логику автоматического access='request' при private
- [ ] Заменить inline Success на SuccessPopup

### CreateGroup:
- [ ] Удалить isIndependent checkbox
- [ ] Удалить ClubPicker
- [ ] Заменить на DropdownPicker для visibility
- [ ] Заменить FormRadioGroup на ToggleButtons
- [ ] Заменить inline Success на SuccessPopup

### ActivityDetail:
- [ ] Заменить GpxUpload на GPXUploadPopup
- [ ] Добавить режимы add/edit

---

## Примечания

1. **Edit mode** — для ActivityCreate в режиме редактирования:
   - Visibility показывается как disabled (нельзя изменить)
   - Access можно менять

2. **Backend совместимость** — проверить что API принимает:
   - `is_private` для клубов
   - `is_open` для access
   - club_id / group_id для привязки

3. **GPX API** — уже реализовано:
   - `POST /api/activities/{id}/gpx` — загрузка
   - `DELETE /api/activities/{id}/gpx` — удаление
   - Замена = DELETE + POST

4. **Telegram интеграция** — использовать tg.showAlert для уведомлений
