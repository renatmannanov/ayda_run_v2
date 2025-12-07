/**
 * Button Component
 * 
 * Reusable button component with different variants.
 * 
 * @param {Object} props - Component props
 * @param {string} props.text - Button text
 * @param {string} [props.variant='primary'] - Button variant: 'primary', 'secondary', 'text'
 * @param {string} [props.onClick] - Click handler name (will be set via addEventListener)
 * @param {string} [props.className] - Additional CSS classes
 * @param {string} [props.id] - Button ID
 * @returns {string} HTML string
 */
export function Button({ text, variant = 'primary', onClick, className = '', id = '' }) {
    const variantClass = {
        'primary': 'btn-primary',
        'secondary': 'btn-secondary',
        'text': 'btn-text'
    }[variant] || 'btn-primary';

    const idAttr = id ? `id="${id}"` : '';
    const dataHandler = onClick ? `data-handler="${onClick}"` : '';

    return `
        <button 
            ${idAttr}
            class="btn ${variantClass} ${className}"
            ${dataHandler}
        >
            ${text}
        </button>
    `;
}

/**
 * Action Button (for action bars)
 * 
 * @param {Object} props - Component props  
 * @param {string} props.text - Button text (can include emoji)
 * @param {string} props.action - Action name
 * @param {string} [props.className] - Additional CSS classes
 * @returns {string} HTML string
 */
export function ActionButton({ text, action, className = '' }) {
    return `
        <button 
            class="action-btn ${className}"
            data-action="${action}"
        >
            ${text}
        </button>
    `;
}
