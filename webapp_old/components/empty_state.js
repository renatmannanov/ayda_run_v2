/**
 * Empty State Component
 * 
 * Display an empty state with icon, title, and subtitle.
 * 
 * @param {Object} props - Component props
 * @param {string} props.icon - Emoji or icon
 * @param {string} props.title - Title text
 * @param {string} [props.subtitle] - Subtitle text (optional)
 * @returns {string} HTML string
 */
export function EmptyState({ icon, title, subtitle = '' }) {
    return `
        <div class="empty-state">
            <div class="empty-icon">${icon}</div>
            <div class="empty-title">${title}</div>
            ${subtitle ? `<div class="empty-subtitle">${subtitle}</div>` : ''}
        </div>
    `;
}
