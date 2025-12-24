# План: Редактирование и Удаление клубов и групп

> **Уведомления:** Через Telegram бот (личное сообщение каждому участнику)

## Обзор задачи

Добавить полноценное редактирование и удаление клубов/групп с учётом:
- Уведомление всех участников при удалении
- Выбор действия с тренировками при удалении (удалить / открепить)
- Ограничения на редактируемые поля (telegram_chat_id, club_id для групп)
- Предупреждения при наличии участников и будущих тренировок

---

## Текущее состояние

### Что уже есть:
- ✅ Backend CRUD для клубов и групп (`app/routers/clubs.py`, `groups.py`)
- ✅ Frontend формы создания/редактирования (`CreateClub.jsx`, `CreateGroup.jsx`)
- ✅ Роуты для edit mode (`/club/:id/edit`, `/group/:id/edit`)
- ✅ Hooks с update/delete мутациями (`useClubs.ts`, `useGroups.ts`)
- ✅ Кнопки Edit/Delete в gear menu (`ClubGroupDetail.jsx`)

### Что нужно добавить:
- ❌ Уведомления участникам при удалении
- ❌ Диалог выбора действия с тренировками при удалении
- ❌ Проверка на immutable поля (telegram_chat_id, club_id)
- ❌ Предупреждение о количестве участников/тренировок
- ❌ Backend параметр notify_members + delete_activities

---

## Файлы для изменения

| Файл | Изменения |
|------|-----------|
| `bot/club_group_notifications.py` | **Новый файл** - уведомления об удалении клуба/группы |
| `app/routers/clubs.py` | DELETE: notify_members + delete_activities параметры |
| `app/routers/groups.py` | DELETE: notify_members + delete_activities параметры |
| `schemas/club.py` | Убрать telegram_chat_id из ClubUpdate |
| `schemas/group.py` | Убрать telegram_chat_id, club_id из GroupUpdate |
| `webapp/src/api.js` | Обновить delete методы с query параметрами |
| `webapp/src/hooks/useClubs.ts` | Обновить useDeleteClub с параметрами |
| `webapp/src/hooks/useGroups.ts` | Обновить useDeleteGroup с параметрами |
| `webapp/src/screens/ClubGroupDetail.jsx` | Диалог выбора при удалении |
| `webapp/src/screens/CreateClub.jsx` | Readonly для telegram_chat_id в edit mode |
| `webapp/src/screens/CreateGroup.jsx` | Readonly для telegram_chat_id, club в edit mode |

---

## Фаза 1: Backend - Уведомления

### 1.1 `bot/club_group_notifications.py` - новый файл

```python
"""
Club and Group deletion notifications
"""
from datetime import datetime
from telegram import Bot
from telegram.error import TelegramError
import logging

logger = logging.getLogger(__name__)


def format_club_deleted_notification(
    club_name: str,
    admin_name: str
) -> str:
    """
    Format notification about club deletion.
    """
    return (
        f"Клуб удалён\n\n"
        f"Клуб «{club_name}» был удалён администратором {admin_name}.\n\n"
        f"Все группы и тренировки клуба также удалены."
    )


def format_club_deleted_activities_kept_notification(
    club_name: str,
    admin_name: str
) -> str:
    """
    Format notification when club deleted but activities kept.
    """
    return (
        f"Клуб удалён\n\n"
        f"Клуб «{club_name}» был удалён администратором {admin_name}.\n\n"
        f"Тренировки сохранены и теперь принадлежат их создателям."
    )


async def send_club_deleted_notification(
    bot: Bot,
    user_telegram_id: int,
    club_name: str,
    admin_name: str,
    activities_deleted: bool = True
) -> bool:
    """Send club deletion notification to a member."""
    try:
        if activities_deleted:
            message = format_club_deleted_notification(club_name, admin_name)
        else:
            message = format_club_deleted_activities_kept_notification(club_name, admin_name)

        await bot.send_message(chat_id=user_telegram_id, text=message)
        logger.info(f"Sent club deleted notification to user {user_telegram_id}")
        return True
    except TelegramError as e:
        logger.error(f"Error sending club deleted notification: {e}")
        return False


def format_group_deleted_notification(
    group_name: str,
    admin_name: str,
    club_name: str = None
) -> str:
    """
    Format notification about group deletion.
    """
    if club_name:
        return (
            f"Группа удалена\n\n"
            f"Группа «{group_name}» клуба «{club_name}» была удалена.\n\n"
            f"Тренировки группы также удалены."
        )
    return (
        f"Группа удалена\n\n"
        f"Группа «{group_name}» была удалена администратором {admin_name}.\n\n"
        f"Тренировки группы также удалены."
    )


async def send_group_deleted_notification(
    bot: Bot,
    user_telegram_id: int,
    group_name: str,
    admin_name: str,
    club_name: str = None,
    activities_deleted: bool = True
) -> bool:
    """Send group deletion notification to a member."""
    try:
        message = format_group_deleted_notification(group_name, admin_name, club_name)
        await bot.send_message(chat_id=user_telegram_id, text=message)
        logger.info(f"Sent group deleted notification to user {user_telegram_id}")
        return True
    except TelegramError as e:
        logger.error(f"Error sending group deleted notification: {e}")
        return False
```

---

## Фаза 2: Backend - Обновление эндпоинтов

### 2.1 `app/routers/clubs.py` - обновить DELETE

```python
@router.delete("/{club_id}", status_code=204)
async def delete_club(
    club_id: str,
    notify_members: bool = Query(False, description="Send notifications to all members"),
    delete_activities: bool = Query(True, description="Delete all activities or detach them"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete club (ADMIN only).

    Args:
        notify_members: If True, send Telegram notification to all members
        delete_activities: If True, cascade delete activities;
                          If False, set club_id=NULL (detach to creator)
    """
    club = db.query(Club).filter(Club.id == club_id).first()
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")

    # Check permissions - ADMIN only
    require_club_permission(db, current_user, club_id, UserRole.ADMIN)

    # Get members to notify BEFORE deleting
    members_to_notify = []
    if notify_members:
        memberships = db.query(Membership, User).join(
            User, Membership.user_id == User.id
        ).filter(
            Membership.club_id == club_id,
            Membership.status == MembershipStatus.ACTIVE,
            User.id != current_user.id  # Don't notify admin who deletes
        ).all()
        members_to_notify = [u for _, u in memberships if u.telegram_id]

    # Count future activities for info
    future_activities_count = db.query(Activity).filter(
        Activity.club_id == club_id,
        Activity.date > datetime.now()
    ).count()

    # Save club data for notifications
    club_data = {
        'name': club.name,
        'admin_name': current_user.first_name or current_user.username or "Администратор"
    }

    # Handle activities
    if not delete_activities:
        # Detach activities - set club_id to NULL
        db.query(Activity).filter(Activity.club_id == club_id).update(
            {Activity.club_id: None, Activity.visibility: ActivityVisibility.PUBLIC},
            synchronize_session=False
        )
        # Also detach group activities
        group_ids = [g.id for g in db.query(Group.id).filter(Group.club_id == club_id).all()]
        if group_ids:
            db.query(Activity).filter(Activity.group_id.in_(group_ids)).update(
                {Activity.group_id: None, Activity.club_id: None, Activity.visibility: ActivityVisibility.PUBLIC},
                synchronize_session=False
            )

    # Delete club (cascades to groups, memberships, and activities if delete_activities=True)
    db.delete(club)
    db.commit()

    # Send notifications asynchronously
    if members_to_notify:
        asyncio.create_task(_send_club_deleted_notifications(
            members_to_notify,
            club_data,
            activities_deleted=delete_activities
        ))

    return None
```

### 2.2 `app/routers/groups.py` - обновить DELETE

```python
@router.delete("/{group_id}", status_code=204)
async def delete_group(
    group_id: str,
    notify_members: bool = Query(False, description="Send notifications to all members"),
    delete_activities: bool = Query(True, description="Delete all activities or detach them"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete group.

    Permissions:
    - Standalone group: ADMIN only
    - Club group: ORGANIZER or higher in the club
    """
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    # Check permissions
    if group.club_id:
        require_club_permission(db, current_user, group.club_id, UserRole.ORGANIZER)
    else:
        require_group_permission(db, current_user, group_id, UserRole.ADMIN)

    # Get members to notify BEFORE deleting
    members_to_notify = []
    if notify_members:
        memberships = db.query(Membership, User).join(
            User, Membership.user_id == User.id
        ).filter(
            Membership.group_id == group_id,
            Membership.status == MembershipStatus.ACTIVE,
            User.id != current_user.id
        ).all()
        members_to_notify = [u for _, u in memberships if u.telegram_id]

    # Save group data for notifications
    club_name = None
    if group.club_id:
        club = db.query(Club).filter(Club.id == group.club_id).first()
        club_name = club.name if club else None

    group_data = {
        'name': group.name,
        'admin_name': current_user.first_name or current_user.username or "Администратор",
        'club_name': club_name
    }

    # Handle activities
    if not delete_activities:
        db.query(Activity).filter(Activity.group_id == group_id).update(
            {Activity.group_id: None, Activity.club_id: None, Activity.visibility: ActivityVisibility.PUBLIC},
            synchronize_session=False
        )

    # Delete group
    db.delete(group)
    db.commit()

    # Send notifications
    if members_to_notify:
        asyncio.create_task(_send_group_deleted_notifications(
            members_to_notify,
            group_data,
            activities_deleted=delete_activities
        ))

    return None
```

### 2.3 Schemas - ограничить Update

**`schemas/club.py`:**
```python
class ClubUpdate(BaseModel):
    """Schema for updating club.

    Note: telegram_chat_id is immutable after creation.
    """
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    # telegram_chat_id is immutable - cannot be changed
    is_paid: Optional[bool] = None
    price_per_activity: Optional[float] = None
    is_open: Optional[bool] = None
```

**`schemas/group.py`:**
```python
class GroupUpdate(BaseModel):
    """Schema for updating group.

    Note: telegram_chat_id and club_id are immutable after creation.
    """
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    # telegram_chat_id is immutable
    # club_id is immutable - cannot change group's club affiliation
    is_open: Optional[bool] = None
```

---

## Фаза 3: Frontend - API и Hooks

### 3.1 `api.js` - обновить delete методы

```javascript
// Clubs API
delete: (id, notifyMembers = false, deleteActivities = true) => apiFetch(
    `/clubs/${id}?notify_members=${notifyMembers}&delete_activities=${deleteActivities}`,
    { method: 'DELETE' }
),

// Groups API
delete: (id, notifyMembers = false, deleteActivities = true) => apiFetch(
    `/groups/${id}?notify_members=${notifyMembers}&delete_activities=${deleteActivities}`,
    { method: 'DELETE' }
),
```

### 3.2 `useClubs.ts` - обновить hook

```typescript
export function useDeleteClub() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      id,
      notifyMembers = false,
      deleteActivities = true
    }: {
      id: string;
      notifyMembers?: boolean;
      deleteActivities?: boolean;
    }) => clubsApi.delete(id, notifyMembers, deleteActivities),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: clubsKeys.lists() })
    },
  })
}
```

### 3.3 `useGroups.ts` - обновить hook

```typescript
export function useDeleteGroup() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      id,
      notifyMembers = false,
      deleteActivities = true
    }: {
      id: string;
      notifyMembers?: boolean;
      deleteActivities?: boolean;
    }) => groupsApi.delete(id, notifyMembers, deleteActivities),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: groupsKeys.lists() })
    },
  })
}
```

---

## Фаза 4: Frontend - Диалог удаления

### 4.1 `ClubGroupDetail.jsx` - обновить handleDelete

```jsx
const handleDelete = () => {
    const membersCount = item.members || 0
    const entityName = type === 'club' ? 'клуб' : 'группу'

    // First: ask about activities
    const askAboutActivities = (callback) => {
        tg.showConfirm(
            `Что сделать с тренировками ${type === 'club' ? 'клуба' : 'группы'}?`,
            // Telegram showConfirm doesn't support custom buttons
            // So we use two-step confirmation
        )
        // Actually, Telegram WebApp doesn't support custom button labels
        // We need a different approach - see Alternative below
    }

    // Alternative: Sequential confirmation dialogs

    // Step 1: Confirm deletion
    tg.showConfirm(
        membersCount > 0
            ? `Удалить ${entityName}? В ${type === 'club' ? 'нём' : 'ней'} ${membersCount} участников.`
            : `Удалить ${entityName}?`,
        (confirmed) => {
            if (!confirmed) return

            // Step 2: Ask about activities
            tg.showConfirm(
                'Удалить тренировки вместе с ' + (type === 'club' ? 'клубом' : 'группой') + '?\n\n' +
                '«Да» - удалить все тренировки\n' +
                '«Отмена» - сохранить тренировки',
                (deleteActivities) => {
                    // Step 3: Confirm notification
                    if (membersCount > 0) {
                        tg.showConfirm(
                            'Уведомить участников об удалении?',
                            (notify) => {
                                performDelete(notify, deleteActivities)
                            }
                        )
                    } else {
                        performDelete(false, deleteActivities)
                    }
                }
            )
        }
    )
}

const performDelete = async (notifyMembers, deleteActivities) => {
    try {
        tg.haptic('medium')
        if (type === 'club') {
            await deleteClub({ id, notifyMembers, deleteActivities })
        } else {
            await deleteGroup({ id, notifyMembers, deleteActivities })
        }
        tg.hapticNotification('success')
        tg.showAlert(type === 'club' ? 'Клуб удалён' : 'Группа удалена')
        navigate('/clubs')
    } catch (e) {
        console.error('Delete failed', e)
        tg.showAlert(e.message || 'Ошибка при удалении')
    }
}
```

### 4.2 `CreateClub.jsx` - readonly поля в edit mode

```jsx
{/* Telegram Chat - disabled in edit mode if already set */}
{isEditMode && existingClub?.telegramChatId ? (
    <div className="mb-4">
        <label className="text-sm text-gray-700 mb-2 block">Telegram чат</label>
        <div className="px-4 py-3 bg-gray-100 rounded-xl text-sm text-gray-500">
            Привязан к чату
            <span className="text-xs text-gray-400 ml-2">(нельзя изменить)</span>
        </div>
    </div>
) : (
    <FormInput
        label="Telegram чат"
        value={telegramChat}
        onChange={setTelegramChat}
        placeholder="@clubchat или ID"
    />
)}
```

### 4.3 `CreateGroup.jsx` - readonly поля в edit mode

```jsx
{/* Club selector - disabled in edit mode */}
{isEditMode ? (
    <div className="mb-4">
        <label className="text-sm text-gray-700 mb-2 block">Клуб</label>
        <div className="px-4 py-3 bg-gray-100 rounded-xl text-sm text-gray-500">
            {existingGroup?.clubId ? `Часть клуба` : 'Независимая группа'}
            <span className="text-xs text-gray-400 ml-2">(нельзя изменить)</span>
        </div>
    </div>
) : (
    // Club selector UI
)}

{/* Telegram Chat - disabled in edit mode if set */}
{isEditMode && existingGroup?.telegramChatId ? (
    <div className="mb-4">
        <label className="text-sm text-gray-700 mb-2 block">Telegram чат</label>
        <div className="px-4 py-3 bg-gray-100 rounded-xl text-sm text-gray-500">
            Привязан к чату
            <span className="text-xs text-gray-400 ml-2">(нельзя изменить)</span>
        </div>
    </div>
) : (
    <FormInput ... />
)}
```

---

## Фаза 5: Уведомления при редактировании (опционально)

По аналогии с активностями можно добавить уведомления при изменении важных параметров:
- Изменение названия
- Изменение is_open (открытый/закрытый)
- Изменение is_paid / price_per_activity

Это можно сделать позже как отдельную задачу.

---

## Порядок реализации

1. **Backend уведомления** - `bot/club_group_notifications.py` (новый файл)
2. **Backend schemas** - убрать immutable поля из Update схем
3. **Backend DELETE** - `clubs.py`, `groups.py` (параметры notify + delete_activities)
4. **Frontend API** - `api.js` (параметры в delete методах)
5. **Frontend Hooks** - `useClubs.ts`, `useGroups.ts` (обновить мутации)
6. **Frontend UI** - `ClubGroupDetail.jsx` (диалог удаления)
7. **Frontend Forms** - `CreateClub.jsx`, `CreateGroup.jsx` (readonly поля)
8. **Тестирование** всех сценариев

---

## Тестовые сценарии

### Удаление клуба
1. ✅ Удалить пустой клуб без уведомлений
2. ✅ Удалить клуб с участниками + уведомить
3. ✅ Удалить клуб + удалить тренировки
4. ✅ Удалить клуб + сохранить тренировки (открепить)
5. ✅ Проверить каскадное удаление групп

### Удаление группы
1. ✅ Удалить пустую группу
2. ✅ Удалить группу клуба (ORGANIZER+)
3. ✅ Удалить независимую группу (ADMIN only)
4. ✅ Удалить + уведомить участников
5. ✅ Удалить + сохранить тренировки

### Редактирование
1. ✅ Редактировать название, описание
2. ✅ Изменить is_open
3. ❌ Попытка изменить telegram_chat_id (должен быть readonly)
4. ❌ Попытка изменить club_id группы (должен быть readonly)

---

## Оценка сложности

| Компонент | Сложность | Время |
|-----------|-----------|-------|
| Backend уведомления | Низкая | — |
| Backend schemas | Низкая | — |
| Backend DELETE | Средняя | — |
| Frontend API/Hooks | Низкая | — |
| Frontend диалог удаления | Средняя | — |
| Frontend readonly поля | Низкая | — |
| **Итого** | **Средняя** | — |
