---
type: llm
focus: { source: file, path: messages/de.json }
---

PASS if this German translation file keeps the same keys as the English source, uses informal "du" forms (not "Sie") as the project's style file requires, keeps "Acme" and "Acme Pro" untranslated, keeps placeholders like {name} and tags like <link>…</link> intact, and reads like natural German UI text.
FAIL if it uses "Sie", translates brand names, drops or renames placeholders, or reads like word-for-word machine output.
