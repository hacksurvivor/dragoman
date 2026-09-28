---
name: dragoman
description: Internationalizes and localizes apps end to end — sets up i18n (next-intl, react-i18next, React Native/Expo, SwiftUI String Catalogs), extracts hardcoded strings, translates locale files, and verifies every translation with bundled checks for missing keys, broken placeholders and wrong plural forms. Use when the user asks to translate, localize or internationalize an app, add a language, update translations after copy changes, find untranslated or broken strings, set up locale routing, hreflang or multilingual SEO, or handle RTL, plurals and date/number formatting. Also translates and checks existing JSON, YAML, ARB and .xcstrings files from any framework.
---

# dragoman

Localizes apps the way a careful human team would: decide tone and terms once, translate only what changed, check every file mechanically, and leave the user a clear list of what still needs human review.

## Where you're running

- **Claude Code or Cowork:** work in the user's project. Run the scripts as written below; `${CLAUDE_SKILL_DIR}` points at this skill's folder.
- **Chat on claude.ai, desktop or mobile:** there's no project checkout. Work on the locale files the user uploads or pastes, and give back complete translated files for them to download. The skill folder is copied into the code-execution sandbox, so run the scripts by their path relative to this file, e.g. `python3 scripts/check_locales.py "messages/[locale].json"` from the skill folder with the files copied next to it. Skip setup steps that need the user's codebase and say so.

## Workflow

Copy this checklist and work through it:

```
- [ ] 1. Detect the stack and existing i18n setup
- [ ] 2. Settle the project style (.dragoman/style.json)
- [ ] 3. Set up i18n — only if the project has none
- [ ] 4. Extract hardcoded strings — only if needed
- [ ] 5. Translate what's new or changed
- [ ] 6. Verify with the scripts, fix, re-run until clean
- [ ] 7. Report: what's translated, what's draft, what needs review
```

### 1. Detect

Check `package.json` dependencies, `next.config.*`, `vite.config.*`, `app.json` (Expo), `*.xcodeproj`, `*.xcstrings`, `i18n.json` (Lingo.dev), and locale folders (`messages/`, `locales/`, `public/locales/`, `lib/l10n/`, `src/i18n/`).

If the project already uses an i18n library, keep it. Don't migrate unless asked.

Setup guides cover **Next.js, React (Vite / React Router / CRA), React Native / Expo, and Apple platforms**. For anything else (Vue, Svelte, Angular, Flutter, Android, server frameworks) say so plainly: don't improvise a setup. You can still translate and check its JSON, YAML or ARB files (steps 5–6), and the Lingo.dev CLI handles PO, XLIFF, Android XML, CSV and more ([references/lingo.md](references/lingo.md)).

### 2. Settle the project style

If `.dragoman/style.json` exists, read it and follow it. Otherwise ask the user, in one message:

- target languages, including regional variants (es-ES or es-419? pt-BR or pt-PT? zh-Hans or zh-Hant?)
- formality per language (German du/Sie, French tu/vous, Japanese plain/polite …) — never guess this
- names and terms that must stay untranslated (brand, product, plan names)
- any required translations for key terms

Then write `.dragoman/style.json` (format in [references/translation-quality.md](references/translation-quality.md#the-style-file)) so later runs stay consistent.

### 3. Set up i18n (only if missing)

| Stack | Default | Read |
|---|---|---|
| Next.js App Router | next-intl | [references/nextjs.md](references/nextjs.md), [references/seo.md](references/seo.md) |
| Vite, React Router, CRA, plain React | react-i18next | [references/react-i18next.md](references/react-i18next.md) |
| React Native / Expo | i18next + react-native-localize or expo-localization | [references/react-native.md](references/react-native.md) |
| SwiftUI / UIKit | String Catalogs (`.xcstrings`) | [references/apple.md](references/apple.md) |

Offer the Lingo.dev compiler or CLI only if the user wants translation automated in the build or CI. It sends source strings to a model provider and needs an API key ([references/lingo.md](references/lingo.md)).

### 4. Extract hardcoded strings (only if needed)

Follow [references/extraction.md](references/extraction.md). Non-negotiable: whole sentences per key (no concatenation or split sentences), placeholders for variables, plural syntax for counts, locale-independent values for logic. Apple projects: read the pitfalls in [references/apple.md](references/apple.md) — most untranslated SwiftUI text comes from `String`-typed parameters.

### 5. Translate what's new or changed

Read [references/translation-quality.md](references/translation-quality.md) before the first translation in a session.

Web and React Native (JSON, YAML, ARB). The pattern names the locale files: `[locale]` is the locale code, `*` a namespace file, e.g. `"messages/[locale].json"`, `"public/locales/[locale]/*.json"`, `"lib/l10n/app_[locale].arb"`.

1. **First run in a project that already has translations:** ask whether people reviewed them. Record the answer so they're never overwritten:
   `python3 "${CLAUDE_SKILL_DIR}/scripts/translation_state.py" mark "<pattern>" --locale <codes> --status reviewed` (or `--status draft`)
2. **Get the work list:**
   `python3 "${CLAUDE_SKILL_DIR}/scripts/translation_state.py" todo "<pattern>" --json`
   Add `--locales de,ja` for languages that have no file yet; it tells you which files to create. Per locale, `translate` holds missing keys with their source text; `update` holds keys whose source changed, with the current translation and whether a person had reviewed it. For i18next plurals it lists the exact keys each language needs (`item_few`, `item_many` for Russian; only `item_other` for Japanese).
3. **Translate only those keys.** Leave every other key untouched — reviewed translations belong to the user. Keep the file's key order and formatting. For large files, go one namespace or top-level section at a time.
4. **Record the drafts:**
   `python3 "${CLAUDE_SKILL_DIR}/scripts/translation_state.py" mark "<pattern>" --locale <codes>`

Apple String Catalogs: use `xcstrings_audit.py` and `xcstrings_add.py` instead — see [references/apple.md](references/apple.md#scripts). Xcode tracks review state itself (Needs Review → Translated).

### 6. Verify

Run the checker and fix every error, then re-run until it passes:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/check_locales.py" "<pattern>"
python3 "${CLAUDE_SKILL_DIR}/scripts/translation_state.py" status "<pattern>"   # fails if a reviewed string was edited
```

`check_locales.py` reports missing or empty keys, placeholders and tags that differ from the source, ICU syntax errors, and plural forms a language needs (from CLDR data). Warnings cover orphan keys, text identical to the source, and style-file misses; read them, they're often real. Use `--allow-missing` while work is in progress and `--json` to parse the results.

Then check what the scripts can't:
- Run the app (or previews) in the longest language (often German) and in an RTL language if targeted: truncation, overflow, mirrored icons ([references/rtl-a11y.md](references/rtl-a11y.md))
- Pseudo-localize to find strings that were never extracted: temporarily replace the source values with accented, padded text (`"Save"` → `"[Šåvé___]"`); anything still plain English is hardcoded
- Dates, numbers and currency go through `Intl` / `FormatStyle`, never hand-built strings ([references/formatting.md](references/formatting.md))
- `<html lang>` and `dir` match the locale; hreflang is present and reciprocal on web ([references/seo.md](references/seo.md))
- Language switcher works and persists; missing keys fall back to the source language, never to raw keys

### 7. Report

Tell the user which locales and keys were translated, that they're drafts until a person reviews them, and how to approve them:
`python3 "${CLAUDE_SKILL_DIR}/scripts/translation_state.py" approve "<pattern>" --locale de --all-drafts` (or `--keys …`).
List any checker warnings you left in place and why. If the user doesn't want review tracking, skip steps 5.1, 5.4 and the approve step, and delete `.dragoman/`.

## References

Read only what the task needs:

| File | When |
|---|---|
| [translation-quality.md](references/translation-quality.md) | Before translating: context, placeholders, plurals, tone, style file, locale codes |
| [extraction.md](references/extraction.md) | Moving hardcoded strings into message files; common i18n bugs; emails |
| [nextjs.md](references/nextjs.md) | next-intl setup, routing, localized pathnames, namespaces |
| [seo.md](references/seo.md) | hreflang, canonical URLs, sitemaps, localized OG images |
| [react-i18next.md](references/react-i18next.md) | react-i18next setup, namespaces, lazy loading |
| [react-native.md](references/react-native.md) | React Native / Expo setup, device locale, RTL |
| [apple.md](references/apple.md) | String Catalogs, what Xcode extracts, SwiftUI pitfalls, xcstrings scripts |
| [formatting.md](references/formatting.md) | `Intl` dates/numbers/lists, locale detection, fallbacks |
| [rtl-a11y.md](references/rtl-a11y.md) | RTL layout, logical CSS, `lang` for screen readers |
| [ai-content.md](references/ai-content.md) | Making LLM-generated text follow the app language |
| [lingo.md](references/lingo.md) | Lingo.dev compiler, CLI and GitHub Action (opt-in) |

## Scripts

Python 3 standard library only (YAML files need PyYAML). Run from the project root; they read `.dragoman/style.json` if present.

| Script | Purpose |
|---|---|
| `check_locales.py "<pattern>"` | Validate every locale against the source; exit 1 on errors |
| `translation_state.py todo\|mark\|approve\|status "<pattern>"` | Incremental translation and review tracking in `.dragoman/state.json` |
| `xcstrings_audit.py --locale <code>` | String Catalogs: keys missing from catalogs, untranslated and needs-review entries |
| `xcstrings_add.py <catalog> --locale <code> --translations <file.json>` | String Catalogs: add translations as Needs Review in Xcode's file format |
