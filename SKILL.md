---
name: i18n-localizer
description: AI-powered internationalization and localization for web, mobile, and native Apple apps. Use when users ask to translate, localize, or internationalize their app, add language support, create locale files, set up i18n routing, manage translations, generate hreflang/SEO metadata, or localize SwiftUI/iOS/macOS apps. Supports Next.js (App Router & Pages Router), Vite, React Router, React Native, Expo, SwiftUI (String Catalogs), and plain React. Handles JSON, YAML, CSV, PO, Markdown, xcstrings, and other translation file formats.
---

# i18n Localizer

An AI-powered skill for internationalizing and localizing web, mobile, and native Apple applications. This skill enables Claude Code to scan codebases for translatable strings, set up i18n infrastructure, generate high-quality localized translations, handle SEO metadata, and maintain translation files — all without external API calls.

## Credits

Built on knowledge from [Lingo.dev](https://github.com/lingodotdev/lingo.dev) (Apache-2.0), Apple Developer documentation, and community best practices.

---

## When to Use This Skill

- User says "translate my app", "localize", "add language support", "i18n", "internationalize"
- User wants to add new locales to an existing app
- User has locale JSON/YAML/PO/xcstrings files that need translation
- User wants i18n routing set up (e.g., `/en/about`, `/es/about`)
- User wants to extract hardcoded strings into locale files
- User asks to update or sync translations after content changes
- User wants hreflang tags, localized metadata, or multilingual SEO
- User wants to localize a SwiftUI/iOS/macOS app using String Catalogs
- User wants to migrate a hardcoded English app to support multiple languages
- User asks about RTL layout, pluralization, or date/number formatting

---

## Core Workflow

### Step 1: Detect Project Type

Scan the project to determine:
1. **Framework**: Next.js, Vite + React, React Router v7, TanStack Start, React Native, Expo, SwiftUI, Vue, Svelte, or other
2. **Existing i18n setup**: `next-intl`, `react-i18next`, `i18next`, `@lingo.dev/compiler`, `.xcstrings`, or similar
3. **Locale file format**: JSON, YAML, PO, CSV, Markdown, XLIFF, xcstrings, or none yet
4. **Source locale**: Usually `en`, detect from existing files or ask
5. **Target locales**: Ask user which languages they need

```
Files to check:
- package.json (dependencies)
- next.config.ts / vite.config.ts
- locales/ or messages/ or i18n/ or public/locales/
- i18n.json (Lingo.dev CLI config)
- *.xcodeproj / *.xcworkspace (Apple projects)
- *.xcstrings (Xcode String Catalogs)
- Localizable.strings (legacy Apple)
- android/app/src/main/res/values/strings.xml (Android)
```

### Step 2: Choose Strategy

| Project Type | Recommended Strategy |
|---|---|
| New React/Next.js/Vite (greenfield) | A: Compiler Approach |
| Next.js needing SEO + locale routing | B: next-intl |
| Vite / CRA / non-Next.js React | C: react-i18next |
| React Native / Expo mobile app | D: React Native |
| SwiftUI / iOS / macOS native app | E: Apple Native |
| Existing locale files need translation | F: Manual Translation |

---

## Strategy A: Compiler Approach (Lingo.dev)

No translation keys needed. Strings detected automatically from JSX.

### Next.js (App Router)

```bash
npm install @lingo.dev/compiler
```

```typescript
// next.config.ts
import type { NextConfig } from "next";
import { withLingo } from "@lingo.dev/compiler/next";

const nextConfig: NextConfig = {};

export default async function (): Promise<NextConfig> {
  return await withLingo(nextConfig, {
    sourceRoot: "./app",
    sourceLocale: "en",
    targetLocales: ["es", "fr", "de", "ru", "zh", "ja"],
    models: "lingo.dev",
    dev: { usePseudotranslator: true },  // fake translations in dev, no API calls
    buildMode: "cache-only",             // production build uses pre-generated translations only
  });
}
```

### LingoProvider (Required)

```typescript
// app/layout.tsx
import { LingoProvider } from "@lingo.dev/compiler/react";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <LingoProvider>
      <html><body>{children}</body></html>
    </LingoProvider>
  );
}
```

**Critical:** LingoProvider MUST be in root layout. Next.js config MUST be async function.

### Vite + React

```typescript
// vite.config.ts
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { lingoCompilerPlugin } from "@lingo.dev/compiler/vite";

export default defineConfig({
  plugins: [
    lingoCompilerPlugin({
      sourceRoot: "src",
      sourceLocale: "en",
      targetLocales: ["es", "fr", "de"],
      models: "lingo.dev",
      dev: { usePseudotranslator: true },
    }),
    react(),
  ],
});
```

**Critical:** Lingo compiler plugin BEFORE `react()` plugin. Wrap the app in `LingoProvider` (from `@lingo.dev/compiler/react`) as high as possible — with TanStack Router it must sit above `RouterProvider`, or code-splitting breaks the context.

**Build modes:** `buildMode: "translate"` (default) calls the configured model for missing strings and fails the build if translation fails. `"cache-only"` makes no API calls and fails if translations are missing — generate them in dev or CI first. Override per run with `LINGO_BUILD_MODE=cache-only npm run build`.

### What Gets Translated

```tsx
// AUTO-TRANSLATED (JSX text):
<h1>Welcome to our app</h1>
<button>Submit</button>
<img alt="Product photo" />

// NOT translated (string literals):
const message = "Hello world";

// WORKAROUND:
const message = <>Hello world</>;  // Fragment → detectable
```

### Free Model Options

- `"groq:qwen/qwen3-32b"` — Free Groq tier (`GROQ_API_KEY`)
- `"google:gemini-2.0-flash"` — Google AI (`GOOGLE_API_KEY`)
- `"ollama:mistral-small3.1"` — Local, zero cost
- `"lingo.dev"` — 10K free words/month

---

## Strategy B: next-intl Setup (Next.js)

The most popular Next.js i18n library. Full routing, middleware, Server Component support.

### Installation

```bash
npm install next-intl
```

### File Structure

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

### Step-by-Step Setup

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

### next-intl Language Switcher

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

### Localized Pathnames

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

---

## Strategy C: react-i18next Setup (Vite / CRA / React)

### Installation

```bash
npm install react-i18next i18next i18next-browser-languagedetector i18next-http-backend
```

### Setup

```typescript
// src/i18n/config.ts
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';
import Backend from 'i18next-http-backend';

i18n
  .use(Backend)
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    fallbackLng: 'en',
    supportedLngs: ['en', 'es', 'fr', 'de', 'ru', 'zh', 'ja'],
    interpolation: { escapeValue: false },
    backend: {
      loadPath: '/locales/{{lng}}/{{ns}}.json',
    },
    detection: {
      order: ['querystring', 'cookie', 'localStorage', 'navigator'],
      caches: ['cookie', 'localStorage'],
    },
  });

export default i18n;
```

```typescript
// src/main.tsx
import './i18n/config';
import { Suspense } from 'react';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <Suspense fallback={<div>Loading...</div>}>
    <App />
  </Suspense>
);
```

### Usage

```typescript
import { useTranslation } from 'react-i18next';

function MyComponent() {
  const { t, i18n } = useTranslation();

  return (
    <div>
      <h1>{t('welcome')}</h1>
      <button onClick={() => i18n.changeLanguage('es')}>Español</button>
    </div>
  );
}
```

### File Structure

```
public/
└── locales/
    ├── en/
    │   ├── translation.json   # Default namespace
    │   └── common.json        # Named namespace
    ├── es/
    │   ├── translation.json
    │   └── common.json
    └── fr/
        ├── translation.json
        └── common.json
```

---

## Strategy D: React Native / Expo

### Installation

```bash
npm install i18next react-i18next react-native-localize
# For Expo:
npx expo install expo-localization
```

### Setup

```typescript
// src/i18n/config.ts
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import * as RNLocalize from 'react-native-localize';
// For Expo: import * as Localization from 'expo-localization';

import en from './locales/en.json';
import es from './locales/es.json';
import fr from './locales/fr.json';

const deviceLocale = RNLocalize.getLocales()[0].languageCode;
// Expo: const deviceLocale = Localization.getLocales()[0].languageCode;

i18n.use(initReactI18next).init({
  resources: {
    en: { translation: en },
    es: { translation: es },
    fr: { translation: fr },
  },
  lng: deviceLocale,
  fallbackLng: 'en',
  interpolation: { escapeValue: false },
});

export default i18n;
```

### React Native Specifics

- Bundle translations directly (no HTTP backend on mobile)
- Use device locale for initial language: `RNLocalize.getLocales()[0]`
- Re-check the device locale when the app returns to the foreground. `react-native-localize` v3 removed `addEventListener`; its calls are now synchronous and always current, so use `AppState`:
  ```typescript
  import { AppState } from 'react-native';

  AppState.addEventListener('change', (state) => {
    if (state !== 'active') return;
    // Skip this if the user picked a language in-app (stored override wins)
    const deviceLocale = RNLocalize.getLocales()[0].languageCode;
    if (deviceLocale !== i18n.language) i18n.changeLanguage(deviceLocale);
  });
  ```
- Store language preference in `AsyncStorage` for user override
- For RTL: `I18nManager.forceRTL(isRTL)` — requires app restart
- Date/number formatting: use `Intl` polyfill if needed (`intl-pluralrules`)

---

## Strategy E: Apple Native (SwiftUI — String Catalogs)

For iOS, macOS, watchOS, tvOS, and visionOS apps. Uses Xcode 15+ String Catalogs (`.xcstrings`).

### How String Catalogs Work

1. Create `Localizable.xcstrings` file in Xcode (File → New → String Catalog)
2. Add target languages in Project → Info → Localizations
3. Build the project — Xcode auto-extracts all localizable strings
4. Translate strings directly in the String Catalog editor

### SwiftUI String Literals Are Localizable by Default

**IMPORTANT CAVEAT:** Only **string literals directly in SwiftUI views** are auto-localizable.
Strings passed through `String` variables or parameters are **NOT** localizable — this is the
single most common localization bug in SwiftUI apps. See "SwiftUI Localization Pitfalls" below.

```swift
// AUTOMATICALLY localizable — Xcode extracts these:
Text("Welcome back")            // ✅ String literal → LocalizedStringKey
Button("Save") { save() }       // ✅ String literal
Label("Settings", systemImage: "gear")  // ✅ String literal

// NOT localizable:
Text(verbatim: "DEBUG: \(value)")  // Explicitly verbatim
Text(String("Not localized"))      // String() wrapping blocks localization
Text(someStringVariable)           // ⚠️ String variable — NOT localized!

// String(localized:) for non-SwiftUI contexts:
let title = String(localized: "Buy a book")
let error = String(localized: "Failed to load data",
                   comment: "Error shown when API request fails")
```

### Adding Translator Context (Comments)

```swift
Text("Explore",
     comment: "Tab bar item title for the discovery/explore section")

Button(action: doSomething) {
  Text("View showtimes",
       comment: "Button to display movie showtimes")
}

String(localized: "items_count",
       defaultValue: "\(count) items",
       comment: "Number of items in the user's cart")
```

### Pluralization in String Catalogs

In the Xcode String Catalog editor, right-click a string → "Vary by Plural":

```swift
// In SwiftUI:
Text("\(count) items")  // Xcode detects the interpolated Int

// String Catalog handles plural forms per language:
// English: "1 item" / "%lld items"
// Russian: "%lld товар" / "%lld товара" / "%lld товаров"
// Arabic: all 6 forms (zero/one/two/few/many/other)
```

### Multiple String Catalogs (Modular Organization)

```swift
// Reference specific table:
Text("Explore", tableName: "Navigation")
String(localized: "Get Started", table: "MainScreen")

// For frameworks/packages, specify bundle:
Text("Cast & Crew", bundle: Bundle(for: MovieDetails.self))
```

Create separate `.xcstrings` files: `Navigation.xcstrings`, `Settings.xcstrings`, etc.

### Type-Safe Localization Keys (Scalable Pattern)

```swift
import SwiftUI

struct Strings {
  struct Onboarding {
    static let welcome = LocalizedStringKey("Welcome to RFLX")
    static let getStarted = LocalizedStringKey("Get Started")
    static let skipForNow = LocalizedStringKey("Skip for now")
  }
  struct Session {
    static let startSession = LocalizedStringKey("Start Session")
    static let endSession = LocalizedStringKey("End Session")
    static let summary = LocalizedStringKey("Session Summary")
  }
  struct Common {
    static let save = LocalizedStringKey("Save")
    static let cancel = LocalizedStringKey("Cancel")
    static let settings = LocalizedStringKey("Settings")
  }
}

// Usage:
Text(Strings.Onboarding.welcome)
Button(Strings.Common.save) { save() }
```

### String(localized:) for Non-View Contexts

```swift
// Error handling:
enum AppError: LocalizedError {
  case networkFailed
  case unauthorized

  var errorDescription: String? {
    switch self {
    case .networkFailed:
      return String(localized: "Network connection failed. Please try again.",
                    comment: "Error when network request fails")
    case .unauthorized:
      return String(localized: "Please sign in to continue.",
                    comment: "Error when user session expired")
    }
  }
}

// Notifications:
let content = UNMutableNotificationContent()
content.title = String(localized: "Session Complete",
                       comment: "Notification title after AI session ends")
content.body = String(localized: "Your session summary is ready.",
                      comment: "Notification body after AI session ends")
```

### Info.plist Localization

Create `InfoPlist.xcstrings` to localize:
- `CFBundleDisplayName` — App name on home screen
- `NSCameraUsageDescription` — Camera permission prompt
- `NSMicrophoneUsageDescription` — Microphone permission prompt
- `NSLocationWhenInUseUsageDescription` — Location permission prompt

### Xcode String Catalog States

| State | Meaning |
|---|---|
| Green ✓ | Translated |
| NEW | Not yet translated |
| STALE | String no longer in code (deleted/renamed) |
| NEEDS REVIEW | Marked for review |

### Preview Localization Testing

```swift
#Preview("English") {
  ContentView()
}

#Preview("Русский") {
  ContentView()
    .environment(\.locale, Locale(identifier: "ru"))
}

#Preview("العربية") {
  ContentView()
    .environment(\.locale, Locale(identifier: "ar"))
    .environment(\.layoutDirection, .rightToLeft)
}
```

### Xcode Export/Import for External Translators

```bash
# Export for translators (creates .xcloc files):
xcodebuild -exportLocalizations -project MyApp.xcodeproj -localizationPath ./translations

# Import translations back:
xcodebuild -importLocalizations -project MyApp.xcodeproj -localizationPath ./translations/es.xcloc
```

### Apple-Specific Formatting

```swift
// Date formatting (auto-adapts to locale):
Text(date, style: .date)
Text(date, format: .dateTime.month(.wide).day().year())

// Number formatting:
Text(price, format: .currency(code: "USD"))
Text(percentage, format: .percent)
Text(count, format: .number)

// Measurement:
let distance = Measurement(value: 5, unit: UnitLength.kilometers)
Text(distance, format: .measurement(width: .wide))
```

### SwiftUI Localization Pitfalls (CRITICAL)

These are the most common localization bugs in real SwiftUI apps. They consume 80%+ of debugging time.

#### Pitfall 1: Helper Functions with `String` Parameters

The **#1 localization bug**. When a helper function takes a `String` parameter and passes it to `Text()`, the string is NOT looked up in the String Catalog.

```swift
// ❌ BROKEN — Text(title) does NOT localize when title is a String:
private func sectionHeader(_ title: String, icon: String) -> some View {
    HStack {
        Image(systemName: icon)
        Text(title)  // ← Receives a String, NOT a LocalizedStringKey. No catalog lookup!
    }
}
sectionHeader("Coming Up", icon: "calendar")  // "Coming Up" stays English forever

// ✅ FIX — Change parameter type to LocalizedStringKey:
private func sectionHeader(_ title: LocalizedStringKey, icon: String) -> some View {
    HStack {
        Image(systemName: icon)
        Text(title)  // ← Now receives LocalizedStringKey. Catalog lookup happens!
    }
}
sectionHeader("Coming Up", icon: "calendar")  // ✅ String literal auto-converts to LocalizedStringKey
```

**Audit command:** Search for all helper functions that might have this bug:
```swift
// Grep for: functions taking String params that render in Text/Label/Button
grep -rn 'func.*(_ \w\+: String' --include="*.swift" Views/
grep -rn 'func.*label: String' --include="*.swift" Views/
grep -rn 'func.*title: String' --include="*.swift" Views/
grep -rn 'func.*header: String' --include="*.swift" Views/
```

#### Pitfall 2: Mixed-Use Strings (Display + Logic Key)

When a string is used both for display AND as a dictionary key or switch value, you can't simply change the param to `LocalizedStringKey` (because `LocalizedStringKey` can't be used in `dict[key]` lookups).

```swift
// ❌ Problem: label is used both for display and as dict key:
func filterChip(_ label: String, count: Int) -> some View {
    HStack {
        Text(label)  // Want this localized...
    }
    .opacity(visibleCounts[label] ?? 0 > 0 ? 1 : 0.5)  // ...but also need it as dict key
}

// ✅ FIX — Keep String param, force catalog lookup with LocalizedStringKey():
func filterChip(_ label: String, count: Int) -> some View {
    HStack {
        Text(LocalizedStringKey(label))  // Forces catalog lookup from runtime String
    }
    .opacity(visibleCounts[label] ?? 0 > 0 ? 1 : 0.5)  // Still works as dict key
}
```

#### Pitfall 3: Enum `rawValue` for Display Text

Using `.rawValue.capitalized` or `.rawValue` for user-facing display bypasses localization entirely.

```swift
// ❌ BROKEN — rawValue is never localized:
enum InsightVerdict: String { case confirmed, mismatch, uncertain }

Text(verdict.rawValue.capitalized)  // Shows "Confirmed" in all languages

// ✅ FIX — Add a localized label computed property or function:
func verdictLabel(_ verdict: InsightVerdict) -> LocalizedStringKey {
    switch verdict {
    case .confirmed: "Confirmed"   // LocalizedStringKey literal → catalog lookup
    case .mismatch:  "Mismatch"
    case .uncertain: "Uncertain"
    }
}
Text(verdictLabel(verdict))  // ✅ Shows translated text

// Alternative — computed property with String(localized:):
extension InsightVerdict {
    var displayName: String {
        switch self {
        case .confirmed: String(localized: "Confirmed")
        case .mismatch:  String(localized: "Mismatch")
        case .uncertain: String(localized: "Uncertain")
        }
    }
}
```

#### Pitfall 4: Computed Properties Returning Plain Strings

Properties that return `String` without `String(localized:)` are invisible to String Catalogs.

```swift
// ❌ BROKEN — plain string literals in computed properties:
var statusLabel: String {
    switch self {
    case .granted: "Granted"      // NOT localized — just a String
    case .denied:  "Not Granted"
    }
}

// ✅ FIX — wrap in String(localized:):
var statusLabel: String {
    switch self {
    case .granted: String(localized: "Granted")
    case .denied:  String(localized: "Not Granted")
    }
}
```

#### Pitfall 5: Settings Picker Items with String Tags

Picker items where the tag value doubles as display text bypass localization.

```swift
// ❌ BROKEN — Text(freq) renders the raw String:
let frequencies = ["Daily", "Weekly", "Monthly"]
Picker("Frequency", selection: $freq) {
    ForEach(frequencies, id: \.self) { freq in
        Text(freq).tag(freq)  // "Daily" stays English
    }
}

// ✅ FIX — Force catalog lookup, keep English as storage value:
ForEach(frequencies, id: \.self) { freq in
    Text(LocalizedStringKey(freq)).tag(freq)  // Display: localized, Storage: English
}
```

### Programmatic xcstrings Audit

For large apps, manual checking is impractical. Use scripts to find untranslated strings.

#### Audit Script: Find `String(localized:)` keys missing from catalogs

Compares every `String(localized:)` key in Swift code against all `.xcstrings` files, then lists keys with no translation or still awaiting review. Handles `comment:`/`table:` arguments, escaped quotes, and nested interpolations; skips `shouldTranslate: false` and stale entries.

```python
#!/usr/bin/env python3
"""Audit String(localized:) calls against the project's String Catalogs."""
import json, os, re

SWIFT_ROOT = "."
TARGET_LOCALE = "ru"  # Change to your target
SKIP_DIRS = {".git", ".build", "build", "DerivedData", "Pods", "Carthage"}

# Xcode turns each interpolation into a typed specifier: String → %@, Int → %lld,
# Double → %lf (untyped extraction writes %arg). Code alone can't tell the type,
# so collapse every specifier to %@ on both sides before comparing.
SPECIFIER = re.compile(r"%(?:\d+\$)?(?:arg|[-+ #0]*\d*(?:\.\d+)?(?:hh|h|ll|l|q|z|t|j|L)?[@dDiuUxXoOfFeEgGcCsSaA])")
CALL = re.compile(r'String\(\s*localized:\s*"(?!"")')  # skips """multi-line""" literals
ESCAPES = {"n": "\n", "t": "\t", "r": "\r", "0": "\0", '"': '"', "'": "'", "\\": "\\"}

def normalize(key):
    return SPECIFIER.sub("%@", key)

def read_literal(src, i):
    """Read a Swift string literal starting just after its opening quote.
    Returns the catalog-style key (interpolations → %@) or None."""
    out = []
    while i < len(src):
        c = src[i]
        if c == '"':
            return "".join(out)
        if c == "\n":
            return None
        if c == "\\":
            nxt = src[i + 1]
            if nxt == "(":  # interpolation — skip balanced parentheses
                depth, i = 1, i + 2
                while i < len(src) and depth:
                    depth += {"(": 1, ")": -1}.get(src[i], 0)
                    i += 1
                out.append("%@")
                continue
            if nxt == "u" and src[i + 2] == "{":
                end = src.index("}", i)
                out.append(chr(int(src[i + 3:end], 16)))
                i = end + 1
                continue
            out.append(ESCAPES.get(nxt, nxt))
            i += 2
            continue
        out.append(c)
        i += 1
    return None

def states(node):
    """All stringUnit states under a localization (covers plural/device variations)."""
    if isinstance(node, dict):
        if "state" in node:
            yield node["state"]
        for v in node.values():
            yield from states(v)

swift_files, catalogs = [], {}
for dirpath, dirnames, filenames in os.walk(SWIFT_ROOT):
    dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
    for name in filenames:
        path = os.path.join(dirpath, name)
        if name.endswith(".swift"):
            swift_files.append(path)
        elif name.endswith(".xcstrings"):
            with open(path, encoding="utf-8") as f:
                catalogs[path] = json.load(f)

# Keys can live in any table (String(localized:table:)), so check against all catalogs.
known = {normalize(k) for c in catalogs.values() for k in c["strings"]}

missing = []
for path in swift_files:
    with open(path, encoding="utf-8") as f:
        src = f.read()
    for m in CALL.finditer(src):
        key = read_literal(src, m.end())
        if key is not None and normalize(key) not in known:
            missing.append((path, src[:m.start()].count("\n") + 1, key))

untranslated, needs_review = [], []
for path, catalog in catalogs.items():
    if catalog.get("sourceLanguage") == TARGET_LOCALE:
        continue
    for key, entry in catalog["strings"].items():
        if entry.get("shouldTranslate") is False or entry.get("extractionState") == "stale":
            continue
        found = set(states(entry.get("localizations", {}).get(TARGET_LOCALE, {})))
        if not found or "new" in found:
            untranslated.append((path, key))
        elif "needs_review" in found:
            needs_review.append((path, key))

print(f"String(localized:) keys missing from every catalog: {len(missing)}")
print("  (usually fixed by building in Xcode so the key gets extracted)")
for path, line, key in missing:
    print(f"  {path}:{line} — {key!r}")
print(f"\nKeys with no {TARGET_LOCALE} translation: {len(untranslated)}")
for path, key in untranslated[:50]:
    print(f"  {os.path.basename(path)}: {key!r}")
print(f"\n{TARGET_LOCALE} translations still marked needs_review: {len(needs_review)}")
for path, key in needs_review[:50]:
    print(f"  {os.path.basename(path)}: {key!r}")
```

#### Audit Script: Find `String` params in helper functions

```bash
# Find helper functions taking String params that likely render in views
grep -rn 'func.*(_ \w\+: String' --include="*.swift" Views/
grep -rn 'Text(\w\+)' --include="*.swift" Views/  # Text(variable) — likely unlocalized
```

#### Bulk-Add Translations to xcstrings via Python

Writes Claude's translations as `needs_review` so they stay flagged in Xcode until a person approves them. Never overwrites a `translated` (reviewed) entry, skips plural keys (edit those per category in Xcode), and reports keys that aren't in the catalog yet instead of inventing them.

```python
#!/usr/bin/env python3
"""Add AI-drafted translations to an xcstrings catalog, marked for human review."""
import json, re

CATALOG = "Resources/Localizable.xcstrings"
LOCALE = "ru"
OVERWRITE_REVIEWED = False  # True replaces translations a person already approved

translations = {
    "Coming Up": "Ближайшие",
    "Your Week": "Ваша неделя",
    # ... add more entries
}

with open(CATALOG, encoding="utf-8") as f:
    raw = f.read()
catalog = json.loads(raw)
strings = catalog["strings"]

added, kept, not_extracted, plural = [], [], [], []
for key, value in translations.items():
    entry = strings.get(key)
    if entry is None:
        not_extracted.append(key)  # build in Xcode first so the key is extracted
        continue
    locs = entry.setdefault("localizations", {})
    if any("variations" in loc for loc in locs.values()):
        plural.append(key)  # needs one value per plural category — edit in Xcode
        continue
    state = locs.get(LOCALE, {}).get("stringUnit", {}).get("state")
    if state == "translated" and not OVERWRITE_REVIEWED:
        kept.append(key)
        continue
    # AI output is a draft: needs_review keeps it visible in Xcode until someone approves it
    locs[LOCALE] = {"stringUnit": {"state": "needs_review", "value": value}}
    entry["localizations"] = dict(sorted(locs.items()))  # Xcode keeps locales sorted
    added.append(key)

# Match Xcode's own formatting (2-space indent, " : ", empty objects split over
# lines) so diffs show only real changes
text = json.dumps(catalog, indent=2, ensure_ascii=False, separators=(",", " : "))
text = re.sub(r"^( *)(.*)\{\}(,?)$", lambda m: f"{m[1]}{m[2]}{{\n\n{m[1]}}}{m[3]}", text, flags=re.M)
with open(CATALOG, "w", encoding="utf-8") as f:
    f.write(text + ("\n" if raw.endswith("\n") else ""))

print(f"Added as needs_review: {added}")
print(f"Kept existing reviewed translations: {kept}")
print(f"Not in catalog yet (build first): {not_extracted}")
print(f"Plural keys to edit in Xcode: {plural}")
```

### AI-Generated Content Localization

Modern apps use LLMs (OpenAI, Gemini, Claude) to generate user-facing content.
This content must match the app's language setting.

#### Pattern: Locale-Aware Prompt Injection

```swift
// 1. Create a locale helper:
enum AppLocale {
    static var promptLanguage: String {
        let code = UserDefaults.standard.string(forKey: "AppLanguage")
            ?? Locale.preferredLanguages.first?.components(separatedBy: "-").first
            ?? "en"
        switch code {
        case "ru": return "Russian"
        case "es": return "Spanish"
        case "de": return "German"
        case "fr": return "French"
        case "zh": return "Chinese"
        case "ja": return "Japanese"
        default:   return "English"
        }
    }

    /// Append to every AI system prompt. Returns "" for English (zero overhead).
    static var promptInstruction: String {
        let lang = promptLanguage
        if lang == "English" { return "" }
        return """
        \n\nIMPORTANT: Respond entirely in \(lang). All titles, body text, \
        reasoning, labels, suggestions, and recommendations must be in \(lang).
        """
    }
}

// 2. Inject into every AI prompt:
let systemPrompt = """
You are an expert interview analyst. Analyze the transcript...
\(AppLocale.promptInstruction)
"""

// 3. What NOT to localize in AI prompts:
// - JSON key names (type, title, body) — keep English for parsing
// - Enum values used for deserialization (confirmed, mismatch)
// - Classifier/gate prompts that return structured boolean data
// - Prompt instructions themselves (the AI understands English best)
// Only localize the AI's OUTPUT content, not the prompt structure.
```

#### What to Localize vs. What to Keep English

| Element | Localize? | Why |
|---|---|---|
| AI-generated titles, body text | Yes | User-facing content |
| AI-generated suggestions, tips | Yes | User-facing content |
| JSON keys in prompt schema | No | Needed for parsing |
| Enum rawValues for deserialization | No | Code depends on English values |
| Prompt instructions to the AI | No | AI understands English prompts best |
| Internal API labels (CSV headers) | Optional | Export format preference |

---

## Strategy F: Translate Existing Locale Files

When user already has `en.json` and needs other languages:

1. Read the source locale file
2. For each target language, create properly localized version following Translation Quality Rules below
3. Maintain identical key structure and variable placeholders

### Lingo.dev CLI (Optional Automation)

```json
// i18n.json
{
  "$schema": "https://lingo.dev/schema/i18n.json",
  "version": "1.10",
  "locale": {
    "source": "en",
    "targets": ["es", "fr", "de", "ru", "zh", "ja"]
  },
  "buckets": {
    "json": { "include": ["locales/[locale].json"] }
  }
}
```

**Supported bucket types:** `json`, `yaml`, `yaml-root-key`, `csv`, `po`, `markdown`, `mdx`, `android`, `xcode-xcstrings`, `properties`, `xliff`, `html`, `txt`, `php`, `flutter-arb`, `vue-json`, `typescript`

```bash
npx lingo.dev@latest init      # Create config
npx lingo.dev@latest run       # Translate all
npx lingo.dev@latest run --target-locale es  # Spanish only
npx lingo.dev@latest run --frozen    # CI: fail if translations are out of date
```

Commit `i18n.lock`. It stores a checksum of every source string, which is how `run` knows which strings changed and need retranslating.

---

## SEO & Multilingual Metadata

### hreflang Tags and Canonical URLs

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

### Manual hreflang (HTML head)

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

### Localized Sitemap

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

### Localized Open Graph Images

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

---

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

---

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

---

## Performance: Lazy Loading Translations

In production apps with many locales, shipping all translations upfront kills performance. Load only the active locale's strings.

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

### react-i18next (Backend Plugin)

```typescript
// i18next-http-backend loads namespaces on demand:
i18n.init({
  ns: ['common'],              // Load immediately
  defaultNS: 'common',
  backend: {
    loadPath: '/locales/{{lng}}/{{ns}}.json',
  },
  partialBundledLanguages: true,  // Allow partial loading
});

// In a component — loads 'dashboard' namespace on mount:
const { t } = useTranslation(['common', 'dashboard']);
```

### React Native / Expo

Bundle only the default locale. Fetch others on demand:

```typescript
import en from './locales/en.json';  // Bundled (always available offline)

// Load other locales lazily:
async function loadLocale(lang: string) {
  if (lang === 'en') return;
  try {
    const messages = await fetch(`https://cdn.example.com/locales/${lang}.json`);
    i18n.addResourceBundle(lang, 'translation', await messages.json());
  } catch {
    // Fallback to bundled English
  }
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

---

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

### Phase 5: Generate Translations

Use Claude Code to generate translations or Lingo.dev CLI for automation.

### Phase 6: SEO & Metadata

Add hreflang tags, localized metadata, and sitemap (see SEO section above).

---

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

---

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

### SwiftUI RTL

```swift
// SwiftUI handles RTL automatically for standard layouts
// Force RTL for testing:
.environment(\.layoutDirection, .rightToLeft)

// For custom drawing, check direction:
@Environment(\.layoutDirection) var layoutDirection
```

---

## Testing i18n

### Pseudo-Localization (Quick Visual Test)

Replace strings with accented characters to spot hardcoded text and layout issues:

```
"Save" → "[Šåvé___]"
"Welcome to our app" → "[Wélçömé tö öür äpp________]"
```

The padding (underscores) simulates text expansion for languages like German.

### Checklist

- [ ] All user-facing strings extracted (no hardcoded text visible)
- [ ] Variables preserved in all translations (`{name}` intact)
- [ ] Plural forms correct for each target language
- [ ] Date/number formats adapt to locale
- [ ] RTL layout works for Arabic/Hebrew (test with `dir="rtl"`)
- [ ] Long text doesn't break UI (German is ~30% longer)
- [ ] Short text doesn't look odd (CJK is ~50% shorter)
- [ ] Language switcher works and persists preference
- [ ] SEO: hreflang tags present and reciprocal
- [ ] SEO: `<html lang="xx">` attribute correct
- [ ] Fallback works when translation is missing
- [ ] Images with text have localized alternatives
- [ ] Email templates render correctly per locale

### Xcode Testing (Apple)

```swift
// Test specific locale in preview:
#Preview("日本語") {
  MyView().environment(\.locale, Locale(identifier: "ja"))
}

// Scheme → Edit Scheme → Run → Options → App Language → choose locale
// Also: App Region, to test date/number formatting
```

---

## Accessibility + i18n

### lang Attribute (Critical for Screen Readers)

```html
<!-- Root document language -->
<html lang="fr">

<!-- Inline language switch for mixed-language content -->
<p>The French word <span lang="fr">bonjour</span> means hello.</p>
```

Screen readers switch pronunciation engine based on `lang`.

### SwiftUI Accessibility

```swift
Text("Welcome")
  .accessibilityLabel(Text("Welcome to the app",
    comment: "VoiceOver label for welcome heading"))
```

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

---

## Email Template Localization

### Pattern

```typescript
// templates/welcome.ts
export function getWelcomeEmail(locale: string, data: { name: string }) {
  const translations: Record<string, { subject: string; body: string }> = {
    en: {
      subject: 'Welcome to RFLX!',
      body: `Hi ${data.name}, thank you for joining RFLX.`,
    },
    es: {
      subject: '¡Bienvenido a RFLX!',
      body: `Hola ${data.name}, gracias por unirte a RFLX.`,
    },
    ru: {
      subject: 'Добро пожаловать в RFLX!',
      body: `Привет, ${data.name}! Спасибо за регистрацию в RFLX.`,
    },
  };

  return translations[locale] || translations.en;
}
```

### Best Practices
- Keep email translations in separate files from UI translations
- Test rendering in actual email clients per locale
- Date/time in emails: include timezone and format for recipient's locale
- Unsubscribe link text must be localized (legal requirement in many countries)

---

## Translation Quality Rules

These rules are CRITICAL. This is localization, not word-for-word translation.

### 1. Context-Aware Translation
- "Save" (button) → "Guardar" (es), not "Salvar" (which means "rescue")
- "Post" (noun, blog) → "Publicación" (es); "Post" (verb) → "Publicar" (es)
- "Home" (navigation) → "Inicio" (es); "Home" (address) → "Hogar" (es)
- "Check" (verify) → "Проверить" (ru); "Check" (payment) → "Чек" (ru)

### 2. Preserve Variables and Placeholders
```json
// Source:
{ "welcome": "Welcome back, {name}!" }

// ✅ CORRECT:
{ "welcome": "¡Bienvenido de nuevo, {name}!" }

// ❌ WRONG (variable name changed):
{ "welcome": "¡Bienvenido de nuevo, {nombre}!" }
```

Never translate variable names inside `{curly braces}`. Keep them identical.

### 3. Handle Pluralization (ICU MessageFormat)

Don't rely on memory for plural forms. Ask the runtime, because CLDR changes between releases (for example, French, Spanish, Italian and Portuguese recently gained `many`):

```bash
node -e 'console.log(new Intl.PluralRules("ru").resolvedOptions().pluralCategories)'
# → [ 'few', 'many', 'one', 'other' ]
```

Every translated plural message must cover every category its locale reports; `other` is always required. Reference (CLDR 48):

| Categories | Languages |
|---|---|
| other | Chinese, Japanese, Korean, Vietnamese, Thai, Indonesian |
| one, other | English, German, Dutch, Turkish |
| one, many, other | Spanish, French, Italian, Portuguese (`many` covers large round numbers like 1 000 000, which take "de"/"di") |
| one, few, other | Romanian, Croatian, Serbian |
| one, two, other | Hebrew |
| one, few, many, other | Russian, Ukrainian, Polish, Czech |
| zero, one, two, few, many, other | Arabic |

### 4. Gender and Formality
- **German:** Formal "Sie" for UI (not "du")
- **French:** Formal "vous" for UI (not "tu")
- **Russian:** Formal "Вы" for UI (not "ты")
- **Spanish:** Regional variants — Latin American vs Castilian
- **Portuguese:** pt-BR vs pt-PT differ significantly

### 5. Text Length Constraints
- German: ~30% longer than English
- Chinese/Japanese/Korean: ~50% shorter
- Arabic/Hebrew: RTL + different character widths
- Test buttons, menus, and nav items in all locales

### 6. Do NOT Translate
- Brand names, product names, company names
- Technical identifiers, code references
- URLs, email addresses, file paths
- API endpoints, variable names

### 7. Cultural Adaptation
- Date: US (MM/DD/YYYY) vs EU (DD/MM/YYYY) vs ISO (YYYY-MM-DD)
- Numbers: 1,000.50 (en) vs 1.000,50 (de) vs 1 000,50 (fr)
- Currency: `$100.00` (en-US) vs `100,00 €` (fr-FR) vs `R$ 100,00` (pt-BR; US dollars are `US$ 100,00`). Never hand-write symbols or their position — use `Intl.NumberFormat(locale, { style: 'currency', currency })`

### 8. Consistency
- Same English term = same target translation throughout
- Build a glossary per project: "Settings" = always "Configuración" (es)
- Exception: different contexts may legitimately need different translations

---

## Translation Glossary Management

For consistency across large apps, maintain a glossary:

```json
// glossary.json — shared reference (not a runtime file)
{
  "en→es": {
    "Dashboard": "Panel",
    "Settings": "Configuración",
    "Profile": "Perfil",
    "Sign In": "Iniciar sesión",
    "Sign Out": "Cerrar sesión",
    "Notifications": "Notificaciones"
  },
  "en→ru": {
    "Dashboard": "Панель управления",
    "Settings": "Настройки",
    "Profile": "Профиль",
    "Sign In": "Войти",
    "Sign Out": "Выйти",
    "Notifications": "Уведомления"
  }
}
```

When translating, always check the glossary first and maintain consistency.

---

## BCP-47 Locale Codes Reference

| Code | Language |
|---|---|
| `en` | English |
| `es` / `es-ES` / `es-MX` / `es-419` | Spanish (generic / Spain / Mexico / Latin America) |
| `fr` / `fr-CA` | French / French (Canada) |
| `de` | German |
| `it` | Italian |
| `pt-BR` / `pt-PT` | Portuguese (Brazil / Portugal) |
| `ru` | Russian |
| `uk` | Ukrainian |
| `pl` | Polish |
| `zh-CN` / `zh-Hans` | Chinese Simplified |
| `zh-TW` / `zh-Hant` | Chinese Traditional |
| `ja` | Japanese |
| `ko` | Korean |
| `ar` | Arabic |
| `he` | Hebrew |
| `hi` | Hindi |
| `th` | Thai |
| `vi` | Vietnamese |
| `id` | Indonesian |
| `ms` | Malay |
| `tr` | Turkish |
| `nl` | Dutch |
| `sv` | Swedish |
| `da` | Danish |
| `nb` | Norwegian Bokmål |
| `fi` | Finnish |
| `ro` | Romanian |
| `cs` | Czech |
| `hu` | Hungarian |
| `bg` | Bulgarian |
| `hr` | Croatian |
| `sr` | Serbian |
| `el` | Greek |
| `sw` | Swahili |

---

## CI/CD Integration

### GitHub Actions (Lingo.dev)

```yaml
name: Translate
on:
  push:
    branches: [main]
permissions:
  contents: write
jobs:
  translate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Lingo.dev
        uses: lingodotdev/lingo.dev@main
        with:
          api-key: ${{ secrets.LINGODOTDEV_API_KEY }}
```

### PR Workflow (review before merge)

```yaml
      - name: Lingo.dev
        uses: lingodotdev/lingo.dev@main
        with:
          api-key: ${{ secrets.LINGODOTDEV_API_KEY }}
          pull-request: true
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

---

## Troubleshooting

### Compiler Issues

| Problem | Cause | Fix |
|---|---|---|
| Strings not translated | Text in string literal, not JSX | Wrap in fragment: `<>text</>` |
| Missing translations in prod | `cache-only` without cache | Run build with real translations first |
| HMR not working | LingoProvider placement | Move to root layout |
| Config type error | Not async function | Wrap in `async function` |

### next-intl Issues

| Problem | Fix |
|---|---|
| "Couldn't find config" | Ensure path in `createNextIntlPlugin()` is correct |
| Hook error in an `async` component | Use `await getTranslations()` from `next-intl/server`; `useTranslations` only works in non-async components |
| Dynamic rendering forced | Add `setRequestLocale(locale)` to all layouts/pages |
| Middleware not running | Check `matcher` config in proxy.ts |
| Client components missing translations | Wrap in `NextIntlClientProvider` with `messages` |

### Translation File Issues

| Problem | Fix |
|---|---|
| Broken variables | Ensure `{variableName}` stays identical |
| Missing plural forms | Add correct plural categories per language |
| Encoding issues | Ensure files are UTF-8 |
| Stale translations after source edits | Run `npx lingo.dev@latest run`: it compares source strings with the checksums in `i18n.lock` and retranslates only what changed. Regenerate specific keys with `run --key <path>`, or everything with `run --force` (overwrites manual edits). **Don't delete `i18n.lock`**: a fresh lockfile records the current source as already translated, so earlier edits are never picked up |

### Apple / Xcode Issues

| Problem | Fix |
|---|---|
| Strings not appearing in catalog | Build the project first (Cmd+B) |
| Stale strings showing | Clean build folder (Cmd+Shift+K) |
| Plurals not working | Right-click → "Vary by Plural" in catalog |
| Framework strings missing | Use `bundle:` parameter in `String(localized:)` |
| InfoPlist not localized | Create separate `InfoPlist.xcstrings` file |

---

## Quick Reference Commands

```bash
# next-intl
npm install next-intl

# react-i18next
npm install react-i18next i18next i18next-browser-languagedetector

# React Native
npm install i18next react-i18next react-native-localize

# Lingo.dev Compiler
npm install @lingo.dev/compiler

# Lingo.dev CLI
npx lingo.dev@latest init
npx lingo.dev@latest run

# Xcode export/import
xcodebuild -exportLocalizations -project MyApp.xcodeproj -localizationPath ./translations
xcodebuild -importLocalizations -project MyApp.xcodeproj -localizationPath ./translations/es.xcloc

# Claude Code approach (no tools needed)
# "Scan my app and create locale files for es, fr, ru, zh"
# "Read locales/en.json and generate all target translations"
# "Add i18n to my SwiftUI app for Russian and Chinese"
```

---

## Security Notes

This skill is a knowledge-only instructional document. It does not:
- Execute shell commands automatically
- Fetch external URLs or APIs
- Collect or transmit any data
- Modify files without explicit user instruction
- Contain prompt injection or override instructions

All translations are performed by Claude's own language capabilities. External tools (Lingo.dev, next-intl, etc.) are optional and installed independently by the user.

Source: Patterns adapted from [lingo.dev](https://github.com/lingodotdev/lingo.dev) (Apache-2.0), Apple Developer documentation, and community best practices.
