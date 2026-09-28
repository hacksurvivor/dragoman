# Next.js with next-intl

Default for Next.js App Router: locale routing, middleware, Server Component support. Messages use ICU syntax, so check them with `check_locales.py "messages/[locale].json"`. Metadata, hreflang, sitemaps and OG images: see [seo.md](seo.md).

## Contents
- Installation
- File Structure
- Step-by-Step Setup
- next-intl Language Switcher
- Localized Pathnames
- Lazy loading messages
- Troubleshooting

## Installation

```bash
npm install next-intl
```

## File Structure

```
project/
├── messages/
│   ├── en.json
│   ├── es.json
│   └── fr.json
├── src/
│   ├── i18n/
│   │   ├── routing.ts      # Locale + routing config
│   │   └── request.ts      # Server-side locale resolution
│   ├── proxy.ts             # Locale negotiation middleware
│   └── app/
│       └── [locale]/
│           ├── layout.tsx   # Root layout with NextIntlClientProvider
│           └── page.tsx
└── next.config.ts
```

## Step-by-Step Setup

**1. Routing configuration:**

```typescript
// src/i18n/routing.ts
import { defineRouting } from 'next-intl/routing';
import { createNavigation } from 'next-intl/navigation';

export const routing = defineRouting({
  locales: ['en', 'es', 'fr', 'de', 'ru', 'zh', 'ja'],
  defaultLocale: 'en',
  localePrefix: 'as-needed'  // No prefix for default locale
});

export const { Link, redirect, usePathname, useRouter, getPathname } =
  createNavigation(routing);
```

**2. Middleware (proxy):**

```typescript
// src/proxy.ts  (called middleware.ts before Next.js 16)
import createMiddleware from 'next-intl/middleware';
import { routing } from './i18n/routing';

export default createMiddleware(routing);

export const config = {
  matcher: ['/((?!api|trpc|_next|_vercel|.*\\..*).*)'
]
};
```

**3. Request configuration:**

```typescript
// src/i18n/request.ts
import { getRequestConfig } from 'next-intl/server';
import { routing } from './routing';

export default getRequestConfig(async ({ requestLocale }) => {
  let locale = await requestLocale;
  if (!locale || !routing.locales.includes(locale as any)) {
    locale = routing.defaultLocale;
  }
  return {
    locale,
    messages: (await import(`../../messages/${locale}.json`)).default
  };
});
```

**4. Next.js config:**

```typescript
// next.config.ts
import createNextIntlPlugin from 'next-intl/plugin';
const withNextIntl = createNextIntlPlugin('./src/i18n/request.ts');

const nextConfig = {};
export default withNextIntl(nextConfig);
```

**5. Root layout:**

```typescript
// src/app/[locale]/layout.tsx
import { NextIntlClientProvider } from 'next-intl';
import { getMessages, setRequestLocale } from 'next-intl/server';
import { routing } from '@/i18n/routing';
import { notFound } from 'next/navigation';

export function generateStaticParams() {
  return routing.locales.map((locale) => ({ locale }));
}

export default async function LocaleLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  if (!routing.locales.includes(locale as any)) notFound();

  setRequestLocale(locale);
  const messages = await getMessages();

  return (
    <html lang={locale}>
      <body>
        <NextIntlClientProvider messages={messages}>
          {children}
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
```

**6. Using translations:**

```typescript
// Async Server Component — hooks are not allowed here, use the awaitable API
import { getTranslations, setRequestLocale } from 'next-intl/server';

export default async function HomePage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations('HomePage');

  return <h1>{t('title')}</h1>;
}

// Non-async Server Component — the hook works
import { useTranslations } from 'next-intl';

export function Hero() {
  const t = useTranslations('HomePage');
  return <p>{t('description', { purpose: 'teams' })}</p>;
}

// Client Component
'use client';
import { useTranslations } from 'next-intl';

export function MyComponent() {
  const t = useTranslations('common');
  return <button>{t('save')}</button>;
}
```

**7. Message files:**

```json
// messages/en.json
{
  "common": {
    "save": "Save",
    "cancel": "Cancel",
    "loading": "Loading..."
  },
  "HomePage": {
    "title": "Welcome to our app",
    "description": "The best tool for {purpose}"
  }
}
```

## next-intl Language Switcher

```typescript
'use client';
import { useLocale } from 'next-intl';
import { useRouter, usePathname } from '@/i18n/routing';

export function LocaleSwitcher() {
  const locale = useLocale();
  const router = useRouter();
  const pathname = usePathname();

  function onChange(newLocale: string) {
    router.replace(pathname, { locale: newLocale });
  }

  return (
    <select value={locale} onChange={(e) => onChange(e.target.value)}>
      <option value="en">English</option>
      <option value="es">Español</option>
      <option value="fr">Français</option>
    </select>
  );
}
```

## Localized Pathnames

```typescript
// src/i18n/routing.ts
export const routing = defineRouting({
  locales: ['en', 'de', 'es'],
  defaultLocale: 'en',
  pathnames: {
    '/about': {
      en: '/about',
      de: '/ueber-uns',
      es: '/sobre-nosotros'
    },
    '/blog/[slug]': {
      en: '/blog/[slug]',
      de: '/blog/[slug]',
      es: '/blog/[slug]'
    }
  }
});
```

## Lazy loading messages

### next-intl (Automatic)

next-intl already lazy-loads per locale via `request.ts` — only the matched locale is imported:

```typescript
// src/i18n/request.ts — this is already lazy
messages: (await import(`../../messages/${locale}.json`)).default
```

For large apps, split by namespace (page-level loading):

```typescript
// Only load messages needed for this page
messages: {
  ...(await import(`../../messages/${locale}/common.json`)).default,
  ...(await import(`../../messages/${locale}/dashboard.json`)).default,
}
```

### File Structure for Split Loading

```
messages/
├── en/
│   ├── common.json       # ~50 strings — nav, buttons, errors
│   ├── auth.json          # Sign in/up flows
│   ├── dashboard.json     # Dashboard page
│   ├── settings.json      # Settings page
│   └── onboarding.json    # Onboarding flow
├── es/
│   ├── common.json
│   ├── auth.json
│   └── ...
```

**Rule of thumb:** Split when total translations exceed ~500 keys or you support 5+ locales. Below that, a single file per locale is fine.

## Troubleshooting

### next-intl Issues

| Problem | Fix |
|---|---|
| "Couldn't find config" | Ensure path in `createNextIntlPlugin()` is correct |
| Hook error in an `async` component | Use `await getTranslations()` from `next-intl/server`; `useTranslations` only works in non-async components |
| Dynamic rendering forced | Add `setRequestLocale(locale)` to all layouts/pages |
| Middleware not running | Check `matcher` config in proxy.ts |
| Client components missing translations | Wrap in `NextIntlClientProvider` with `messages` |
