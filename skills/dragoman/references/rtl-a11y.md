# RTL layout and accessibility

## RTL (Right-to-Left) Layout

For Arabic (`ar`), Hebrew (`he`), Farsi (`fa`), Urdu (`ur`).

### HTML Setup

```html
<html lang="ar" dir="rtl">
```

### CSS Logical Properties (Use Instead of Physical)

| Physical (Don't use) | Logical (Use this) |
|---|---|
| `margin-left` | `margin-inline-start` |
| `margin-right` | `margin-inline-end` |
| `padding-left` | `padding-inline-start` |
| `padding-right` | `padding-inline-end` |
| `text-align: left` | `text-align: start` |
| `text-align: right` | `text-align: end` |
| `float: left` | `float: inline-start` |
| `border-left` | `border-inline-start` |
| `left: 0` | `inset-inline-start: 0` |
| `right: 0` | `inset-inline-end: 0` |

### Flexbox Auto-Flips

```css
/* Flexbox and Grid automatically reverse in RTL: */
.container {
  display: flex;
  flex-direction: row; /* LTR: left→right, RTL: right→left */
  gap: 1rem;
}
```

### Icons That Need Flipping

Directional icons must mirror in RTL:
- Back arrows (←) → (→)
- Forward arrows (→) → (←)
- Progress bars
- Breadcrumbs
- Navigation chevrons

Icons that do NOT flip: checkmarks, play/pause, clocks, search, social media logos.

```css
[dir="rtl"] .icon-directional {
  transform: scaleX(-1);
}
```

## Accessibility + i18n

### lang Attribute (Critical for Screen Readers)

```html
<!-- Root document language -->
<html lang="fr">

<!-- Inline language switch for mixed-language content -->
<p>The French word <span lang="fr">bonjour</span> means hello.</p>
```

Screen readers switch pronunciation engine based on `lang`.

### aria-label Localization

```tsx
// ❌ Forgot to localize:
<button aria-label="Close">×</button>

// ✅ Correct:
<button aria-label={t('common.close')}>×</button>
```

### Text Expansion + Dynamic Type

- Test with largest accessibility text sizes
- German text at 130% + large Dynamic Type can overflow
- Use flexible layouts (no fixed widths for text containers)
