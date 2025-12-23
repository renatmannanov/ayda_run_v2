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
    id: u.id,
    telegramId: u.telegram_id,
    username: u.username,
    firstName: u.first_name,
    lastName: u.last_name,
    country: u.country,
    city: u.city,
    createdAt: u.created_at,
    preferredSports: u.preferred_sports
})

const transformActivity = (a) => !a ? null : ({
    id: a.id,
    title: a.title,
    description: a.description,
    date: a.date,
    location: a.location,
    country: a.country,
    city: a.city,
    sportType: a.sport_type,
    difficulty: a.difficulty,
    distance: a.distance,
    duration: a.duration,
    maxParticipants: a.max_participants,
    visibility: a.visibility,
    status: a.status,
    participants: a.participants_count, // Map count to prop expected by UI
    isJoined: a.is_joined,
    isOpen: a.is_open !== undefined ? a.is_open : true, // Default to open for backwards compatibility
    participationStatus: a.participation_status, // User's participation status (awaiting, attended, missed, etc.)
    canViewParticipants: a.can_view_participants !== undefined ? a.can_view_participants : true,
    canDownloadGpx: a.can_download_gpx !== undefined ? a.can_download_gpx : true,
    // GPX file info
    gpxFileId: a.gpx_file_id,
    gpxFilename: a.gpx_filename,
    hasGpx: a.has_gpx || false,
    isCreator: a.is_creator || false,
    clubId: a.club_id,
    groupId: a.group_id,
    club: a.club_name,
    group: a.group_name,
    creatorId: a.creator_id,
    creatorName: a.creator_name,
    createdAt: a.created_at,
    isPast: new Date(a.date) < new Date(),
    icon: (a.sport_type === 'running' || !a.sport_type) ? '🏃' :
        a.sport_type === 'trail' ? '⛰️' :
            a.sport_type === 'cycling' ? '🚴' :
                a.sport_type === 'hiking' ? '🥾' :
                    a.sport_type === 'yoga' ? '🧘' :
                        a.sport_type === 'workout' ? '💪' : '🏃'
})

const transformClub = (c) => !c ? null : ({
    id: c.id,
    name: c.name,
    description: c.description,
    country: c.country,
    city: c.city,
    photo: c.photo, // Telegram file_id for avatar
    isPaid: c.is_paid,
    pricePerActivity: c.price_per_activity,
    telegramChatId: c.telegram_chat_id,
    createdAt: c.created_at,
    groupsCount: c.groups_count,
    members: c.members_count, // Map count
    isMember: c.is_member,
    isOpen: c.is_open !== undefined ? c.is_open : true, // Default to open for backwards compatibility
    userRole: c.user_role,
    isAdmin: c.user_role === 'admin' || c.user_role === 'organizer'
})

const transformGroup = (g) => !g ? null : ({
    id: g.id,
    name: g.name,
    description: g.description,
    photo: g.photo, // Telegram file_id for avatar
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
    id: m.user_id,
    userId: m.user_id,
    telegramId: m.telegram_id,
    username: m.username,
    firstName: m.first_name,
    name: m.name,
    role: m.role,
    status: m.status, // Participation status (registered, confirmed, awaiting, attended, missed)
    joinedAt: m.joined_at,
    photo: m.photo,
    stravaLink: m.strava_link,
    preferredSports: m.preferred_sports,
    attended: m.attended,
    isOrganizer: m.is_organizer || m.role === 'admin' || m.role === 'organizer'
})


// ============================================================================
// Generic API object (for direct endpoints access)
// ============================================================================

export const api = {
    get: (endpoint) => apiFetch(endpoint),
    post: (endpoint, data) => apiFetch(endpoint, {
        method: 'POST',
        body: JSON.stringify(data)
    }),
    patch: (endpoint, data) => apiFetch(endpoint, {
        method: 'PATCH',
        body: JSON.stringify(data)
    }),
    delete: (endpoint) => apiFetch(endpoint, { method: 'DELETE' })
}

// ============================================================================
// Users API
// ============================================================================

export const usersApi = {
    getMe: () => apiFetch('/users/me').then(transformUser),
    getStats: () => apiFetch('/users/me/stats')
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

    update: (id, data, notifyParticipants = false) => apiFetch(
        `/activities/${id}?notify_participants=${notifyParticipants}`,
        {
            method: 'PATCH',
            body: JSON.stringify(data)
        }
    ).then(transformActivity),

    delete: (id, notifyParticipants = false) => apiFetch(
        `/activities/${id}?notify_participants=${notifyParticipants}`,
        { method: 'DELETE' }
    ),

    join: (id) => apiFetch(`/activities/${id}/join`, { method: 'POST' }),

    leave: (id) => apiFetch(`/activities/${id}/leave`, { method: 'POST' }),

    requestJoin: (id) => apiFetch(`/activities/${id}/request-join`, { method: 'POST' }),

    // Confirm attendance for past activity (attended=true or missed=false)
    confirm: (id, attended) => apiFetch(`/activities/${id}/confirm?attended=${attended}`, { method: 'POST' }),

    getParticipants: (id) => apiFetch(`/activities/${id}/participants`)
        .then(items => items.map(transformMember)),

    // GPX file operations
    uploadGpx: async (activityId, file) => {
        const formData = new FormData()
        formData.append('file', file)

        const headers = {}
        if (window.Telegram?.WebApp?.initData) {
            headers['X-Telegram-Init-Data'] = window.Telegram.WebApp.initData
        }
        // Note: Don't set Content-Type - browser will set it with boundary for FormData

        const response = await fetch(`${API_BASE}/activities/${activityId}/gpx`, {
            method: 'POST',
            headers,
            body: formData
        })

        if (!response.ok) {
            const error = await response.json().catch(() => ({}))
            throw new Error(error.detail || 'Failed to upload GPX file')
        }

        return response.json()
    },

    deleteGpx: (activityId) => apiFetch(`/activities/${activityId}/gpx`, { method: 'DELETE' }),

    getGpxDownloadUrl: (activityId) => `${API_BASE}/activities/${activityId}/gpx`
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

    delete: (id, notifyMembers = false, deleteActivities = true) => apiFetch(
        `/clubs/${id}?notify_members=${notifyMembers}&delete_activities=${deleteActivities}`,
        { method: 'DELETE' }
    ),

    join: (id) => apiFetch(`/clubs/${id}/join`, { method: 'POST' }),

    requestJoin: (id) => apiFetch(`/clubs/${id}/request-join`, { method: 'POST' }),

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

    delete: (id, notifyMembers = false, deleteActivities = true) => apiFetch(
        `/groups/${id}?notify_members=${notifyMembers}&delete_activities=${deleteActivities}`,
        { method: 'DELETE' }
    ),

    join: (id) => apiFetch(`/groups/${id}/join`, { method: 'POST' }),

    requestJoin: (id) => apiFetch(`/groups/${id}/request-join`, { method: 'POST' }),

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

    // Impact feedback: light, medium, heavy, rigid, soft
    haptic(type = 'medium') {
        this.webApp?.HapticFeedback?.impactOccurred(type)
    },

    // Notification feedback: error, success, warning
    hapticNotification(type = 'success') {
        this.webApp?.HapticFeedback?.notificationOccurred(type)
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
