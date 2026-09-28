# Extracting strings and avoiding i18n bugs

## Contents
- Migration Guide: Hardcoded English → i18n
- Common i18n Mistakes
- Email Template Localization

## Migration Guide: Hardcoded English → i18n

Step-by-step process to internationalize an existing app.

### Phase 1: Audit

1. Scan all components for user-facing strings
2. Identify string categories: UI labels, error messages, validation, emails, dates
3. Note dynamic strings with variables: `Welcome, ${name}`
4. Check for string concatenation (needs refactoring)
5. Count total strings to estimate effort

### Phase 2: Infrastructure

1. Install i18n library (next-intl, react-i18next, etc.)
2. Create locale directory structure
3. Set up routing/middleware if needed
4. Add provider to root layout/component

### Phase 3: Extract Strings

Replace hardcoded strings with translation keys:

```typescript
// BEFORE:
<h1>Welcome to our platform</h1>
<p>You have {count} new messages</p>
<button>Save changes</button>
{error && <span>Something went wrong. Please try again.</span>}

// AFTER:
<h1>{t('dashboard.welcome')}</h1>
<p>{t('dashboard.newMessages', { count })}</p>
<button>{t('common.save')}</button>
{error && <span>{t('errors.generic')}</span>}
```

### Phase 4: Create Source Locale File

```json
{
  "dashboard": {
    "welcome": "Welcome to our platform",
    "newMessages": "{count, plural, one {You have # new message} other {You have # new messages}}"
  },
  "common": {
    "save": "Save changes",
    "cancel": "Cancel",
    "delete": "Delete"
  },
  "errors": {
    "generic": "Something went wrong. Please try again."
  }
}
```

### Phase 5: Translate

Follow the translate-and-verify loop in SKILL.md (`translation_state.py todo` → translate → `check_locales.py` → `mark`), or the Lingo.dev CLI if the user opted into it ([lingo.md](lingo.md)).

### Phase 6: SEO & Metadata

Add hreflang tags, localized metadata and a sitemap ([seo.md](seo.md)).

## Common i18n Mistakes

### String Concatenation (NEVER do this)

```typescript
// ❌ BROKEN — word order differs across languages:
const msg = "Welcome, " + name + "! You have " + count + " items.";

// ✅ CORRECT — use interpolation:
const msg = t('welcome', { name, count });
// "Welcome, {name}! You have {count} items."
```

### Split Sentences

```typescript
// ❌ BROKEN — sentence structure varies by language:
<p>{t('click')} <a href="/terms">{t('here')}</a> {t('toAgree')}</p>

// ✅ CORRECT — keep full sentence together:
<p>
  <Trans i18nKey="agreeToTerms">
    Click <a href="/terms">here</a> to agree to our terms.
  </Trans>
</p>
```

### Hardcoded Plurals

```typescript
// ❌ BROKEN — English-only plural logic:
const text = count === 1 ? "1 item" : `${count} items`;

// ✅ CORRECT — use ICU plural format:
// "{count, plural, one {# item} other {# items}}"
```

### Assuming Text Direction

```css
/* ❌ BROKEN — fails for RTL: */
margin-left: 16px;
text-align: left;

/* ✅ CORRECT — logical properties: */
margin-inline-start: 16px;
text-align: start;
```

### Hardcoded Date/Number Formats

```typescript
// ❌ BROKEN — US format hardcoded:
const dateStr = `${month}/${day}/${year}`;

// ✅ CORRECT — use Intl API:
new Intl.DateTimeFormat(locale).format(date);
```

### Translating Inside Code Logic

```typescript
// ❌ BROKEN — translated string used as logic key:
if (status === t('active')) { ... }

// ✅ CORRECT — use locale-independent identifiers:
if (status === 'active') { ... }
// Display: t(`status.${status}`)
```

## Email Template Localization

Emails are rendered outside React, so use the library's standalone translator with the recipient's stored locale — never the locale of whoever triggered the send. Keep the text in message files like the UI, so the same checks and review apply.

```json
// messages/en.json
{
  "emails": {
    "welcome": {
      "subject": "Welcome to {appName}!",
      "body": "Hi {name}, thanks for joining {appName}."
    }
  }
}
```

```typescript
// next-intl / ICU messages
import { createTranslator } from 'next-intl';

export async function welcomeEmail(user: { name: string; locale: string }) {
  const messages = (await import(`../messages/${user.locale}.json`)).default;
  const t = createTranslator({ locale: user.locale, messages, namespace: 'emails.welcome' });
  return {
    subject: t('subject', { appName: 'Acme' }),
    body: t('body', { name: user.name, appName: 'Acme' }),
  };
}

// i18next: const t = i18next.getFixedT(user.locale, 'emails');
```

### Best Practices
- Store each user's locale when they sign up or change it; background jobs have no request to detect it from
- Date/time in emails: include the time zone and format for the recipient's locale
- Localize the unsubscribe link text (required by law in many countries)
- Test rendering in real email clients for RTL and long-word languages
