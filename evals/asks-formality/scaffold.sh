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
    "settings": "Settings"
  },
  "cart": {
    "greeting": "Welcome back, {name}!",
    "items": "{count, plural, one {# item} other {# items}}",
    "empty": "Your cart is empty. <link>Browse products</link>"
  },
  "account": {
    "invite": "{inviter} invited you to join {team} on Acme.",
    "plan": "You're on the Acme Pro plan."
  }
}
FIXTURE
