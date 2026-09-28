---
type: regex
target: { source: file, path: messages/de.json }
pattern: '^(?=[\s\S]*\{name\})(?=[\s\S]*<link>[^<]+</link>)(?=[\s\S]*\{inviter\})(?=[\s\S]*\{team\})(?=[\s\S]*Acme Pro)'
---
