/**
 * 📚 СПРАВОЧНИК ВСЕХ ИКОНОК ПРОЕКТА
 *
 * Этот файл содержит все кастомные SVG иконки для удобного переиспользования.
 * Иконки разбиты по категориям: навигация, действия, статусы и т.д.
 */

import React from 'react'


// ============================================
// 🧭 НАВИГАЦИЯ (BottomNav)
// ============================================
//
// 📅 CalendarIcon - раздел "Активности" 
// 👥 ClubsIcon - раздел "Клубы" 
// 👤 ProfileIcon - раздел "Профиль"

export const CalendarIcon = ({ className = "w-5 h-5" }) => (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 012.25-2.25h13.5A2.25 2.25 0 0121 7.5v11.25m-18 0A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75m-18 0v-7.5A2.25 2.25 0 015.25 9h13.5A2.25 2.25 0 0121 11.25v7.5" />
    </svg>
)

export const ClubsIcon = ({ className = "w-5 h-5" }) => (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M18 18.72a9.094 9.094 0 003.741-.479 3 3 0 00-4.682-2.72m.94 3.198l.001.031c0 .225-.012.447-.037.666A11.944 11.944 0 0112 21c-2.17 0-4.207-.576-5.963-1.584A6.062 6.062 0 016 18.719m12 0a5.971 5.971 0 00-.941-3.197m0 0A5.995 5.995 0 0012 12.75a5.995 5.995 0 00-5.058 2.772m0 0a3 3 0 00-4.681 2.72 8.986 8.986 0 003.74.477m.94-3.197a5.971 5.971 0 00-.94 3.197M15 6.75a3 3 0 11-6 0 3 3 0 016 0zm6 3a2.25 2.25 0 11-4.5 0 2.25 2.25 0 014.5 0zm-13.5 0a2.25 2.25 0 11-4.5 0 2.25 2.25 0 014.5 0z" />
    </svg>
)

export const ProfileIcon = ({ className = "w-5 h-5" }) => (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
    </svg>
)


// ============================================
// ⬅️ СТРЕЛКИ И НАВИГАЦИЯ
// ============================================
//
// ◀️ ChevronLeftIcon - назад
// ▶️ ChevronRightIcon - вперёд
// 🔽 ChevronDownIcon - выпадающий список

export const ChevronLeftIcon = ({ className = "w-5 h-5", strokeWidth = 2 }) => (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={strokeWidth}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
    </svg>
)

export const ChevronRightIcon = ({ className = "w-5 h-5", strokeWidth = 2 }) => (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={strokeWidth}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
    </svg>
)

export const ChevronDownIcon = ({ className = "w-5 h-5", strokeWidth = 2 }) => (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={strokeWidth}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
    </svg>
)


// ============================================
// 🎬 ДЕЙСТВИЯ
// ============================================
//
// ➕ PlusIcon - добавить/создать
// ✖️ CloseIcon - закрыть
// 🗑️ TrashIcon - удалить
// 📤 ShareIcon - поделиться
// 🔍 SearchIcon - поиск (лупа)
// 🎚️ FilterIcon - фильтр (эквалайзер)
// 🔗 ExternalLinkIcon - внешняя ссылка

export const PlusIcon = ({ className = "w-4 h-4", strokeWidth = 3 }) => (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={strokeWidth}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v12m6-6H6" />
    </svg>
)

export const CloseIcon = ({ className = "w-5 h-5", strokeWidth = 2 }) => (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={strokeWidth}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
    </svg>
)

export const TrashIcon = ({ className = "w-5 h-5", strokeWidth = 2 }) => (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={strokeWidth}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
    </svg>
)

export const ShareIcon = ({ className = "w-5 h-5", strokeWidth = 2 }) => (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={strokeWidth}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
    </svg>
)

export const SearchIcon = ({ className = "w-3.5 h-3.5", strokeWidth = 2.5 }) => (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round">
        <circle cx="10" cy="10" r="6" />
        <line x1="14.5" y1="14.5" x2="20" y2="20" />
    </svg>
)

export const FilterIcon = ({ className = "w-3.5 h-3.5", strokeWidth = 2.5 }) => (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={strokeWidth} strokeLinecap="round">
        <line x1="4" y1="4" x2="4" y2="20" />
        <circle cx="4" cy="14" r="2.5" fill="currentColor" stroke="none" />
        <line x1="12" y1="4" x2="12" y2="20" />
        <circle cx="12" cy="8" r="2.5" fill="currentColor" stroke="none" />
        <line x1="20" y1="4" x2="20" y2="20" />
        <circle cx="20" cy="16" r="2.5" fill="currentColor" stroke="none" />
    </svg>
)

export const ExternalLinkIcon = ({ className = "w-4 h-4", strokeWidth = 2 }) => (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={strokeWidth}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
    </svg>
)


// ============================================
// ✅ СТАТУСЫ (общие)
// ============================================
//
// ✓ CheckIcon - галочка (успех)
// ✗ XMarkIcon - крестик (отмена)
// 🔒 LockIcon - замок (приватно)
// 🕐 ClockIcon - часы (ожидание)
// 🔄 RepeatIcon - повторение (recurring)

export const CheckIcon = ({ className = "w-5 h-5", strokeWidth = 2 }) => (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={strokeWidth}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
    </svg>
)

export const XMarkIcon = ({ className = "w-5 h-5", strokeWidth = 3 }) => (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={strokeWidth}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
    </svg>
)

export const LockIcon = ({ className = "w-5 h-5", strokeWidth = 2 }) => (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={strokeWidth}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
    </svg>
)

export const ClockIcon = ({ className = "w-5 h-5", strokeWidth = 2 }) => (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={strokeWidth}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6l4 2m6-2a10 10 0 11-20 0 10 10 0 0120 0z" />
    </svg>
)

export const RepeatIcon = ({ className = "w-4 h-4", strokeWidth = 2 }) => (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={strokeWidth}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
    </svg>
)


// ============================================
// ⭕ СТАТУСЫ КАРТОЧЕК (ActivityCard)
// Используются внутри круглых кнопок 7x7
// ============================================
//
// ➕ StatusPlusIcon - не записан (серый)
// ✓ StatusCheckIcon - записан (серый)
// ✗ StatusXIcon - пропустил (серый)
// 🕐 StatusClockIcon - ожидает (серый)
// ✅ StatusAttendedIcon - участвовал (зелёный)
// ❌ StatusMissedIcon - пропустил подтв. (серый)

export const StatusPlusIcon = ({ className = "w-3.5 h-3.5" }) => (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v12m6-6H6" />
    </svg>
)

export const StatusCheckIcon = ({ className = "w-3.5 h-3.5" }) => (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
    </svg>
)

export const StatusXIcon = ({ className = "w-3.5 h-3.5" }) => (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
    </svg>
)

export const StatusClockIcon = ({ className = "w-3.5 h-3.5" }) => (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6l4 2m6-2a10 10 0 11-20 0 10 10 0 0120 0z" />
    </svg>
)

export const StatusAttendedIcon = ({ className = "w-5 h-5" }) => (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
    </svg>
)

export const StatusMissedIcon = ({ className = "w-5 h-5" }) => (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
    </svg>
)


// ============================================
// 📱 TELEGRAM
// ============================================
//
// ✈️ TelegramIcon - бейдж связанного чата

export const TelegramIcon = ({ className = "w-2.5 h-2.5" }) => (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
        <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
    </svg>
)


// ============================================
// 🏃 EMOJI ИКОНКИ - СПОРТ (constants/sports.js)
// ============================================
//
// 🏃 Бег (running)
// ⛰️ Трейл (trail)
// 🥾 Хайкинг (hiking)
// 🚴 Вело (cycling)
// 🧘 Йога (yoga)
// 💪 Workout (workout)


// ============================================
// 🎨 EMOJI ИКОНКИ - ИНТЕРФЕЙС
// ============================================
//
// 📅 Календарь/дата
// 📍 Локация/маршрут/GPX
// 📊 Статистика
// ⚙️ Настройки
// 🏆 Клуб
// 👥 Группа
// 🌐 Публичный
// 🔒 Приватный
// ✏️ Редактировать
// 🗑️ Удалить
// ❤️ Любовь
// ? Ожидание подтверждения (оранжевый)


// ============================================
// 📦 ЭКСПОРТ ПО УМОЛЧАНИЮ
// ============================================

export default {
    // 🧭 Навигация (BottomNav)
    CalendarIcon,
    ClubsIcon,
    ProfileIcon,

    // ⬅️ Стрелки
    ChevronLeftIcon,
    ChevronRightIcon,
    ChevronDownIcon,

    // 🎬 Действия
    PlusIcon,
    CloseIcon,
    TrashIcon,
    ShareIcon,
    SearchIcon,
    FilterIcon,
    ExternalLinkIcon,

    // ✅ Статусы (общие)
    CheckIcon,
    XMarkIcon,
    LockIcon,
    ClockIcon,
    RepeatIcon,

    // ⭕ Статусы карточек
    StatusPlusIcon,
    StatusCheckIcon,
    StatusXIcon,
    StatusClockIcon,
    StatusAttendedIcon,
    StatusMissedIcon,

    // 📱 Соцсети
    TelegramIcon,
}
