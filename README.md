# Dragoman

**Localization for Claude that checks its own work.**

A dragoman was the interpreter and guide at the Ottoman court: the person who made sure what was said in one language arrived intact in another. This plugin does that job for apps. It sets up i18n, moves hardcoded strings into message files, translates them, and then verifies every translation mechanically instead of trusting the model.

```text
check_locales.py "messages/[locale].json"
  error  ru  cart.items: {count, plural} missing 'few' form (ru needs one, few, many, other)
  error  ru  cart.total: placeholder {amount} missing
  error  ru  terms: tags differ: source {'link': 1} vs {}
  warn   ja  cart.greeting: identical to source — untranslated?
```

## Install

Dragoman is a Claude plugin, listed in the Claude directory. It works in chat on claude.ai, the desktop and mobile apps, Cowork, and Claude Code, and a plugin you add to your account follows you to all of them.

**From the directory:** in Claude, open **Directory**, search for **Dragoman**, and add it.

**From this repo (claude.ai, desktop and mobile apps, Cowork):** open **Customize → Plugins**, choose **Add → Add marketplace**, enter `hacksurvivor/dragoman`, select **Sync**, then **Add** next to Dragoman.

**Claude Code:**

```
/plugin marketplace add hacksurvivor/dragoman
/plugin install dragoman@dragoman
```

Or from a terminal: `claude plugin marketplace add hacksurvivor/dragoman`, then `claude plugin install dragoman@dragoman`.

Then ask Claude to localize your app: *"Add German and Japanese"*, *"I changed the English copy, update the translations"*, *"Why is this SwiftUI screen still in English?"*

### Where it works best

- **Claude Code and Cowork** work directly in your project: Dragoman can set up i18n, edit source files, and run its checks on the real files.
- **Chat** works on the locale files you upload or paste. Claude translates them, runs the same checks in its code-execution sandbox, and gives you the finished files to download. Setup steps that need your codebase are described rather than applied.

## How it works

1. **Detects** your stack and any existing i18n library (it keeps what you have).
2. **Settles your style once**: target languages and regional variants, formality (du/Sie, tu/vous …), terms that stay untranslated, required terminology. Saved to `.dragoman/style.json` and reused on every run.
3. **Sets up i18n** if there is none, using the standard library for your stack.
4. **Extracts hardcoded strings** into message files, avoiding concatenation, split sentences and English-only plural logic.
5. **Translates only what's new or changed.** `.dragoman/state.json` records a hash of each source string and whether a person reviewed the translation, so re-runs never touch reviewed text and edited source strings get flagged.
6. **Verifies** with bundled scripts, fixes what they find, and re-runs until clean.
7. **Reports** what's done, what's a draft, and how to approve drafts after human review.

## What's supported

| | Setup and code guidance | Translation + automatic checks |
|---|---|---|
| Next.js (next-intl) | ✓ incl. routing, hreflang, sitemaps, OG images | ✓ ICU messages |
| React: Vite, React Router, CRA (react-i18next) | ✓ | ✓ i18next messages and plural keys |
| React Native / Expo | ✓ | ✓ |
| SwiftUI / UIKit (String Catalogs) | ✓ incl. the pitfalls that leave text in English | ✓ `.xcstrings` |
| Other frameworks with JSON, YAML or ARB files (Vue, Flutter, …) | — | ✓ |
| PO, XLIFF, Android XML, CSV, … | — | via the optional [Lingo.dev](https://lingo.dev) CLI |

The checker understands ICU MessageFormat (next-intl, FormatJS, Flutter ARB) and i18next syntax, and knows the CLDR plural categories for 128 languages.

## The scripts

Python 3.9+ standard library only (YAML needs PyYAML). They're in `skills/dragoman/scripts/` and work on their own, e.g. in CI:

| Script | What it does |
|---|---|
| `check_locales.py "<pattern>"` | Missing/empty keys, placeholders and tags that differ from the source, ICU syntax errors, missing plural forms, orphan keys, untranslated copies, style-file misses. Exit 1 on errors; `--json` for tooling |
| `translation_state.py todo\|mark\|approve\|status` | Incremental translation and review tracking. `status` exits 1 if a reviewed translation was edited without approval |
| `xcstrings_audit.py --locale <code>` | Keys used in Swift code but missing from every catalog, untranslated keys, needs-review entries |
| `xcstrings_add.py <catalog> --locale <code> --translations <file>` | Adds translations as Needs Review, never overwrites reviewed ones, writes Xcode's exact file format |

`<pattern>` names your locale files: `messages/[locale].json`, `public/locales/[locale]/*.json`, `lib/l10n/app_[locale].arb`.

## What it runs and sends

- Runs the Python scripts above: in Claude Code with your permission, in chat inside Claude's code-execution sandbox. They read your locale files and write only `.dragoman/` and the files you're translating.
- Translations are written by Claude in your session. Nothing is sent anywhere else unless you choose the optional Lingo.dev compiler or CLI, which send source strings to Lingo.dev or the model provider you configure.
- May suggest installing i18n libraries (`next-intl`, `react-i18next`, …) for projects that have none.

## Development

```bash
python3 -m unittest discover tests -v        # script tests (also run in CI)
claude plugin validate . --strict            # manifests
claude plugin validate skills --strict       # skill
```

The icon is generated: `node tools/generate-icon.mjs` rewrites `.claude-plugin/icon.svg`.

The `evals/` suite runs real Claude sessions against small fixture projects (translate ICU messages, update without touching reviewed strings, fix a SwiftUI `String` parameter, ask about formality first). It costs money; each run prints a list-price estimate:

```bash
claude plugin eval . --scaffold --trust-plugin --no-publish \
  --allow-tools Write Edit "Bash(python3 *)" --max-cost-usd 10
```

The eval harness refuses to run from a path containing a directory name with leading or trailing spaces.

## Credits

Lingo.dev guidance is based on the [lingo.dev](https://github.com/lingodotdev/lingo.dev) docs and packages (Apache-2.0). Plural data comes from the Unicode CLDR via ICU.

## License

[MIT](LICENSE)
