/**
 * API wrapper for Ayda Run backend
 */

const API_BASE = '/api'

// Get Telegram WebApp init data for auth
const getAuthHeaders = () => {
    const headers = {
        'Content-Type': 'application/json'
    }

    if (window.Telegram?.WebApp?.initData) {
        headers['X-Telegram-Init-Data'] = window.Telegram.WebApp.initData
    }

    return headers
}

// Generic fetch wrapper
async function apiFetch(endpoint, options = {}) {
    const response = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        headers: {
            ...getAuthHeaders(),
            ...options.headers
        }
    })

    if (!response.ok) {
        const error = await response.json().catch(() => ({}))
        throw new Error(error.detail || `HTTP ${response.status}`)
    }

    if (response.status === 204) return null
    return response.json()
}

// ============================================================================
// Data Transformers (Snake_case -> CamelCase)
// ============================================================================

const transformUser = (u) => !u ? null : ({
    ...u,
    firstName: u.first_name,
    lastName: u.last_name,
    telegramId: u.telegram_id,
    createdAt: u.created_at
})

const transformActivity = (a) => !a ? null : ({
    ...a,
    sportType: a.sport_type,
    maxParticipants: a.max_participants,
    participants: a.participants_count, // Map count to prop expected by UI
    isJoined: a.is_joined,
    clubId: a.club_id,
    groupId: a.group_id,
    club: a.club_name,
    group: a.group_name,
    creatorId: a.creator_id,
    createdAt: a.created_at,
    isPast: new Date(a.date) < new Date(),
    icon: (a.sport_type === 'running' || !a.sport_type) ? '🏃' :
        a.sport_type === 'cycling' ? '🚴' :
            a.sport_type === 'hiking' ? '🥾' : '🏃'
})

const transformClub = (c) => !c ? null : ({
    ...c,
    isPaid: c.is_paid,
    pricePerActivity: c.price_per_activity,
    telegramChatId: c.telegram_chat_id,
    createdAt: c.created_at,
    groupsCount: c.groups_count,
    members: c.members_count, // Map count
    isMember: c.is_member,
    userRole: c.user_role,
    isAdmin: c.user_role === 'admin' || c.user_role === 'organizer'
})

const transformGroup = (g) => !g ? null : ({
    ...g,
    clubId: g.club_id,
    telegramChatId: g.telegram_chat_id,
    isOpen: g.is_open,
    createdAt: g.created_at,
    members: g.members_count, // Map count
    isMember: g.is_member,
    userRole: g.user_role,
    isAdmin: g.user_role === 'admin' || g.user_role === 'trainer'
})

const transformMember = (m) => !m ? null : ({
    ...m,
    userId: m.user_id,
    telegramId: m.telegram_id,
    firstName: m.first_name,
    joinedAt: m.joined_at,
    avatar: '👤' // Mock avatar
})


// ============================================================================
// Users API
// ============================================================================

export const usersApi = {
    getMe: () => apiFetch('/users/me').then(transformUser)
}

// ============================================================================
// Activities API
// ============================================================================

export const activitiesApi = {
    list: (filters = {}) => {
        const params = new URLSearchParams(filters).toString()
        return apiFetch(`/activities${params ? `?${params}` : ''}`)
            .then(items => items.map(transformActivity))
    },

    get: (id) => apiFetch(`/activities/${id}`).then(transformActivity),

    create: (data) => apiFetch('/activities', {
        method: 'POST',
        body: JSON.stringify(data)
    }).then(transformActivity),

    update: (id, data) => apiFetch(`/activities/${id}`, {
        method: 'PATCH',
        body: JSON.stringify(data)
    }).then(transformActivity),

    delete: (id) => apiFetch(`/activities/${id}`, { method: 'DELETE' }),

    join: (id) => apiFetch(`/activities/${id}/join`, { method: 'POST' }),

    leave: (id) => apiFetch(`/activities/${id}/leave`, { method: 'POST' }),

    getParticipants: (id) => apiFetch(`/activities/${id}/participants`)
        .then(items => items.map(transformMember))
}

// ============================================================================
// Clubs API
// ============================================================================

export const clubsApi = {
    list: (limit = 50, offset = 0) =>
        apiFetch(`/clubs?limit=${limit}&offset=${offset}`)
            .then(items => items.map(transformClub)),

    get: (id) => apiFetch(`/clubs/${id}`).then(transformClub),

    create: (data) => apiFetch('/clubs', {
        method: 'POST',
        body: JSON.stringify(data)
    }).then(transformClub),

    update: (id, data) => apiFetch(`/clubs/${id}`, {
        method: 'PATCH',
        body: JSON.stringify(data)
    }).then(transformClub),

    delete: (id) => apiFetch(`/clubs/${id}`, { method: 'DELETE' }),

    join: (id) => apiFetch(`/clubs/${id}/join`, { method: 'POST' }),

    getMembers: (id) => apiFetch(`/clubs/${id}/members`)
        .then(items => items.map(transformMember))
}

// ============================================================================
// Groups API
// ============================================================================

export const groupsApi = {
    list: (clubId = null, limit = 50, offset = 0) => {
        const params = new URLSearchParams({ limit, offset })
        if (clubId) params.append('club_id', clubId)
        return apiFetch(`/groups?${params}`)
            .then(items => items.map(transformGroup))
    },

    get: (id) => apiFetch(`/groups/${id}`).then(transformGroup),

    create: (data) => apiFetch('/groups', {
        method: 'POST',
        body: JSON.stringify(data)
    }).then(transformGroup),

    update: (id, data) => apiFetch(`/groups/${id}`, {
        method: 'PATCH',
        body: JSON.stringify(data)
    }).then(transformGroup),

    delete: (id) => apiFetch(`/groups/${id}`, { method: 'DELETE' }),

    join: (id) => apiFetch(`/groups/${id}/join`, { method: 'POST' }),

    getMembers: (id) => apiFetch(`/groups/${id}/members`)
        .then(items => items.map(transformMember))
}

// ============================================================================
// Telegram WebApp helpers
// ============================================================================

export const tg = {
    get webApp() {
        return window.Telegram?.WebApp
    },

    get user() {
        return this.webApp?.initDataUnsafe?.user
    },

    haptic(type = 'medium') {
        this.webApp?.HapticFeedback?.impactOccurred(type)
    },

    showAlert(message) {
        if (this.webApp?.showAlert) {
            this.webApp.showAlert(message)
        } else {
            alert(message)
        }
    },

    showConfirm(message, callback) {
        // Support both callback and Promise
        if (this.webApp?.showConfirm) {
            // Check if version supports it, or just try/catch if possible, 
            // but showConfirm doesn't return promise in older versions usually.
            // However, the error says 'WebAppMethodUnsupported'.
            try {
                this.webApp.showConfirm(message, (confirmed) => {
                    if (callback) callback(confirmed)
                })
            } catch (e) {
                console.warn('Telegram showConfirm failed, falling back to window.confirm', e)
                const confirmed = window.confirm(message)
                if (callback) callback(confirmed)
            }
        } else {
            const confirmed = window.confirm(message)
            if (callback) callback(confirmed)
        }
    },

    close() {
        this.webApp?.close()
    }
}

export default { activitiesApi, clubsApi, groupsApi, usersApi, tg }
