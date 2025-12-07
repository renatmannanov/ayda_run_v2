// app.js - Main Application Entry Point
import { api } from './api.js';
import { Card } from './components/card.js';
import { Button, ActionButton } from './components/button.js';
import { EmptyState } from './components/empty_state.js';
import { List } from './components/list.js';

// ============================================================================
// Application State
// ============================================================================
const state = {
    userId: null,
    items: [],
    // TODO: Add your application state here
};

// ============================================================================
// Initialization
// ============================================================================
async function init() {
    console.log('Initializing app...');

    // Initialize Telegram WebApp
    api.init();

    // Get user ID
    state.userId = api.getUserId();
    console.log('User ID:', state.userId);

    // TODO: Load initial data
    // await loadData();

    // Render UI
    render();

    // Setup event listeners
    setupEventListeners();

    console.log('App initialized');
}

// ============================================================================
// Data Loading
// ============================================================================
async function loadData() {
    // TODO: Implement your data loading logic
    // Example:
    // try {
    //     const data = await api.fetch(`/api/data?user_id=${state.userId}`);
    //     state.items = data.items;
    //     render();
    // } catch (error) {
    //     api.showAlert('Error loading data');
    //     console.error(error);
    // }
}

// ============================================================================
// UI Rendering
// ============================================================================
function render() {
    const container = document.getElementById('content');

    // Example: Render using components
    if (state.items.length === 0) {
        // Show empty state
        container.innerHTML = EmptyState({
            icon: '🚀',
            title: 'No items yet',
            subtitle: 'Create your first item to get started'
        });
    } else {
        // Render list of items
        container.innerHTML = List({
            items: state.items,
            renderItem: (item) => Card({
                title: item.title,
                content: item.content
            }),
            emptyState: {
                icon: '📋',
                title: 'No items found'
            }
        });
    }

    // TODO: Customize rendering logic for your app
}

// ============================================================================
// Event Handlers
// ============================================================================
function setupEventListeners() {
    // Delegate events from document
    document.addEventListener('click', (e) => {
        // Handle button clicks by data-action
        const action = e.target.dataset.action;
        if (action) {
            handleAction(action, e.target);
        }

        // Handle button clicks by data-handler
        const handler = e.target.dataset.handler;
        if (handler && typeof window[handler] === 'function') {
            window[handler](e.target);
        }
    });
}

function handleAction(action, element) {
    api.haptic('medium');

    // TODO: Implement your action handlers
    switch (action) {
        case 'create':
            console.log('Create action');
            break;
        case 'delete':
            console.log('Delete action');
            break;
        default:
            console.log('Unknown action:', action);
    }
}

// ============================================================================
// Start Application
// ============================================================================
document.addEventListener('DOMContentLoaded', init);
