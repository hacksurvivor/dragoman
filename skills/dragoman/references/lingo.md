# Lingo.dev: compiler, CLI and CI

Opt-in only. Both the compiler and the CLI send your source strings to a translation model — Lingo.dev's engine (`LINGODOTDEV_API_KEY`) or an LLM provider you configure — so they need an API key and a network connection. Suggest them when the user wants automated translation in their build or CI; otherwise translate with the default workflow in SKILL.md.

Lingo.dev ships three separate tools. Check which one a project already uses (`package.json`, `i18n.json`, `.lingo/config.json`) before suggesting any:

| Tool | Package | What it is |
|---|---|---|
| Compiler | `@lingo.dev/compiler` | Build-time plugin that translates JSX text without keys |
| Classic CLI | `lingo.dev` | Translates locale files in place; `i18n.json` + `i18n.lock` |
| Platform CLI + React library | `@lingo.dev/cli` + `@lingo.dev/react` | Source text with required context in code, synced with the Lingo.dev platform; `.lingo/config.json` |

## Contents
- Compiler: Next.js, Vite, what gets translated, models
- Classic CLI: `i18n.json`, commands, lockfile
- Platform CLI and `@lingo.dev/react`
- GitHub Actions
- Troubleshooting

## Compiler (`@lingo.dev/compiler`)

No translation keys: the compiler finds text in JSX at build time and swaps in translations. Beta package — pin the version.

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

**Critical:** `LingoProvider` goes in the root layout, and the Next.js config must be an async function.

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

### What gets translated

```tsx
// Translated: JSX text, string literals inside JSX, and string values of
// title, aria-label, aria-description, alt, label, description,
// placeholder, content, subtitle
<h1>Welcome to our app</h1>
<button>{"Submit"}</button>
<img alt="Product photo" />

// Skipped: <code>, <pre>, <script>, <style>, <kbd>, <samp>, <var>,
// and anything marked translate="no" or data-lingo-skip
<code>npm install</code>
<span translate="no">Acme</span>

// Not translated: plain JS strings outside JSX
const message = "Hello world";
// Workaround: make it JSX
const message = <>Hello world</>;
```

Pin a translation per locale (brand names, legal copy) with `data-lingo-override={{ de: "…", fr: "…" }}`. Set `useDirective: true` to translate only files that start with `'use i18n'`.

### Models

`models: "lingo.dev"` uses Lingo.dev's engine. For your own provider, map locale pairs to `provider:model` strings; each provider reads its key from an env var:

```typescript
models: {
  "en:de": "anthropic:<model>",   // ANTHROPIC_API_KEY
  "*:*": "openai:<model>",        // OPENAI_API_KEY
}
// Also: google: (GOOGLE_API_KEY), groq: (GROQ_API_KEY), mistral: (MISTRAL_API_KEY),
// openrouter: (OPENROUTER_API_KEY), ollama: (local, no key)
```

Pass the project's tone and glossary through `prompt` (placeholders `{SOURCE_LOCALE}` and `{TARGET_LOCALE}`), built from `.dragoman/style.json`.

## Classic CLI (`lingo.dev`)

Translates locale files in place. Works with more formats than dragoman's checker covers.

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

**Bucket types:** `json`, `yaml`, `yaml-root-key`, `csv`, `po`, `markdown`, `mdx`, `android`, `xcode-xcstrings`, `properties`, `xliff`, `html`, `txt`, `php`, `flutter-arb`, `vue-json`, `typescript`

```bash
npx lingo.dev@0.138.8 init                    # create i18n.json
npx lingo.dev@0.138.8 run                     # translate new and changed strings
npx lingo.dev@0.138.8 run --target-locale es  # Spanish only
npx lingo.dev@0.138.8 run --key auth/login    # keys under a prefix (nesting joined with /)
npx lingo.dev@0.138.8 run --frozen            # CI: fail if translations are out of date
npx lingo.dev@0.138.8 run --force             # retranslate everything (overwrites manual edits)
```

The version above is the one these docs were checked against; pin whatever version the project uses rather than `@latest`.

Commit `i18n.lock`. It stores a checksum of every source string, which is how `run` knows which strings changed. Don't delete it: a fresh lockfile records the current source as already translated, so edits made since the last run are never picked up.

## Platform CLI and `@lingo.dev/react`

A different model from everything above, published on npm only (not in the open-source repository, no license declared). Code uses source text plus a required context instead of keys, and the CLI extracts it and syncs translations with the Lingo.dev platform:

```tsx
const l = useLingo();
l.text("Save", { context: "Form submit button" });
l.plural(count, { one: "# item", other: "# items" }, { context: "Cart count" });
```

```bash
npx @lingo.dev/cli@1.16.0 init        # create .lingo/config.json
npx @lingo.dev/cli@1.16.0 extract     # write locales/<locale>.jsonc and lingo.d.ts from code
npx @lingo.dev/cli@1.16.0 push        # send source strings to the platform for translation
npx @lingo.dev/cli@1.16.0 pull        # fetch translations
npx @lingo.dev/cli@1.16.0 check       # validate; expect 0 issues
npx @lingo.dev/cli@1.16.0 guide setup # its own setup, API and migration guides
```

Its setup guide targets the Next.js Pages Router (`withLingoApp`, `withLingoProps`). Only suggest it when the project already uses it or the user asks for it; migrating an existing next-intl or i18next app means rewriting every call site. Its `.jsonc` files carry `@context` metadata that `check_locales.py` doesn't read — use `lingo check` for them.

## GitHub Actions

Pin actions to a commit SHA, not a branch — a moving `@main` runs whatever code is pushed there with your API key and write access. Update the SHAs deliberately.

```yaml
name: Translate
on:
  push:
    branches: [main]
permissions:
  contents: write
  pull-requests: write
jobs:
  translate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
      - uses: lingodotdev/lingo.dev@3a6845966696d0fd1a97922ed455381426b61ffd # lingo.dev@0.138.8
        with:
          api-key: ${{ secrets.LINGODOTDEV_API_KEY }}
          pull-request: true   # open a PR for review instead of committing to main
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

## Troubleshooting

| Problem | Cause | Fix |
|---|---|---|
| Strings not translated | Plain JS string outside JSX | Move it into JSX, e.g. `<>text</>` |
| Build fails in production | `cache-only` with no cached translations | Generate translations in dev or CI first |
| HMR not working | `LingoProvider` placement | Move it to the root layout / above the router |
| Config type error | Next.js config not async | Export an `async function` returning `withLingo(...)` |
| Stale translations after source edits | — | `run` (not deleting `i18n.lock`); see CLI section |
