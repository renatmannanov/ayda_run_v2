# План: Удаление и Редактирование активности в ActivityDetail

> **Уведомления:** Через Telegram бот (личное сообщение каждому участнику)

## Обзор задачи

Добавить функции удаления и редактирования активности на экране ActivityDetail с учётом:
- Блокировка для прошедших активностей
- Предупреждение и уведомление участников при наличии регистраций
- Ограничения на редактируемые поля

---

## Файлы для изменения

| Файл | Изменения |
|------|-----------|
| `webapp/src/screens/ActivityDetail.jsx` | Добавить handleDelete, handleEdit с логикой подтверждения |
| `webapp/src/screens/ActivityCreate.jsx` | Добавить isEditMode логику для редактирования |
| `webapp/src/hooks/useActivities.ts` | Обновить useDeleteActivity и useUpdateActivity с параметром notify |
| `webapp/src/api.js` | Обновить delete и update методы с query параметром |
| `webapp/src/App.jsx` | Добавить роут `/activity/:id/edit` |
| `app/routers/activities.py` | Обновить DELETE и PATCH с notify_participants и проверкой isPast |
| `bot/activity_notifications.py` | Добавить функции уведомлений об отмене/изменении |
| `schemas/activity.py` | Убрать sport_type, club_id, group_id из ActivityUpdate |

---

## Фаза 1: Backend - Уведомления участникам

### 1.1 `bot/activity_notifications.py` - добавить функции

```python
def format_activity_cancelled_notification(activity_title, activity_date, location, organizer_name) -> str:
    """Форматирование уведомления об отмене"""

async def send_activity_cancelled_notification(bot, user_telegram_id, activity_title, ...) -> bool:
    """Отправить уведомление об отмене участнику"""

def format_activity_updated_notification(activity_title, changes_summary) -> str:
    """Форматирование уведомления об изменениях"""

async def send_activity_updated_notification(bot, user_telegram_id, activity_title, ...) -> bool:
    """Отправить уведомление об изменениях участнику"""
```

### 1.2 `app/routers/activities.py` - обновить DELETE

- Добавить query параметр `notify_participants: bool = False`
- Проверка `activity.date < datetime.now()` → 400 "Cannot delete past activities"
- Перед удалением получить список участников (REGISTERED/CONFIRMED)
- После удаления асинхронно отправить уведомления

### 1.3 `app/routers/activities.py` - обновить PATCH

- Добавить query параметр `notify_participants: bool = False`
- Проверка `activity.date < datetime.now()` → 400 "Cannot update past activities"
- Сохранить старые значения для формирования changes_summary
- После обновления асинхронно отправить уведомления

### 1.4 `schemas/activity.py` - ограничить ActivityUpdate

Убрать из схемы:
- `sport_type` (нельзя менять тип активности)
- `club_id` (нельзя менять клуб)
- `group_id` (нельзя менять группу)

---

## Фаза 2: Frontend - Удаление активности

### 2.1 `ActivityDetail.jsx` - handleDelete

```jsx
const { mutate: deleteActivity, isPending: deleting } = useDeleteActivity()

const handleDelete = async () => {
    if (isPast) return

    const joinedCount = participants.filter(p =>
        p.userId !== activity.creatorId &&
        ['registered', 'confirmed'].includes(p.status)
    ).length

    if (joinedCount > 0) {
        tg.showConfirm(
            `У этой тренировки ${joinedCount} участников. Удалить и уведомить их?`,
            (confirmed) => {
                if (confirmed) deleteActivity({ id, notifyParticipants: true })
            }
        )
    } else {
        tg.showConfirm('Удалить тренировку?', (confirmed) => {
            if (confirmed) deleteActivity({ id })
        })
    }
}
```

### 2.2 Обновить кнопку удаления

```jsx
<button
    onClick={handleDelete}
    disabled={isPast || deleting}
    className={isPast ? 'opacity-50 cursor-not-allowed' : ''}
>
    🗑 {deleting ? 'Удаление...' : 'Удалить'}
</button>
```

---

## Фаза 3: Frontend - Редактирование активности

### 3.1 `App.jsx` - добавить роут

```jsx
<Route path="/activity/:id/edit" element={<ActivityCreate />} />
```

### 3.2 `ActivityCreate.jsx` - добавить режим редактирования

```jsx
const { id } = useParams()
const isEditMode = !!id

// Загрузка данных в режиме редактирования
const { data: existingActivity } = useActivity(isEditMode ? id : null)
const { data: participantsData } = useActivityParticipants(isEditMode ? id : null)

// Заполнение формы при загрузке
useEffect(() => {
    if (existingActivity) {
        setTitle(existingActivity.title)
        setDescription(existingActivity.description)
        // ... остальные поля
    }
}, [existingActivity])

// В edit mode: sportType, club, group - readonly
// При сохранении: предупреждение если есть участники
```

### 3.3 `ActivityDetail.jsx` - handleEdit

```jsx
<button
    onClick={() => navigate(`/activity/${id}/edit`)}
    disabled={isPast}
    className={isPast ? 'opacity-50 cursor-not-allowed' : ''}
>
    ✏️ Редактировать
</button>
```

---

## Фаза 4: API и Hooks

### 4.1 `api.js`

```javascript
delete: (id, notifyParticipants = false) =>
    apiFetch(`/activities/${id}?notify_participants=${notifyParticipants}`, { method: 'DELETE' }),

update: (id, data, notifyParticipants = false) =>
    apiFetch(`/activities/${id}?notify_participants=${notifyParticipants}`, {
        method: 'PATCH',
        body: JSON.stringify(data)
    }).then(transformActivity),
```

### 4.2 `useActivities.ts`

```typescript
export function useDeleteActivity() {
  return useMutation({
    mutationFn: ({ id, notifyParticipants = false }) =>
      activitiesApi.delete(id, notifyParticipants),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: activitiesKeys.lists() })
  })
}

export function useUpdateActivity() {
  return useMutation({
    mutationFn: ({ id, data, notifyParticipants = false }) =>
      activitiesApi.update(id, data, notifyParticipants),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: activitiesKeys.detail(id) })
      queryClient.invalidateQueries({ queryKey: activitiesKeys.lists() })
    }
  })
}
```

---

## Порядок реализации

1. **Backend уведомления** - `bot/activity_notifications.py`
2. **Backend ограничения** - `schemas/activity.py` (убрать поля из ActivityUpdate)
3. **Backend эндпоинты** - `app/routers/activities.py` (notify_participants + isPast check)
4. **Frontend API** - `api.js`, `useActivities.ts`
5. **Frontend удаление** - `ActivityDetail.jsx` (handleDelete + кнопка)
6. **Frontend редактирование** - `App.jsx` (роут), `ActivityCreate.jsx` (isEditMode)
7. **Тестирование** всех сценариев
