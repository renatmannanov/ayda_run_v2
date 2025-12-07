/**
 * List Component
 * 
 * Render a list of items using a render function.
 * 
 * @param {Object} props - Component props
 * @param {Array} props.items - Array of items to render
 * @param {Function} props.renderItem - Function to render each item
 * @param {string} [props.className] - Additional CSS classes
 * @param {Object} [props.emptyState] - Empty state config { icon, title, subtitle }
 * @returns {string} HTML string
 */
export function List({ items, renderItem, className = '', emptyState = null }) {
    if (!items || items.length === 0) {
        if (emptyState) {
            return `
                <div class="empty-state">
                    <div class="empty-icon">${emptyState.icon}</div>
                    <div class="empty-title">${emptyState.title}</div>
                    ${emptyState.subtitle ? `<div class="empty-subtitle">${emptyState.subtitle}</div>` : ''}
                </div>
            `;
        }
        return '<div>No items</div>';
    }

    return `
        <div class="list ${className}">
            ${items.map(renderItem).join('')}
        </div>
    `;
}
