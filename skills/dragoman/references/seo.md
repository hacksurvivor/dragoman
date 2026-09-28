# Multilingual SEO

## Contents
- hreflang Tags and Canonical URLs
- Manual hreflang (HTML head)
- Localized Sitemap
- Localized Open Graph Images

## hreflang Tags and Canonical URLs

Canonical and hreflang URLs are **per page**, so build them in each page's `generateMetadata` — never in the layout. A page that doesn't set its own `alternates` inherits the layout's, so every such page would declare the layout URL (usually the home page) as its canonical and drop out of search results.

Use next-intl's `getPathname` so the URLs follow your `localePrefix` and localized `pathnames` settings:

```typescript
// src/i18n/metadata.ts — canonical + hreflang for one page
import type { Metadata } from 'next';
import { routing, getPathname } from './routing';

const host = 'https://example.com';

type Href = Parameters<typeof getPathname>[0]['href'];

export function getAlternates(locale: string, href: Href): Metadata['alternates'] {
  const url = (l: string) => host + getPathname({ locale: l, href });
  return {
    canonical: url(locale),
    languages: {
      ...Object.fromEntries(routing.locales.map((l) => [l, url(l)])),
      'x-default': url(routing.defaultLocale),
    },
  };
}
```

```typescript
// src/app/[locale]/about/page.tsx
import type { Metadata } from 'next';
import { getTranslations } from 'next-intl/server';
import { routing } from '@/i18n/routing';
import { getAlternates } from '@/i18n/metadata';

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: 'AboutPage' });

  return {
    title: t('metaTitle'),
    description: t('metaDescription'),
    alternates: getAlternates(locale, '/about'),
    openGraph: {
      title: t('metaTitle'),
      description: t('metaDescription'),
      locale,
      alternateLocale: routing.locales.filter((l) => l !== locale),
    },
  };
}

// Dynamic routes: pass the concrete path, e.g. getAlternates(locale, `/blog/${slug}`).
// With localized `pathnames`, pass the internal route instead:
// getAlternates(locale, { pathname: '/blog/[slug]', params: { slug } })
```

next-intl's middleware also sends the alternates as a `Link` response header by default (`alternateLinks` in `defineRouting`).

## Manual hreflang (HTML head)

```html
<link rel="alternate" hreflang="en" href="https://example.com/about" />
<link rel="alternate" hreflang="es" href="https://example.com/es/about" />
<link rel="alternate" hreflang="fr" href="https://example.com/fr/about" />
<link rel="alternate" hreflang="x-default" href="https://example.com/about" />
```

**Rules:**
- Every page MUST have hreflang for ALL language versions including itself
- `x-default` points to the canonical/default version
- Use full URLs (not relative)
- hreflang MUST be reciprocal (if page A links to page B, B must link back to A)

## Localized Sitemap

```typescript
// Next.js: app/sitemap.ts
import { routing } from '@/i18n/routing';

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const pages = ['', '/about', '/pricing', '/blog'];

  return pages.flatMap((page) =>
    routing.locales.map((locale) => ({
      url: `https://example.com${locale === 'en' ? '' : `/${locale}`}${page}`,
      lastModified: new Date(),
      changeFrequency: 'weekly' as const,
      priority: page === '' ? 1 : 0.8,
      alternates: {
        languages: Object.fromEntries(
          routing.locales.map((l) => [
            l,
            `https://example.com${l === 'en' ? '' : `/${l}`}${page}`,
          ])
        ),
      },
    }))
  );
}
```

## Localized Open Graph Images

```typescript
// app/[locale]/opengraph-image.tsx
import { ImageResponse } from 'next/og';
import { getTranslations } from 'next-intl/server';

export default async function OGImage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;  // params is a Promise since Next.js 16
  const t = await getTranslations({ locale, namespace: 'OG' });

  return new ImageResponse(
    <div style={{ fontSize: 48, color: 'white', background: '#000' }}>
      {t('title')}
    </div>,
    { width: 1200, height: 630 }
  );
}
```
