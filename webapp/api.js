// api.js - Telegram WebApp API Wrapper
// This provides a clean interface to interact with Telegram WebApp features

export const api = {
    // Telegram WebApp instance
    tg: window.Telegram.WebApp,

    /**
     * Initialize Telegram WebApp
     * Call this once when your app starts
     */
    init() {
        this.tg.expand();
        this.tg.ready();
        console.log('Telegram WebApp initialized', this.tg.initDataUnsafe);
    },

    /**
     * Get the current user's Telegram ID
     * @returns {number|string} User ID or 'demo' for testing
     */
    getUserId() {
        const urlParams = new URLSearchParams(window.location.search);
        const urlUserId = urlParams.get('user_id');
        return this.tg.initDataUnsafe?.user?.id || urlUserId || 'demo';
    },

    /**
     * Get user information
     * @returns {Object} User object with id, first_name, username, etc.
     */
    getUser() {
        return this.tg.initDataUnsafe?.user || null;
    },

    /**
     * Fetch data from your API
     * @param {string} endpoint - API endpoint (e.g., '/api/data')
     * @param {Object} options - Fetch options
     * @returns {Promise} Response data
     */
    async fetch(endpoint, options = {}) {
        try {
            const response = await fetch(endpoint, {
                ...options,
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers,
                },
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error(`API Error [${endpoint}]:`, error);
            throw error;
        }
    },

    // TODO: Add your project-specific API methods
    // Example:
    // async fetchNotes(userId) {
    //     return this.fetch(`/api/notes?user_id=${userId}`);
    // },

    /**
     * Show a confirmation dialog
     * @param {string} message - Message to display
     * @param {Function} callback - Callback(confirmed: boolean)
     */
    showConfirm(message, callback) {
        this.tg.showConfirm(message, callback);
    },

    /**
     * Show an alert dialog
     * @param {string} message - Message to display
     */
    showAlert(message) {
        this.tg.showAlert(message);
    },

    /**
     * Trigger haptic feedback
     * @param {string} type - 'light', 'medium', 'heavy', 'rigid', 'soft'
     */
    haptic(type = 'medium') {
        if (this.tg.HapticFeedback) {
            this.tg.HapticFeedback.impactOccurred(type);
        }
    },

    /**
     * Close the Mini App
     */
    close() {
        this.tg.close();
    },

    /**
     * Setup main button
     * @param {string} text - Button text
     * @param {Function} onClick - Click handler
     */
    setupMainButton(text, onClick) {
        this.tg.MainButton.setText(text);
        this.tg.MainButton.onClick(onClick);
        this.tg.MainButton.show();
    },

    /**
     * Hide main button
     */
    hideMainButton() {
        this.tg.MainButton.hide();
    },

    /**
     * Setup back button
     * @param {Function} onClick - Click handler
     */
    setupBackButton(onClick) {
        this.tg.BackButton.onClick(onClick);
        this.tg.BackButton.show();
    },

    /**
     * Hide back button
     */
    hideBackButton() {
        this.tg.BackButton.hide();
    }
};
