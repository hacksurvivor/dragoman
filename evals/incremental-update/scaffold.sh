#!/usr/bin/env bash
# Seeds the workspace. Runs only with `claude plugin eval --scaffold`.
set -euo pipefail
cat > package.json <<'FIXTURE'
{
  "name": "shop",
  "private": true,
  "dependencies": { "next": "16.3.6", "next-intl": "4.14.7", "react": "19.2.0", "react-dom": "19.2.0" }
}
FIXTURE
mkdir -p messages
cat > messages/en.json <<'FIXTURE'
{
  "nav": {
    "home": "Home",
    "settings": "Settings",
    "help": "Help center"
  },
  "checkout": {
    "title": "Checkout",
    "greeting": "Good to see you again, {name}! Your cart is waiting.",
    "items": "{count, plural, one {# item in your cart} other {# items in your cart}}"
  }
}
FIXTURE
mkdir -p messages
cat > messages/de.json <<'FIXTURE'
{
  "nav": {
    "home": "Start",
    "settings": "Optionen"
  },
  "checkout": {
    "title": "Zur Kasse",
    "greeting": "Schön, dass du wieder da bist, {name}!",
    "items": "{count, plural, one {# Artikel im Warenkorb} other {# Artikel im Warenkorb}}"
  }
}
FIXTURE
mkdir -p .dragoman
cat > .dragoman/state.json <<'FIXTURE'
{
  "files": {
    "messages/[locale].json": {
      "de": {
        "checkout.greeting": {
          "source": "fc53f6caa381",
          "status": "reviewed",
          "target": "01fcc916dd59"
        },
        "checkout.items": {
          "source": "ab7656446466",
          "status": "reviewed",
          "target": "a4b5b6c68d4c"
        },
        "checkout.title": {
          "source": "c4e0089ebdb6",
          "status": "reviewed",
          "target": "ee66187e71af"
        },
        "nav.home": {
          "source": "8f3852d397a1",
          "status": "reviewed",
          "target": "d0d8ef2df968"
        },
        "nav.settings": {
          "source": "1dfb67011cd3",
          "status": "reviewed",
          "target": "b204243b5df3"
        }
      }
    }
  },
  "version": 1
}
FIXTURE
mkdir -p .dragoman
cat > .dragoman/style.json <<'FIXTURE'
{
  "sourceLocale": "en",
  "locales": { "de": { "formality": "informal" } }
}
FIXTURE
