# Formatting, locale detection and fallbacks

## Contents
- Intl API — Runtime Formatting
- Locale Detection Strategy

## Intl API — Runtime Formatting

Use the native `Intl` API for dates, numbers, currency, and relative time. It automatically adapts to the user's locale.

### Date Formatting

```typescript
// Basic
new Intl.DateTimeFormat('de-DE').format(new Date())
// → "13.2.2026"

// With options
new Intl.DateTimeFormat('ja-JP', {
  year: 'numeric', month: 'long', day: 'numeric', weekday: 'long'
}).format(new Date())
// → "2026年2月13日金曜日"

// next-intl shortcut:
import { useFormatter } from 'next-intl';
const format = useFormatter();
format.dateTime(new Date(), { dateStyle: 'full' });
```

### Number Formatting

```typescript
new Intl.NumberFormat('de-DE').format(1234567.89)
// → "1.234.567,89"

new Intl.NumberFormat('en-US', {
  style: 'currency', currency: 'USD'
}).format(29.99)
// → "$29.99"

new Intl.NumberFormat('ja-JP', {
  style: 'currency', currency: 'JPY'
}).format(2999)
// → "￥2,999"

new Intl.NumberFormat('en', {
  style: 'percent', minimumFractionDigits: 1
}).format(0.856)
// → "85.6%"

new Intl.NumberFormat('en', {
  notation: 'compact', compactDisplay: 'short'
}).format(1500000)
// → "1.5M"
```

### Relative Time

```typescript
const rtf = new Intl.RelativeTimeFormat('ru', { numeric: 'auto' });
rtf.format(-1, 'day')    // → "вчера"
rtf.format(3, 'hour')    // → "через 3 часа"
rtf.format(-2, 'month')  // → "2 месяца назад"
```

### List Formatting

```typescript
new Intl.ListFormat('en', { type: 'conjunction' }).format(['Red', 'Green', 'Blue'])
// → "Red, Green, and Blue"

new Intl.ListFormat('zh', { type: 'conjunction' }).format(['红', '绿', '蓝'])
// → "红、绿和蓝"
```

## Locale Detection Strategy

Recommended priority chain for detecting user locale:

```
1. URL path/param (/es/about)     → Highest priority, explicit choice
2. Cookie (NEXT_LOCALE)           → Remembered preference
3. User profile setting           → Logged-in user preference
4. Accept-Language header         → Browser/OS language
5. IP geolocation                 → Rough guess (least reliable)
6. Default locale (en)            → Fallback
```

### Implementation Pattern

```typescript
function detectLocale(request: Request, supportedLocales: string[]): string {
  // 1. URL param (handled by routing middleware)

  // 2. Cookie
  const cookieLocale = getCookie(request, 'NEXT_LOCALE');
  if (cookieLocale && supportedLocales.includes(cookieLocale)) return cookieLocale;

  // 3. Accept-Language header
  const acceptLang = request.headers.get('accept-language');
  if (acceptLang) {
    const matched = matchLocale(acceptLang, supportedLocales);
    if (matched) return matched;
  }

  // 4. Fallback
  return 'en';
}
```

### Fallback Behavior

When a translation is missing for the user's locale:
1. Try regional fallback: `es-MX` → `es` → `en`
2. Show source language string (better than empty)
3. Log missing translation for developer review
4. Never show raw translation keys to users
