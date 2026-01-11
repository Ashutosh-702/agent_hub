# Agent Hub Design System

A comprehensive design system for the Agent Hub frontend application. This document serves as the single source of truth for all UI/UX decisions.

---

## Table of Contents

1. [Design Principles](#design-principles)
2. [Color System](#color-system)
3. [Typography](#typography)
4. [Spacing](#spacing)
5. [Border Radius](#border-radius)
6. [Shadows](#shadows)
7. [Transitions](#transitions)
8. [Components](#components)
9. [Layout Patterns](#layout-patterns)
10. [Icons](#icons)
11. [Best Practices](#best-practices)

---

## Design Principles

### Core Values

1. **Clean & Professional** - Minimal visual noise, muted colors, clear hierarchy
2. **Consistent** - Reuse patterns, tokens, and components across all features
3. **Accessible** - WCAG 2.1 AA compliant, keyboard navigable, proper focus states
4. **Performant** - CSS variables, minimal animations, efficient renders

### Visual Guidelines

- **No emojis in professional UI** - Use icons or badges instead
- **Muted color palette** - Avoid saturated colors; prefer grays with subtle accents
- **Clear hierarchy** - Use typography weight and size, not color, for emphasis
- **Generous whitespace** - Let content breathe; avoid cramped layouts
- **Subtle interactions** - Hover states should be visible but not distracting

---

## Color System

All colors are defined as CSS custom properties in `App.css`.

### Primary Colors (Fynd Blue)

| Variable | Value | Usage |
|----------|-------|-------|
| `--color-primary` | `#2E31BE` | Primary buttons, links, active states |
| `--color-primary-hover` | `#2628A1` | Hover states for primary elements |
| `--color-primary-light` | `rgba(46, 49, 190, 0.08)` | Light backgrounds, selected states |
| `--color-primary-lighter` | `rgba(46, 49, 190, 0.04)` | Very subtle highlights |

### Neutral Colors (Grays)

| Variable | Value | Usage |
|----------|-------|-------|
| `--color-white` | `#FFFFFF` | Backgrounds, cards |
| `--color-gray-50` | `#F5F7FA` | Page backgrounds |
| `--color-gray-100` | `#EDF0F5` | Subtle dividers, hover states |
| `--color-gray-200` | `#E4E7ED` | Borders, dividers |
| `--color-gray-300` | `#D4D8E1` | Input borders |
| `--color-gray-400` | `#9CA3AF` | Placeholder text, muted icons |
| `--color-gray-500` | `#6B7280` | Secondary text |
| `--color-gray-600` | `#4B5563` | Body text |
| `--color-gray-700` | `#374151` | Strong text |
| `--color-gray-800` | `#1F2937` | Headings |
| `--color-gray-900` | `#111827` | Primary text, titles |

### Status Colors

| Variable | Value | Usage |
|----------|-------|-------|
| `--color-success` | `#0CA678` | Success states, positive metrics |
| `--color-success-light` | `rgba(12, 166, 120, 0.1)` | Success backgrounds |
| `--color-warning` | `#F59E0B` | Warnings, attention needed |
| `--color-warning-light` | `rgba(245, 158, 11, 0.1)` | Warning backgrounds |
| `--color-error` | `#DC2626` | Errors, destructive actions |
| `--color-error-light` | `rgba(220, 38, 38, 0.1)` | Error backgrounds |
| `--color-info` | `#3B82F6` | Information, tips |
| `--color-info-light` | `rgba(59, 130, 246, 0.1)` | Info backgrounds |

### Sidebar Colors (Dark Theme)

| Variable | Value | Usage |
|----------|-------|-------|
| `--sidebar-bg` | `#1A1D2E` | Sidebar background |
| `--sidebar-hover` | `rgba(255, 255, 255, 0.06)` | Hover state |
| `--sidebar-active` | `rgba(46, 49, 190, 0.2)` | Active nav item |
| `--sidebar-text` | `rgba(255, 255, 255, 0.7)` | Default text |
| `--sidebar-text-active` | `#FFFFFF` | Active text |
| `--sidebar-border` | `rgba(255, 255, 255, 0.08)` | Dividers |

### Dashboard-Specific Colors

For metric cards and dashboards, use a restrained palette:

```css
--metric-primary: #374151;   /* Default metric accent */
--metric-hot: #b91c1c;       /* Hot leads, urgent */
--metric-warning: #d97706;   /* Warnings, attention */
--metric-success: #059669;   /* Positive trends */
```

---

## Typography

### Font Family

```css
--font-family: 'Figtree', 'DM Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
--font-mono: 'SF Mono', 'Monaco', 'Consolas', monospace;
```

**Figtree** is the primary font. Load via Google Fonts:

```css
@import url('https://fonts.googleapis.com/css2?family=Figtree:wght@400;500;600;700&display=swap');
```

### Font Sizes

| Variable | Value | Usage |
|----------|-------|-------|
| `--text-xs` | `0.75rem` (12px) | Labels, badges, captions |
| `--text-sm` | `0.875rem` (14px) | Body text, buttons, inputs |
| `--text-base` | `1rem` (16px) | Default body text |
| `--text-lg` | `1.125rem` (18px) | Subheadings |
| `--text-xl` | `1.25rem` (20px) | Section titles |
| `--text-2xl` | `1.5rem` (24px) | Page titles |
| `--text-3xl` | `1.875rem` (30px) | Large headings |

### Font Weights

- **400** - Regular body text
- **500** - Medium emphasis, buttons
- **600** - Semibold, subheadings
- **700** - Bold, titles and headings

### Typography Patterns

```css
/* Page title */
font-size: var(--text-2xl);
font-weight: 700;
color: var(--color-gray-900);
letter-spacing: -0.02em;

/* Section heading */
font-size: var(--text-lg);
font-weight: 600;
color: var(--color-gray-800);

/* Body text */
font-size: var(--text-sm);
font-weight: 400;
color: var(--color-gray-600);
line-height: 1.5;

/* Label (uppercase) */
font-size: var(--text-xs);
font-weight: 600;
color: var(--color-gray-500);
text-transform: uppercase;
letter-spacing: 0.04em;

/* Monospace (IDs, codes) */
font-family: var(--font-mono);
font-size: var(--text-sm);
color: var(--color-primary);
```

---

## Spacing

Use consistent spacing tokens. Never use arbitrary pixel values.

| Variable | Value | Usage |
|----------|-------|-------|
| `--space-1` | `0.25rem` (4px) | Tight spacing, inline elements |
| `--space-2` | `0.5rem` (8px) | Small gaps |
| `--space-3` | `0.75rem` (12px) | Button padding, list gaps |
| `--space-4` | `1rem` (16px) | Standard spacing |
| `--space-5` | `1.25rem` (20px) | Card padding |
| `--space-6` | `1.5rem` (24px) | Section gaps |
| `--space-8` | `2rem` (32px) | Large sections |
| `--space-10` | `2.5rem` (40px) | Page padding |
| `--space-12` | `3rem` (48px) | Extra large gaps |

### Spacing Guidelines

- **Card padding**: `--space-5` or `--space-6`
- **Button padding**: `--space-3 --space-4` (vertical horizontal)
- **Input padding**: `--space-3 --space-4`
- **List item gaps**: `--space-2` to `--space-3`
- **Section margins**: `--space-6` to `--space-8`
- **Page padding**: `--space-8`

---

## Border Radius

| Variable | Value | Usage |
|----------|-------|-------|
| `--radius-sm` | `4px` | Small badges, tags |
| `--radius-md` | `8px` | Buttons, inputs, dropdowns |
| `--radius-lg` | `12px` | Cards, modals |
| `--radius-xl` | `16px` | Large cards, panels |

---

## Shadows

| Variable | Value | Usage |
|----------|-------|-------|
| `--shadow-sm` | `0 1px 2px rgba(0, 0, 0, 0.04)` | Subtle elevation |
| `--shadow-md` | `0 4px 12px rgba(0, 0, 0, 0.06)` | Cards, dropdowns |
| `--shadow-lg` | `0 8px 24px rgba(0, 0, 0, 0.08)` | Modals, overlays |
| `--shadow-card` | `0 1px 3px rgba(0, 0, 0, 0.05), 0 4px 12px rgba(0, 0, 0, 0.04)` | Default card shadow |

---

## Transitions

| Variable | Value | Usage |
|----------|-------|-------|
| `--transition-fast` | `150ms ease` | Hover states, micro-interactions |
| `--transition-base` | `200ms ease` | Default transitions |
| `--transition-slow` | `300ms ease` | Larger animations, modals |

---

## Components

### Shared Components (`/components/shared/`)

| Component | Description |
|-----------|-------------|
| `BackButton` | Navigation back button |
| `Card` | Container with border and shadow |
| `DataTable` | Sortable data table |
| `EmptyState` | Empty state with icon and CTA |
| `ErrorBanner` | Error message with retry |
| `InfoGrid` | Label-value grid display |
| `Loader` | Loading spinner |
| `PageHeader` | Page title with actions |
| `Pagination` | Page navigation |
| `SearchBar` | Search input with button |
| `StatusBadge` | Status indicator badge |

### Component Patterns

#### Buttons

```css
/* Primary button */
.btn-primary {
  padding: var(--space-3) var(--space-4);
  font-size: var(--text-sm);
  font-weight: 600;
  background: var(--color-primary);
  color: var(--color-white);
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn-primary:hover {
  background: var(--color-primary-hover);
}

/* Secondary button */
.btn-secondary {
  background: var(--color-white);
  color: var(--color-gray-700);
  border: 1px solid var(--color-gray-300);
}

/* Outlined button */
.btn-outlined {
  background: transparent;
  color: var(--color-primary);
  border: 1px solid var(--color-primary);
}
```

#### Cards

```css
.card {
  background: var(--color-white);
  border: 1px solid var(--color-gray-200);
  border-radius: var(--radius-lg);
  padding: var(--space-5);
  box-shadow: var(--shadow-card);
}
```

#### Form Inputs

```css
.input {
  padding: var(--space-3) var(--space-4);
  font-size: var(--text-sm);
  font-family: var(--font-family);
  border: 1px solid var(--color-gray-300);
  border-radius: var(--radius-md);
  background: var(--color-white);
  color: var(--color-gray-800);
  transition: all var(--transition-fast);
}

.input:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-light);
}
```

#### Status Badges

```css
.badge {
  display: inline-block;
  padding: var(--space-1) var(--space-3);
  border-radius: var(--radius-sm);
  font-size: var(--text-xs);
  font-weight: 600;
}

.badge-success {
  background: var(--color-success-light);
  color: var(--color-success);
}

.badge-warning {
  background: var(--color-warning-light);
  color: var(--color-warning);
}

.badge-error {
  background: var(--color-error-light);
  color: var(--color-error);
}
```

---

## Layout Patterns

### Page Layout

```
┌─────────────────────────────────────────────────────┐
│ Sidebar │           Main Content                    │
│  260px  │                                           │
│         │ ┌───────────────────────────────────────┐ │
│         │ │ Page Header                           │ │
│         │ ├───────────────────────────────────────┤ │
│         │ │                                       │ │
│         │ │ Content Area                          │ │
│         │ │                                       │ │
│         │ └───────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

### Split Pane (Inbox)

```
┌───────────────────────────────────────────────────────┐
│ Header + Tabs + Filters                               │
├───────────────┬───────────────────────────────────────┤
│ List Pane     │ Detail Pane                           │
│ (380px fixed) │ (flex: 1)                             │
│               │                                       │
│ Scrollable    │ Scrollable                            │
└───────────────┴───────────────────────────────────────┘
```

### Dashboard Grid

```
┌─────────────────────────────────────────────────────────┐
│ Header: Title + Actions + Period Selector               │
├─────────────────────────────────────────────────────────┤
│ Metrics Row: 4 cards (grid-template-columns: repeat(4)) │
├─────────────────────────────────────────────────────────┤
│ ┌─────────────────────┐ ┌─────────────────────────────┐ │
│ │ AI Insights         │ │ Charts Column               │ │
│ │ (Recommendations)   │ │ - Funnel                    │ │
│ │                     │ │ - Channel Performance       │ │
│ └─────────────────────┘ └─────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

---

## Icons

### SVG Icon Guidelines

- **Size**: 20x20px for navigation, 16x16px for inline
- **Stroke**: 2px stroke width
- **Style**: Line icons, not filled
- **Color**: `currentColor` to inherit text color

### Icon Pattern

```tsx
const Icon = (
  <svg 
    width="20" 
    height="20" 
    viewBox="0 0 24 24" 
    fill="none" 
    stroke="currentColor" 
    strokeWidth="2" 
    strokeLinecap="round" 
    strokeLinejoin="round"
  >
    {/* paths */}
  </svg>
);
```

### Common Icons (defined in Sidebar.tsx)

- `masterData` - Grid layout
- `campaign` - Document
- `companies` - Building
- `prospecting` - Target
- `inbox` - Mail tray
- `hubspot` - HubSpot logo
- `chevronRight` - Expand indicator

---

## Best Practices

### Do's

1. **Use CSS variables** - Never hardcode colors or spacing
2. **Use semantic colors** - `--color-error` not `#DC2626`
3. **Maintain consistency** - Same patterns across all pages
4. **Focus states** - Always visible, use `--color-primary` outline
5. **Loading states** - Show skeletons or spinners, never blank
6. **Error handling** - Clear error messages with retry actions
7. **Responsive design** - Test at 768px, 1024px breakpoints

### Don'ts

1. **No emojis** in professional UI (use icons)
2. **No saturated colors** - Keep it muted and professional
3. **No arbitrary values** - Use spacing and color tokens
4. **No inline styles** for reusable patterns - Use CSS classes
5. **No deep nesting** - Keep component hierarchy flat
6. **No color-only indicators** - Always pair with text/icons for accessibility

### Accessibility Checklist

- [ ] Keyboard navigable (Tab, Enter, Escape)
- [ ] Focus states visible
- [ ] Color contrast 4.5:1 minimum
- [ ] Screen reader labels (aria-label)
- [ ] No color-only information
- [ ] Touch targets 44x44px minimum

---

## File Structure

```
ui/src/
├── App.css                 # Global styles, CSS variables
├── components/
│   ├── shared/             # Reusable components
│   │   ├── BackButton.tsx
│   │   ├── Card.tsx
│   │   ├── DataTable.tsx
│   │   ├── EmptyState.tsx
│   │   ├── ErrorBanner.tsx
│   │   ├── InfoGrid.tsx
│   │   ├── Loader.tsx
│   │   ├── PageHeader.tsx
│   │   ├── Pagination.tsx
│   │   ├── SearchBar.tsx
│   │   ├── StatusBadge.tsx
│   │   └── index.ts
│   ├── inbox/              # Inbox feature
│   │   ├── InboxDashboard.tsx
│   │   ├── InboxDashboard.css
│   │   ├── InboxPage.tsx
│   │   ├── InboxPage.css
│   │   └── ...
│   └── ...
├── services/               # API services
├── types/                  # TypeScript types
└── context/                # React context providers
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-02 | Initial design system documentation |

---

*This design system is a living document. Update it as new patterns emerge.*


