# React with react-i18next (Vite, React Router, CRA)

Default for React apps without Next.js. Messages use i18next syntax (`{{name}}`, plural keys `item_one`/`item_other`); check them with `check_locales.py "public/locales/[locale]/*.json"`. Plural keys follow each language's categories, so `ru` needs `item_few` and `item_many` while `ja` only has `item_other` — `translation_state.py todo` lists the keys each locale needs.

## Contents
- Installation
- Setup
- Usage
- File Structure
- Lazy loading namespaces

## Installation

```bash
npm install react-i18next i18next i18next-browser-languagedetector i18next-http-backend
```

## Setup

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

## Usage

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

## File Structure

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

## Lazy loading namespaces

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
