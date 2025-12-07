# Design System

UI/UX guidelines for minimalist Telegram Mini Apps.

---

## Philosophy

**Less is more** - Clean, focused, professional.

### Principles
1. **Minimalism** - Remove unnecessary elements
2. **Clarity** - Clear hierarchy
3. **Consistency** - Predictable patterns
4. **Accessibility** - Readable, touchable (44px min)
5. **Performance** - Fast, lightweight

---

## Colors

### Gray Scale (Foundation)
```css
--gray-200: #e5e7eb;  /* Borders */
--gray-400: #9ca3af;  /* Muted text */
--gray-500: #6b7280;  /* Secondary text */
--gray-700: #374151;  /* Labels */
--gray-800: #1f2937;  /* Primary text */
--gray-900: #111827;  /* Strong emphasis */
```

### Accents
```css
--orange-500: #f97316;  /* Focus */
--green-600: #16a34a;   /* Success */
--amber-600: #d97706;   /* Warning */
```

**TODO**: Add brand colors
```css
--primary-500: #3b82f6;
--secondary-500: #8b5cf6;
```

---

## Typography

### Font Stack
System fonts for native feel:
```css
font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
```

### Sizes
```css
--text-xs: 0.75rem;   /* 12px - tiny labels */
--text-sm: 0.875rem;  /* 14px - buttons */
--text-base: 1rem;    /* 16px - body */
--text-lg: 1.125rem;  /* 18px - headings */
```

### Weights
- Normal: `400`
- Medium: `500` (active, emphasis)
- Semi-bold: `600` (headings)

---

## Layout

### Container
```css
.app {
    max-width: 28rem;  /* 448px mobile-first */
    margin: 0 auto;
}
```

### Spacing
```css
padding: 0.75rem 1rem;  /* Header, actions */
padding: 1rem;          /* Body, cards */
gap: 0.5rem;            /* Related items */
```

---

## Components

### Buttons

**Text (Primary)**:
```css
.btn-text {
    background: none;
    color: var(--gray-500);
}
```

**Filled (CTA)**:
```css
.btn-primary {
    background: var(--gray-900);
    color: white;
}
```

### Cards
```css
.card {
    border: 1px solid var(--border);
    border-radius: 0.5rem;
    padding: 1rem;
}
```

### Empty State
```html
<div class="empty-state">
    <div class="empty-icon">✓</div>
    <div class="empty-title">Title</div>
    <div class="empty-subtitle">Subtitle</div>
</div>
```

**Design**: Centered, large emoji (1.875rem), positive tone

---

## Interactions

### Hover
```css
button:hover {
    color: var(--gray-700);
}
```

### Active
```css
.toggle-btn.active {
    color: var(--gray-900);
    font-weight: 500;
}
```

### Transitions
```css
transition: color 0.2s;  /* Keep under 300ms */
```

---

## Patterns

### Toggle Buttons
```html
<button class="toggle-btn active">All</button>
<span class="toggle-separator">/</span>
<button class="toggle-btn">Focus</button>
```
Design: Text-only, separator character, no background

### Metadata
```html
<div class="card-meta">
    <div class="card-tags">
        <button class="card-tag">#tag1</button>
    </div>
    <button class="card-date">28 Nov 2025</button>
</div>
```
Design: Gray-500, small text (0.875rem), all clickable

---

## Responsive

**Mobile First**:
```css
.app {
    max-width: 28rem;
}

@media (max-width: 448px) {
    .app {
        border-left: none;
        border-right: none;
    }
}
```

---

## Accessibility

**Touch Targets**: 44px minimum
```css
button {
    min-height: 44px;
}
```

**Contrast**:
- Primary text: `--gray-800` (✓ AAA)
- Secondary: `--gray-500` (✓ AA)

**Focus**:
```css
button:focus-visible {
    outline: 2px solid var(--orange-500);
}
```

---

## Dark Mode (Optional)

Use Telegram theme colors:
```css
body {
    background: var(--tg-theme-bg-color);
    color: var(--tg-theme-text-color);
}
```

---

## Summary

✅ **DO**:
- Use gray-scale foundation
- Leverage white space
- 44px+ touch targets
- Maintain consistency

❌ **DON'T**:
- Overuse colors
- Add unnecessary animations
- Mix patterns
- Clutter interface

---

**Remember**: Every element should serve a purpose. Function over decoration.
