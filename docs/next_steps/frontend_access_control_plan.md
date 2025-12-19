# Frontend Access Control Implementation Plan

## Задача
Добавить поддержку открытых/закрытых клубов, групп и активностей во frontend.

## Изменения в API слое (webapp/src/api.js)

### 1. transformActivity - добавить isOpen
```javascript
const transformActivity = (a) => !a ? null : ({
    // ... existing fields
    isOpen: a.is_open,
    canViewParticipants: a.can_view_participants,
    canDownloadGpx: a.can_download_gpx,
    // ... rest
})
```

### 2. transformClub - добавить isOpen
```javascript
const transformClub = (c) => !c ? null : ({
    // ... existing fields
    isOpen: c.is_open,
    // ... rest
})
```

### 3. transformGroup - уже есть isOpen ✓
```javascript
// Already has: isOpen: g.is_open
```

### 4. Добавить методы для join requests в activitiesApi
```javascript
export const activitiesApi = {
    // ... existing methods

    requestJoin: (id) => apiFetch(`/activities/${id}/request-join`, { method: 'POST' }),
}
```

### 5. Добавить методы для join requests в clubsApi
```javascript
export const clubsApi = {
    // ... existing methods

    requestJoin: (id) => apiFetch(`/clubs/${id}/request-join`, { method: 'POST' }),
}
```

### 6. Добавить методы для join requests в groupsApi
```javascript
export const groupsApi = {
    // ... existing methods

    requestJoin: (id) => apiFetch(`/groups/${id}/request-join`, { method: 'POST' }),
}
```

## Изменения в компонентах

### 1. ActivityCard.jsx - добавить иконку замка для закрытых активностей

**Место**: В заголовке карточки (строка 54-58)

**Изменение**:
```jsx
<h3 className="text-base text-gray-800 font-medium pr-2 flex items-center gap-1">
    {!activity.isOpen && <span className="text-gray-400">🔒</span>}
    {activity.title}
</h3>
```

### 2. ClubCard.jsx - добавить иконку замка для закрытых клубов

**Проверить файл и добавить аналогично ActivityCard**

### 3. GroupCard.jsx - добавить иконку замка для закрытых групп

**Проверить файл и добавить аналогично ActivityCard**

### 4. ActivityDetail.jsx - основные изменения

#### 4.1. Обновить useJoinActivity hook
**Место**: hooks/useActivities.ts

**Логика**:
- Если `activity.isOpen === true` → вызывать `activitiesApi.join(id)`
- Если `activity.isOpen === false` → вызывать `activitiesApi.requestJoin(id)` и показать уведомление

#### 4.2. Обновить текст кнопки (строка 258-264)
```jsx
{isJoined ? (
    <Button ...>
        <span>Иду ✓</span>
        <span className="text-green-400">·</span>
        <span className="text-green-500 font-normal">Отменить</span>
    </Button>
) : isFull ? (
    <Button disabled ...>Мест нет</Button>
) : (
    <Button onClick={handleJoinToggle} ...>
        {activity.isOpen ? 'Записаться' : 'Отправить заявку'}
    </Button>
)}
```

#### 4.3. Добавить иконку замка в заголовок (строка 99-101)
```jsx
<h1 className="text-xl text-gray-800 font-medium mb-1 flex items-center gap-2">
    {!activity.isOpen && <span className="text-gray-400">🔒</span>}
    {activity.title}
</h1>
```

#### 4.4. Скрыть GPX для закрытых активностей (строка 141-153)
```jsx
{activity.gpxLink && activity.canDownloadGpx && (
    <div className="flex items-start gap-3">
        <span className="text-gray-400">📎</span>
        <a href={activity.gpxLink} ...>
            Маршрут GPX →
        </a>
    </div>
)}
```

#### 4.5. Обновить отображение участников (строка 169-207)
```jsx
{/* Participants */}
<div className="mb-4">
    <p className="text-sm text-gray-500 mb-3">
        Участники · {activity.canViewParticipants
            ? (isPast
                ? `${attendedCount} из ${participants.length} были`
                : activity.maxParticipants !== null
                    ? `${activity.participants}/${activity.maxParticipants}`
                    : `${activity.participants}`
            )
            : `${activity.participants}`
        }
        {!activity.canViewParticipants && !activity.isMember && (
            <span className="text-xs text-gray-400"> (только участники)</span>
        )}
    </p>

    {activity.canViewParticipants && (
        <button onClick={() => setShowParticipants(true)} ...>
            {/* Existing participant avatars */}
        </button>
    )}

    {!activity.canViewParticipants && (
        <p className="text-sm text-gray-400">
            🔒 Список участников доступен только членам активности
        </p>
    )}
</div>
```

#### 4.6. Обновить обработчик join для уведомления
```jsx
const handleJoinToggle = async () => {
    try {
        if (isJoined) {
            await leaveActivity(id)
        } else {
            if (activity.isOpen) {
                await joinActivity(id)
            } else {
                // Send join request
                await requestJoinActivity(id)
                // Show confirmation
                tg.showAlert('Заявка отправлена! Мы уведомим тебя, когда организатор рассмотрит её.')
            }
        }
        refetchActivity()
        refetchParticipants()
    } catch (e) {
        console.error('Action failed', e)
        tg.showAlert(e.message || 'Ошибка при отправке заявки')
    }
}
```

### 5. ClubGroupDetail.jsx - аналогичные изменения

**Проверить структуру файла и применить аналогичную логику:**
- Иконка замка в заголовке
- Кнопка "Вступить" vs "Отправить заявку"
- Скрытие списка участников для не-членов закрытых сущностей

## Изменения в hooks

### useActivities.ts

Добавить хук для join request:
```typescript
export function useRequestJoinActivity() {
    const { mutate, loading, error } = useApi(activitiesApi.requestJoin)
    return { mutate, loading, error }
}
```

### useClubs.ts

Добавить хук для join request:
```typescript
export function useRequestJoinClub() {
    const { mutate, loading, error } = useApi(clubsApi.requestJoin)
    return { mutate, loading, error }
}
```

### useGroups.ts

Добавить хук для join request:
```typescript
export function useRequestJoinGroup() {
    const { mutate, loading, error } = useApi(groupsApi.requestJoin)
    return { mutate, loading, error }
}
```

## Порядок внесения изменений

1. ✅ **api.js** - добавить поля в transformers и методы requestJoin
2. ✅ **hooks** - добавить useRequestJoinActivity, useRequestJoinClub, useRequestJoinGroup
3. ✅ **ActivityCard.jsx** - добавить иконку замка
4. ✅ **ClubCard.jsx** - добавить иконку замка
5. ✅ **GroupCard.jsx** - проверить иконку замка (уже может быть)
6. ✅ **ActivityDetail.jsx** - все изменения для активности
7. ✅ **ClubGroupDetail.jsx** - все изменения для клубов/групп
8. ✅ **Тестирование** - проверить все флоу

## Тестовые сценарии

1. **Открытая активность**:
   - Кнопка "Записаться" → сразу добавляет в участники
   - Виден список участников
   - Доступен GPX (если есть)

2. **Закрытая активность (не участник)**:
   - Иконка замка 🔒 в заголовке
   - Кнопка "Отправить заявку" → показывает уведомление
   - Скрыт список участников (только количество)
   - Не доступен GPX

3. **Закрытая активность (участник)**:
   - Иконка замка 🔒 в заголовке
   - Виден список участников
   - Доступен GPX (если есть)

4. **Аналогично для клубов и групп**

## Важные замечания

- Все изменения должны быть обратно совместимы
- Для старых данных без поля `is_open` предполагаем `true` (открыто)
- Обработка ошибок должна показывать понятные сообщения пользователю
- Использовать `tg.showAlert()` для уведомлений
- Иконка замка: 🔒 (Unicode U+1F512)
