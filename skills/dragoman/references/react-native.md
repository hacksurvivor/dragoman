# React Native and Expo

i18next with bundled JSON (no HTTP backend on device). Same i18next syntax and plural keys as [react-i18next.md](react-i18next.md).

## Installation

```bash
npm install i18next react-i18next react-native-localize
# For Expo:
npx expo install expo-localization
```

## Setup

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

## React Native Specifics

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

## Loading locales on demand

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
