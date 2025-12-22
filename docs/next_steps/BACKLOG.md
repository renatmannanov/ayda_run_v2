# BACKLOG - Невыполненные задачи Ayda Run v2

**Дата обновления:** 2025-12-22

---

## P0 - Критичные задачи

### 1. Тестирование P0 функционала в production
**Источник:** mvp_readiness_plan.md
**Цель:** Проверить работоспособность всех основных сценариев на production окружении
- Создание клуба
- Отправка заявки → уведомление админу → approve → уведомление пользователю
- Создание активности → уведомление участникам клуба
- Запись на активность
- Онбординг через `/start`
- Deep link invitations
- Команды `/requests` и `/my_requests`

---

## P1 - Важные задачи

### 2. GPX маршруты
**Источник:** mvp_readiness_plan.md, plan_1_done.md
**Цель:** Поддержка загрузки и отображения GPX маршрутов для активностей
- Загрузка GPX файлов
- Отображение маршрута на карте
- Скачивание GPX участниками

### 4. Telegram Group Integration - расширенная синхронизация
**Источник:** tggroup_plan_v1.md, tggroup_plan_v1_done.md
**Цель:** Расширить интеграцию с Telegram группами

**Что доделать:**
- Команда `/update_club` - синхронизация данных группы с клубом
- Обработка удаления бота из группы (webhook `my_chat_member`)
- Автоматическая синхронизация участников (при вступлении в TG группу → добавление в клуб)
- Публикация тренировок в группу с кнопками "Иду" / "Не иду"

---

## P2 - Желательные задачи

### 5. Analytics Dashboard
**Источник:** dashboard_plan_v1.md
**Цель:** Базовый дашборд с метриками для админов

**Phase 1 (MVP Dashboard):**
- Endpoint `/api/admin/analytics`
- Метрики: users (total, active_7d, new_7d), clubs (total, with_activities), activities (total, upcoming, completed, cancelled, avg_participants)
- Простая страница в admin panel с карточками

**Phase 2 (отложено):**
- User retention tracking
- Activity attendance rate
- Club engagement
- Графики с Recharts/Chart.js

### 6. Strava Integration
**Источник:** accesses_plan_v1.md
**Цель:** Добавить поддержку ссылки на Strava профиль

**Задачи:**
- Добавить поле `strava_link` в User модель (уже добавлено?)
- Обновить onboarding - добавить шаг запроса ссылки (опционально)
- Отображать в профиле и при заявках на вступление

### 7. Unit и Integration тесты для Access Control
**Источник:** accesses_plan_v1.md, accesses_final_summary.md
**Цель:** Покрыть тестами систему контроля доступа

**Задачи:**
- Unit тесты для JoinRequest модели
- Unit тесты для JoinRequestStorage
- Integration тесты для join request flow
- E2E тесты через frontend

### 8. Страница "Мои заявки" для пользователя
**Источник:** accesses_final_summary.md
**Цель:** UI страница для просмотра статуса заявок на вступление
- Список всех pending заявок
- История одобренных/отклоненных заявок

### 9. Фильтр "только открытые" в списках
**Источник:** accesses_final_summary.md
**Цель:** Добавить фильтр для показа только открытых клубов/групп/активностей

---

## P3 - Будущие улучшения

### 10. Event Tracking и Session Analytics
**Источник:** dashboard_plan_v1.md
**Цель:** Продвинутая аналитика использования приложения
- Таблица `events` для логирования действий
- Session tracking
- Feature usage analytics
- Интеграция с analytics service (Amplitude, Mixpanel, PostHog)

**Когда:** После 200+ пользователей

### 11. Cascades и правила удаления
**Источник:** plan_1_done.md
**Цель:** Продумать и реализовать логику при удалении клубов/групп/активностей

### 12. Database Indexes
**Источник:** plan_1_done.md
**Цель:** Оптимизация запросов (если потребуется при росте)

### 13. i18n (многоязычность)
**Источник:** onboarding_plan_v1_done.md
**Цель:** Поддержка нескольких языков в боте и webapp

### 14. A/B тестирование текстов
**Источник:** onboarding_plan_v1_done.md
**Цель:** Оптимизация конверсии онбординга через тестирование вариантов текстов

---

## Инфраструктурные задачи

### 15. Production Deployment
**Источник:** mvp_readiness_plan.md
**Задачи:**
- PostgreSQL database setup
- Environment variables настроены (.env)
- Telegram bot token и webhook настроены
- Frontend build и deploy (webapp/dist)
- Backend deploy (uvicorn/gunicorn)
- SSL сертификаты для webhook
- Monitoring (Sentry)

---

## Примечания

- Все задачи из файлов с суффиксом `_done.md` исключены как выполненные
- Файл `tggroup_sync_implementation_plan.md` исключен по запросу
- Приоритеты P0-P3 соответствуют важности для MVP и запуска
