/**
 * Card Component
 * 
 * Reusable card component for displaying content.
 * 
 * @param {Object} props - Component props
 * @param {string} props.title - Card title
 * @param {string} props.content - Card content
 * @param {string} [props.className] - Additional CSS classes
 * @returns {string} HTML string
 */
export function Card({ title, content, className = '' }) {
    const escapedTitle = escapeHtml(title);
    const escapedContent = escapeHtml(content);

    return `
        <div class="card ${className}">
            ${title ? `<h3 class="card-title">${escapedTitle}</h3>` : ''}
            <p class="card-text">${escapedContent}</p>
        </div>
    `;
}

/**
 * Helper to escape HTML
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text || '';
    return div.innerHTML;
}
