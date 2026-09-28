# Translation quality

Read this before translating. This is localization, not word-for-word translation. Project-specific choices (tone, regional variants, terms) live in `.dragoman/style.json` and override the defaults here.

## Contents
- Rules 1–8: context, placeholders, plurals, tone, length, do-not-translate, cultural formats, consistency
- The style file
- Locale codes
- Translation file problems

## Translation Quality Rules

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

Never translate variable names inside `{curly braces}` (ICU) or `{{double braces}}` (i18next), `$t(nested.keys)`, or tag names (`<link>…</link>`, `<1>…</1>`). Translate only the text between tags. Reorder placeholders freely when the grammar needs it.

In ICU messages an apostrophe before `{`, `}`, `<` or `#` starts literal text: `'{'` prints a brace. Ordinary apostrophes (`l'application`, `don't`) are fine as they are; `check_locales.py` flags messages that no longer parse.

### 3. Handle Pluralization (ICU MessageFormat)

Don't rely on memory for plural forms. Ask the runtime, because CLDR changes between releases (for example, French, Spanish, Italian and Portuguese recently gained `many`):

```bash
node -e 'console.log(new Intl.PluralRules("ru").resolvedOptions().pluralCategories)'
# → [ 'few', 'many', 'one', 'other' ]
```

Every translated plural message must cover every category its locale reports; `other` is always required. In ICU messages the categories are branches of `{count, plural, …}`; in i18next each is its own key (`item_one`, `item_few`, `item_many`, `item_other`), so the target file can have different keys from the source. Reference (CLDR 48):

| Categories | Languages |
|---|---|
| other | Chinese, Japanese, Korean, Vietnamese, Thai, Indonesian |
| one, other | English, German, Dutch, Turkish |
| one, many, other | Spanish, French, Italian, Portuguese (`many` covers large round numbers like 1 000 000, which take "de"/"di") |
| one, few, other | Romanian, Croatian, Serbian |
| one, two, other | Hebrew |
| one, few, many, other | Russian, Ukrainian, Polish, Czech |
| zero, one, two, few, many, other | Arabic |

### 4. Formality and regional variants
These are product decisions, not rules — ask the user once and record the answer in the style file:
- **Formality:** German du/Sie, French tu/vous, Spanish tú/usted, Russian ты/вы, Japanese plain/polite. Consumer apps often use the informal form; business and government software usually the formal one. Keep one choice per locale throughout.
- **Regional variants:** Spanish (Spain `es-ES` vs Latin America `es-419`), Portuguese (`pt-BR` vs `pt-PT` differ in vocabulary and grammar), Chinese (Simplified `zh-Hans` vs Traditional `zh-Hant`), French (`fr` vs `fr-CA`).
- **Gender:** prefer phrasings that avoid gendering the user when the language allows; use ICU `select` when the app knows the gender.

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
- Same source term = same target term throughout, taken from the style file's glossary
- Match the platform's own vocabulary (iOS/Android/Windows system terms) for standard actions
- Exception: different contexts may legitimately need different translations

## The style file

`.dragoman/style.json` records the project's decisions so every run translates the same way. `check_locales.py` warns when a translation drops a do-not-translate term or misses a glossary term.

```json
{
  "sourceLocale": "en",
  "locales": {
    "de": { "formality": "informal", "notes": "du; friendly, short" },
    "es-419": { "formality": "informal" },
    "ja": { "formality": "polite", "notes": "です/ます in UI text" }
  },
  "doNotTranslate": ["Acme", "Acme Pro", "GitHub"],
  "glossary": {
    "de": { "Workspace": "Arbeitsbereich", "Settings": "Einstellungen" },
    "es-419": { "Dashboard": "Panel", "Sign in": "Iniciar sesión" }
  }
}
```

Glossary checks are case-insensitive substring matches, so inflected forms (Russian cases, German compounds) can trigger false warnings — read them, don't blindly "fix" them.

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

## Translation file problems

| Problem | Fix |
|---|---|
| Broken variables or tags | `check_locales.py` names the key and placeholder; restore the source name |
| Missing plural forms | Add the categories `check_locales.py` lists for that language |
| Encoding issues | Save files as UTF-8 |
| Stale translations after source edits | Run `npx lingo.dev@latest run`: it compares source strings with the checksums in `i18n.lock` and retranslates only what changed. Regenerate specific keys with `run --key <path>`, or everything with `run --force` (overwrites manual edits). **Don't delete `i18n.lock`**: a fresh lockfile records the current source as already translated, so earlier edits are never picked up |
